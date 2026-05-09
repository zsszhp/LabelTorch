"""Annotation service: save edits, audit log, assisted annotation"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Optional

from labeltorch.app.infra.db.sqlite import Database
from labeltorch.app.infra.storage.yolo_parser import YOLOBBox, YOLOLabelFile
from labeltorch.app.infra.storage.file_repo import atomic_write

logger = logging.getLogger(__name__)


class AnnotationService:
    """Annotation management service"""

    def __init__(self, db: Database):
        self.db = db

    def get_sample_boxes(self, sample_id: str) -> list:
        """Get bounding boxes for a sample from its label file"""
        row = self.db.fetchone(
            "SELECT * FROM dataset_samples WHERE id = ?", (sample_id,)
        )
        if not row or not row["label_path"]:
            return []

        label = YOLOLabelFile.parse(row["label_path"])
        return [
            {
                "class_id": box.class_id,
                "x_center": box.x_center,
                "y_center": box.y_center,
                "width": box.width,
                "height": box.height,
            }
            for box in label.boxes
        ]

    def save_annotation_edit(self, sample_id: str, boxes: list,
                             source: str = "manual") -> dict:
        """Save annotation edits for a sample.

        Args:
            sample_id: Sample ID
            boxes: List of box dicts with class_id, x_center, y_center, width, height
            source: "manual" or "assisted"

        Returns:
            dict with success status
        """
        row = self.db.fetchone(
            "SELECT * FROM dataset_samples WHERE id = ?", (sample_id,)
        )
        if not row:
            return {"success": False, "error": "Sample not found"}

        # Convert to YOLOBBox objects
        yolo_boxes = []
        for b in boxes:
            yolo_boxes.append(YOLOBBox(
                class_id=b["class_id"],
                x_center=b["x_center"],
                y_center=b["y_center"],
                width=b["width"],
                height=b["height"],
            ))

        # Write to label file (atomic)
        if row["label_path"]:
            YOLOLabelFile.write(row["label_path"], yolo_boxes)

        # Record audit log
        change_id = str(uuid.uuid4())
        boxes_json = json.dumps(boxes, ensure_ascii=False)
        self.db.execute(
            "INSERT INTO annotation_changes (id, sample_id, action, boxes_json, source, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (change_id, sample_id, "edit", boxes_json, source, datetime.now().isoformat()),
        )

        logger.info("Annotation saved for sample %s (%d boxes)", sample_id, len(boxes))
        return {"success": True, "box_count": len(boxes)}

    def bulk_confirm(self, sample_ids: list) -> dict:
        """Bulk confirm assisted annotations.

        For each sample, mark all assisted boxes as confirmed
        by recording an audit entry.

        Returns:
            dict with confirmed_count and errors
        """
        confirmed_count = 0
        errors = []

        for sample_id in sample_ids:
            try:
                # Get boxes
                boxes = self.get_sample_boxes(sample_id)
                if not boxes:
                    continue

                # Record confirmation
                change_id = str(uuid.uuid4())
                boxes_json = json.dumps(boxes, ensure_ascii=False)
                self.db.execute(
                    "INSERT INTO annotation_changes (id, sample_id, action, boxes_json, source, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (change_id, sample_id, "confirm", boxes_json, "assisted",
                     datetime.now().isoformat()),
                )
                confirmed_count += 1
            except Exception as e:
                errors.append(f"{sample_id}: {e}")

        logger.info("Bulk confirm: %d samples confirmed", confirmed_count)
        return {"confirmed_count": confirmed_count, "errors": errors}

    def get_annotation_history(self, sample_id: str) -> list:
        """Get annotation change history for a sample"""
        rows = self.db.fetchall(
            "SELECT * FROM annotation_changes WHERE sample_id = ? ORDER BY created_at DESC",
            (sample_id,),
        )
        return [dict(row) for row in rows]
