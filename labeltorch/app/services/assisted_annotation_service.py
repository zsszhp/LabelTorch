"""Assisted annotation: model inference, candidate box generation, batch confirm"""

import os
import logging
from typing import Optional

from labeltorch.app.infra.db.sqlite import Database
from labeltorch.app.services.annotation_service import AnnotationService
from labeltorch.app.ui.widgets.image_canvas import BBox

logger = logging.getLogger(__name__)


class AssistedAnnotationService:
    """Assisted annotation using trained models"""

    def __init__(self, db: Database):
        self.db = db
        self._annotation_service = AnnotationService(db)

    def run_inference(self, model_path: str, image_paths: list,
                      conf_threshold: float = 0.25,
                      device: str = "cpu") -> dict:
        """Run inference on images using a trained model.

        Args:
            model_path: Path to best.pt weights
            image_paths: List of image file paths
            conf_threshold: Minimum confidence threshold
            device: "cpu" or "cuda" device string

        Returns:
            dict with results (mapping image_path -> list of candidate boxes)
        """
        if not os.path.exists(model_path):
            return {"error": f"Model not found: {model_path}", "results": {}}

        try:
            from ultralytics import YOLO
            model = YOLO(model_path)
        except Exception as e:
            return {"error": f"Failed to load model: {e}", "results": {}}

        results = {}
        total_boxes = 0

        for img_path in image_paths:
            if not os.path.exists(img_path):
                continue
            try:
                preds = model.predict(
                    source=img_path,
                    conf=conf_threshold,
                    device=device,
                    verbose=False,
                )
                boxes = []
                if preds and len(preds) > 0:
                    pred = preds[0]
                    if pred.boxes is not None:
                        img_w = pred.orig_shape[1]
                        img_h = pred.orig_shape[0]
                        for box in pred.boxes:
                            xyxy = box.xyxy[0].cpu().numpy()
                            x1, y1, x2, y2 = xyxy
                            # Convert to YOLO normalized format
                            x_center = ((x1 + x2) / 2) / img_w
                            y_center = ((y1 + y2) / 2) / img_h
                            width = (x2 - x1) / img_w
                            height = (y2 - y1) / img_h
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            boxes.append({
                                "class_id": class_id,
                                "x_center": float(x_center),
                                "y_center": float(y_center),
                                "width": float(width),
                                "height": float(height),
                                "confidence": confidence,
                            })
                            total_boxes += 1
                results[img_path] = boxes
            except Exception as e:
                logger.warning("Inference failed for %s: %s", img_path, e)
                results[img_path] = []

        logger.info("Inference complete: %d images, %d boxes (threshold=%.2f)",
                     len(results), total_boxes, conf_threshold)
        return {"error": None, "results": results}

    def run_assisted_annotation(self, dataset_id: str, model_path: str,
                                conf_threshold: float = 0.25,
                                device: str = "cpu") -> dict:
        """Run assisted annotation on a dataset.

        Args:
            dataset_id: Target dataset ID
            model_path: Path to model weights
            conf_threshold: Minimum confidence threshold
            device: Device string

        Returns:
            dict with sample_id -> candidate boxes mapping
        """
        from labeltorch.app.services.dataset_service import DatasetService
        ds = DatasetService(self.db)

        samples = ds.get_samples(dataset_id, status="valid")
        if not samples:
            return {"error": "No valid samples", "candidates": {}}

        image_paths = [s["image_path"] for s in samples]
        infer_result = self.run_inference(model_path, image_paths, conf_threshold, device)

        if infer_result["error"]:
            return {"error": infer_result["error"], "candidates": {}}

        # Map image_path -> sample_id
        path_to_sample = {s["image_path"]: s["id"] for s in samples}
        candidates = {}
        total_candidates = 0

        for img_path, boxes in infer_result["results"].items():
            sample_id = path_to_sample.get(img_path)
            if sample_id and boxes:
                candidates[sample_id] = boxes
                total_candidates += len(boxes)

        logger.info("Assisted annotation: %d samples with %d candidates",
                     len(candidates), total_candidates)
        return {"error": None, "candidates": candidates}

    def bulk_confirm(self, candidates: dict) -> dict:
        """Confirm assisted annotation candidates, writing to label files.

        Args:
            candidates: dict mapping sample_id -> list of box dicts

        Returns:
            dict with confirmed_count and errors
        """
        return self._annotation_service.bulk_confirm(
            list(candidates.keys()), candidates
        )

    def filter_by_confidence(self, candidates: dict,
                             threshold: float) -> dict:
        """Filter candidate boxes by confidence threshold.

        Args:
            candidates: dict mapping sample_id -> list of box dicts
            threshold: Minimum confidence to keep

        Returns:
            Filtered candidates dict
        """
        filtered = {}
        for sample_id, boxes in candidates.items():
            kept = [b for b in boxes if b.get("confidence", 0) >= threshold]
            if kept:
                filtered[sample_id] = kept
        return filtered
