"""Dataset service: import, validate, split, class remapping"""

import os
import uuid
import json
import logging
import random
from datetime import datetime
from typing import Optional

from labeltorch.app.infra.db.sqlite import Database
from labeltorch.app.infra.storage.file_repo import (
    scan_image_dir, find_paired_label, get_image_size, ensure_dir, atomic_write,
)
from labeltorch.app.infra.storage.yolo_parser import (
    YOLOLabelFile, YOLOBBox, extract_classes_from_labels, remap_label_file,
)

logger = logging.getLogger(__name__)


class DatasetService:
    """Dataset management service"""

    def __init__(self, db: Database):
        self.db = db

    def import_dataset(self, project_id: str, name: str, image_dir: str,
                       label_dir: str, fmt: str = "yolo_txt") -> dict:
        """Import a YOLO txt dataset.

        Scans image directory, pairs with labels, validates,
        and stores metadata in database.

        Returns:
            dict with dataset_id, total_samples, valid_samples, invalid_samples, errors
        """
        dataset_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        # Scan images
        image_paths = scan_image_dir(image_dir)
        if not image_paths:
            return {
                "dataset_id": None,
                "total_samples": 0,
                "valid_samples": 0,
                "invalid_samples": 0,
                "errors": ["No images found in directory"],
            }

        # Insert dataset record
        self.db.execute(
            "INSERT INTO datasets (id, project_id, name, image_dir, label_dir, format, sample_count, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
            (dataset_id, project_id, name, image_dir, label_dir, fmt, created_at),
        )

        # Process each image
        valid_count = 0
        invalid_count = 0
        errors = []
        class_ids_seen = set()

        for img_path in image_paths:
            sample_id = str(uuid.uuid4())
            label_path = find_paired_label(img_path, label_dir)
            width, height = None, None

            status = "valid"

            # Check label exists
            if label_path is None:
                status = "missing_label"
                invalid_count += 1
                errors.append(f"Missing label for {os.path.basename(img_path)}")
            else:
                # Parse and validate label
                label = YOLOLabelFile.parse(label_path)
                if label.errors:
                    status = "invalid_coord"
                    invalid_count += 1
                    for err in label.errors:
                        errors.append(f"{os.path.basename(label_path)}: {err}")
                else:
                    valid_count += 1
                    for box in label.boxes:
                        class_ids_seen.add(box.class_id)

            # Get image dimensions
            size = get_image_size(img_path)
            if size:
                width, height = size

            # Insert sample record
            self.db.execute(
                "INSERT INTO dataset_samples (id, dataset_id, image_path, label_path, width, height, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sample_id, dataset_id, img_path, label_path, width, height, status),
            )

        # Update sample count
        self.db.execute(
            "UPDATE datasets SET sample_count = ? WHERE id = ?",
            (valid_count + invalid_count, dataset_id),
        )

        # Insert class mappings
        for class_id in sorted(class_ids_seen):
            mapping_id = str(uuid.uuid4())
            self.db.execute(
                "INSERT INTO class_mappings (id, dataset_id, original_id, mapped_id, class_name) "
                "VALUES (?, ?, ?, ?, ?)",
                (mapping_id, dataset_id, class_id, class_id, f"class_{class_id}"),
            )

        logger.info(
            "Dataset imported: %s (%d valid, %d invalid)",
            name, valid_count, invalid_count,
        )

        return {
            "dataset_id": dataset_id,
            "total_samples": valid_count + invalid_count,
            "valid_samples": valid_count,
            "invalid_samples": invalid_count,
            "errors": errors[:50],  # Limit error list
        }

    def validate_dataset(self, dataset_id: str) -> dict:
        """Validate dataset and return report"""
        rows = self.db.fetchall(
            "SELECT * FROM dataset_samples WHERE dataset_id = ?",
            (dataset_id,),
        )
        total = len(rows)
        valid = sum(1 for r in rows if r["status"] == "valid")
        missing = sum(1 for r in rows if r["status"] == "missing_label")
        invalid = sum(1 for r in rows if r["status"] == "invalid_coord")
        return {
            "dataset_id": dataset_id,
            "total": total,
            "valid": valid,
            "missing_labels": missing,
            "invalid_coords": invalid,
        }

    def list_datasets(self, project_id: str) -> list:
        """List datasets for a project"""
        rows = self.db.fetchall(
            "SELECT * FROM datasets WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        )
        return [dict(r) for r in rows]

    def get_dataset(self, dataset_id: str) -> Optional[dict]:
        """Get dataset by ID"""
        row = self.db.fetchone("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        return dict(row) if row else None

    def get_classes(self, dataset_id: str) -> list:
        """Get class mappings for a dataset"""
        rows = self.db.fetchall(
            "SELECT * FROM class_mappings WHERE dataset_id = ? ORDER BY mapped_id",
            (dataset_id,),
        )
        return [dict(r) for r in rows]

    def remap_classes(self, dataset_id: str, mapping: dict) -> dict:
        """Remap class IDs and rewrite label files.

        Args:
            dataset_id: Dataset ID
            mapping: dict mapping old_class_id -> new_class_id (both int)

        Returns:
            dict with remapped_count and errors
        """
        # Get all valid samples with labels
        rows = self.db.fetchall(
            "SELECT * FROM dataset_samples WHERE dataset_id = ? AND status = 'valid'",
            (dataset_id,),
        )

        total_remapped = 0
        errors = []

        for row in rows:
            label_path = row["label_path"]
            if not label_path or not os.path.exists(label_path):
                continue
            try:
                count = remap_label_file(label_path, mapping)
                total_remapped += count
            except Exception as e:
                errors.append(f"{label_path}: {e}")

        # Update class_mappings table
        for old_id, new_id in mapping.items():
            self.db.execute(
                "UPDATE class_mappings SET mapped_id = ? WHERE dataset_id = ? AND original_id = ?",
                (new_id, dataset_id, old_id),
            )

        logger.info("Class remapping done: %d boxes remapped", total_remapped)
        return {
            "dataset_id": dataset_id,
            "remapped_count": total_remapped,
            "errors": errors,
        }

    def split_dataset(self, dataset_id: str, train_ratio: float = 0.8,
                      val_ratio: float = 0.2, seed: int = 42) -> dict:
        """Split dataset into train/val and generate data.yaml

        Args:
            dataset_id: Dataset ID
            train_ratio: Training set ratio (0-1)
            val_ratio: Validation set ratio (0-1)
            seed: Random seed for reproducibility

        Returns:
            dict with train_count, val_count, yaml_path
        """
        dataset = self.get_dataset(dataset_id)
        if not dataset:
            return {"train_count": 0, "val_count": 0, "yaml_path": None}

        # Get valid samples
        rows = self.db.fetchall(
            "SELECT * FROM dataset_samples WHERE dataset_id = ? AND status = 'valid'",
            (dataset_id,),
        )

        sample_paths = [dict(r) for r in rows]
        random.seed(seed)
        random.shuffle(sample_paths)

        split_idx = int(len(sample_paths) * train_ratio)
        train_samples = sample_paths[:split_idx]
        val_samples = sample_paths[split_idx:]

        # Write split files
        # Get project root path for splits directory
        project_row = self.db.fetchone("SELECT root_path FROM projects WHERE id = ?", (dataset["project_id"],))
        project_root = project_row["root_path"] if project_row else os.path.dirname(dataset["image_dir"])
        splits_dir = ensure_dir(os.path.join(project_root, "datasets", dataset_id, "splits"))

        train_txt = os.path.join(splits_dir, "train.txt")
        val_txt = os.path.join(splits_dir, "val.txt")

        with open(train_txt, "w", encoding="utf-8") as f:
            for s in train_samples:
                f.write(s["image_path"] + "\n")

        with open(val_txt, "w", encoding="utf-8") as f:
            for s in val_samples:
                f.write(s["image_path"] + "\n")

        # Generate data.yaml for Ultralytics
        classes = self.get_classes(dataset_id)
        class_names = {}
        for c in sorted(classes, key=lambda x: x["mapped_id"]):
            class_names[c["mapped_id"]] = c["class_name"]

        yaml_content = self._generate_data_yaml(
            train_txt, val_txt, class_names, dataset["image_dir"],
        )
        yaml_path = os.path.join(splits_dir, "data.yaml")
        atomic_write(yaml_path, yaml_content)

        logger.info("Dataset split: %d train, %d val", len(train_samples), len(val_samples))
        return {
            "dataset_id": dataset_id,
            "train_count": len(train_samples),
            "val_count": len(val_samples),
            "yaml_path": yaml_path,
        }

    def _generate_data_yaml(self, train_path: str, val_path: str,
                            class_names: dict, image_dir: str) -> str:
        """Generate Ultralytics-compatible data.yaml"""
        lines = [
            f"path: {image_dir}",
            f"train: {train_path}",
            f"val: {val_path}",
            "",
            f"nc: {len(class_names)}",
            f"names: {class_names}",
        ]
        return "\n".join(lines) + "\n"

    def get_samples(self, dataset_id: str, status: str = None,
                    limit: int = 100, offset: int = 0) -> list:
        """Get samples for a dataset with optional filtering and pagination"""
        if status:
            rows = self.db.fetchall(
                "SELECT * FROM dataset_samples WHERE dataset_id = ? AND status = ? "
                "ORDER BY image_path LIMIT ? OFFSET ?",
                (dataset_id, status, limit, offset),
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM dataset_samples WHERE dataset_id = ? "
                "ORDER BY image_path LIMIT ? OFFSET ?",
                (dataset_id, limit, offset),
            )
        return [dict(r) for r in rows]
