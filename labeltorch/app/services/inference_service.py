"""Inference service: load model and run prediction for assisted annotation"""

import os
import logging
from typing import Optional

from labeltorch.app.infra.db.sqlite import Database

logger = logging.getLogger(__name__)


class InferenceService:
    """Model inference for assisted annotation"""

    def __init__(self, db: Database):
        self.db = db
        self._model = None
        self._model_path = None

    def load_model(self, model_path: str) -> bool:
        """Load a YOLO model from path"""
        if not os.path.exists(model_path):
            logger.error("Model file not found: %s", model_path)
            return False
        try:
            from ultralytics import YOLO
            self._model = YOLO(model_path)
            self._model_path = model_path
            logger.info("Model loaded: %s", model_path)
            return True
        except Exception as e:
            logger.error("Failed to load model: %s - %s", model_path, e)
            self._model = None
            return False

    def predict(self, image_path: str, conf_threshold: float = 0.25,
                iou_threshold: float = 0.45) -> list:
        """Run inference on an image, return list of box dicts.

        Returns:
            List of dicts with keys: class_id, x_center, y_center, width, height, confidence
        """
        if self._model is None:
            logger.warning("No model loaded for inference")
            return []

        try:
            results = self._model.predict(
                source=image_path,
                conf=conf_threshold,
                iou=iou_threshold,
                verbose=False,
            )

            boxes = []
            if results and len(results) > 0:
                result = results[0]
                if result.boxes is not None:
                    img_w = result.orig_shape[1]
                    img_h = result.orig_shape[0]

                    for i in range(len(result.boxes)):
                        xyxy = result.boxes.xyxy[i].cpu().numpy()
                        cls_id = int(result.boxes.cls[i].cpu().numpy())
                        conf = float(result.boxes.conf[i].cpu().numpy())

                        x1, y1, x2, y2 = xyxy
                        boxes.append({
                            "class_id": cls_id,
                            "x_center": ((x1 + x2) / 2) / img_w,
                            "y_center": ((y1 + y2) / 2) / img_h,
                            "width": (x2 - x1) / img_w,
                            "height": (y2 - y1) / img_h,
                            "confidence": conf,
                        })

            logger.info("Inference: %s -> %d boxes (conf>=%.2f)",
                       os.path.basename(image_path), len(boxes), conf_threshold)
            return boxes

        except Exception as e:
            logger.error("Inference failed: %s - %s", image_path, e)
            return []

    def predict_batch(self, image_paths: list, conf_threshold: float = 0.25,
                      iou_threshold: float = 0.45) -> dict:
        """Run inference on multiple images.

        Returns:
            dict mapping image_path -> list of box dicts
        """
        results_map = {}
        for path in image_paths:
            results_map[path] = self.predict(path, conf_threshold, iou_threshold)
        return results_map

    def is_loaded(self) -> bool:
        return self._model is not None

    def get_model_path(self) -> Optional[str]:
        return self._model_path

    def unload_model(self):
        """Release model from memory"""
        self._model = None
        self._model_path = None
        logger.info("Model unloaded")
