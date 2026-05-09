"""YOLO txt format parser and validator

YOLO label format per line:
    class_id x_center y_center width height
All coordinates are normalized [0, 1] relative to image dimensions.
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class YOLOBBox:
    """A single YOLO bounding box annotation"""
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float

    def is_valid(self) -> bool:
        """Check if coordinates are within valid range [0, 1]"""
        return (
            0.0 <= self.x_center <= 1.0
            and 0.0 <= self.y_center <= 1.0
            and 0.0 < self.width <= 1.0
            and 0.0 < self.height <= 1.0
        )

    def to_yolo_line(self) -> str:
        """Convert back to YOLO txt line format"""
        return f"{self.class_id} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"

    @staticmethod
    def from_yolo_line(line: str) -> Optional["YOLOBBox"]:
        """Parse a single YOLO label line"""
        parts = line.strip().split()
        if len(parts) != 5:
            return None
        try:
            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])
            return YOLOBBox(
                class_id=class_id,
                x_center=x_center,
                y_center=y_center,
                width=width,
                height=height,
            )
        except (ValueError, IndexError):
            return None


@dataclass
class YOLOLabelFile:
    """Parsed YOLO label file"""
    path: str
    boxes: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @staticmethod
    def parse(label_path: str) -> "YOLOLabelFile":
        """Parse a YOLO txt label file"""
        result = YOLOLabelFile(path=label_path)

        if not os.path.exists(label_path):
            result.errors.append("File not found")
            return result

        try:
            with open(label_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    box = YOLOBBox.from_yolo_line(line)
                    if box is None:
                        result.errors.append(f"Line {line_num}: parse failed '{line}'")
                        continue

                    if not box.is_valid():
                        result.errors.append(
                            f"Line {line_num}: invalid coords "
                            f"cls={box.class_id} ({box.x_center}, {box.y_center}, "
                            f"{box.width}, {box.height})"
                        )
                        continue

                    result.boxes.append(box)
        except Exception as e:
            result.errors.append(f"Read error: {e}")

        return result

    @staticmethod
    def write(label_path: str, boxes: list):
        """Write boxes to YOLO label file (atomic write)"""
        from labeltorch.app.infra.storage.file_repo import atomic_write
        lines = [box.to_yolo_line() for box in boxes]
        content = "\n".join(lines) + "\n" if lines else ""
        atomic_write(label_path, content)


def extract_classes_from_labels(label_paths: list) -> dict:
    """Extract all class IDs and their occurrence count from label files.

    Returns:
        dict mapping class_id -> count
    """
    class_counts = {}
    for path in label_paths:
        label = YOLOLabelFile.parse(path)
        for box in label.boxes:
            class_counts[box.class_id] = class_counts.get(box.class_id, 0) + 1
    return class_counts


def remap_label_file(label_path: str, mapping: dict, dry_run: bool = False) -> int:
    """Remap class IDs in a label file according to mapping dict.

    Args:
        label_path: Path to YOLO txt label file
        mapping: dict mapping old_class_id -> new_class_id
        dry_run: If True, only count changes without writing

    Returns:
        Number of boxes remapped
    """
    label = YOLOLabelFile.parse(label_path)
    remapped_count = 0
    new_boxes = []

    for box in label.boxes:
        if box.class_id in mapping:
            new_box = YOLOBBox(
                class_id=mapping[box.class_id],
                x_center=box.x_center,
                y_center=box.y_center,
                width=box.width,
                height=box.height,
            )
            new_boxes.append(new_box)
            remapped_count += 1
        else:
            new_boxes.append(box)

    if not dry_run and remapped_count > 0:
        YOLOLabelFile.write(label_path, new_boxes)

    return remapped_count
