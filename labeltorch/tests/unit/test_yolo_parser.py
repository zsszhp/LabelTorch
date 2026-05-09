"""Unit tests for YOLO txt parser, validator, and class remapping"""

import os
import tempfile
import pytest

from labeltorch.app.infra.storage.yolo_parser import (
    YOLOBBox, YOLOLabelFile, extract_classes_from_labels, remap_label_file,
)


class TestYOLOBBox:
    """Test YOLOBBox parsing and validation"""

    def test_from_yolo_line_valid(self):
        box = YOLOBBox.from_yolo_line("0 0.5 0.5 0.3 0.4")
        assert box is not None
        assert box.class_id == 0
        assert box.x_center == 0.5

    def test_from_yolo_line_invalid_parts(self):
        assert YOLOBBox.from_yolo_line("0 0.5 0.5") is None
        assert YOLOBBox.from_yolo_line("a b c d e") is None
        assert YOLOBBox.from_yolo_line("") is None

    def test_is_valid_normal(self):
        box = YOLOBBox(0, 0.5, 0.5, 0.3, 0.4)
        assert box.is_valid()

    def test_is_valid_boundary(self):
        assert YOLOBBox(0, 0.0, 0.0, 0.01, 0.01).is_valid()
        assert YOLOBBox(0, 1.0, 1.0, 0.5, 0.5).is_valid()

    def test_is_invalid_out_of_range(self):
        assert not YOLOBBox(0, -0.1, 0.5, 0.3, 0.4).is_valid()
        assert not YOLOBBox(0, 0.5, 1.5, 0.3, 0.4).is_valid()
        assert not YOLOBBox(0, 0.5, 0.5, 0.0, 0.4).is_valid()
        assert not YOLOBBox(0, 0.5, 0.5, 0.3, 1.5).is_valid()

    def test_to_yolo_line_roundtrip(self):
        original = YOLOBBox(3, 0.123456, 0.789012, 0.345678, 0.901234)
        line = original.to_yolo_line()
        parsed = YOLOBBox.from_yolo_line(line)
        assert parsed is not None
        assert parsed.class_id == original.class_id
        assert abs(parsed.x_center - original.x_center) < 1e-5


class TestYOLOLabelFile:
    """Test YOLO label file parsing and writing"""

    def test_parse_valid_file(self, tmp_path):
        label_path = str(tmp_path / "test.txt")
        with open(label_path, "w") as f:
            f.write("0 0.5 0.5 0.3 0.4\n1 0.2 0.3 0.1 0.2\n")
        result = YOLOLabelFile.parse(label_path)
        assert len(result.boxes) == 2
        assert len(result.errors) == 0

    def test_parse_empty_file(self, tmp_path):
        label_path = str(tmp_path / "empty.txt")
        with open(label_path, "w") as f:
            f.write("")
        result = YOLOLabelFile.parse(label_path)
        assert len(result.boxes) == 0
        assert len(result.errors) == 0

    def test_parse_missing_file(self, tmp_path):
        result = YOLOLabelFile.parse(str(tmp_path / "nonexistent.txt"))
        assert len(result.boxes) == 0
        assert "File not found" in result.errors

    def test_parse_with_invalid_lines(self, tmp_path):
        label_path = str(tmp_path / "mixed.txt")
        with open(label_path, "w") as f:
            f.write("0 0.5 0.5 0.3 0.4\nbad line\n1 0.2 0.3 0.1 0.2\n")
        result = YOLOLabelFile.parse(label_path)
        assert len(result.boxes) == 2
        assert len(result.errors) == 1

    def test_write_and_read_roundtrip(self, tmp_path):
        label_path = str(tmp_path / "roundtrip.txt")
        boxes = [
            YOLOBBox(0, 0.5, 0.5, 0.3, 0.4),
            YOLOBBox(1, 0.2, 0.8, 0.1, 0.15),
        ]
        YOLOLabelFile.write(label_path, boxes)
        result = YOLOLabelFile.parse(label_path)
        assert len(result.boxes) == 2
        assert result.boxes[0].class_id == 0
        assert result.boxes[1].class_id == 1

    def test_write_empty_boxes(self, tmp_path):
        label_path = str(tmp_path / "empty_write.txt")
        YOLOLabelFile.write(label_path, [])
        result = YOLOLabelFile.parse(label_path)
        assert len(result.boxes) == 0


class TestExtractClasses:
    """Test class extraction from label files"""

    def test_extract_classes(self, tmp_path):
        f1 = str(tmp_path / "a.txt")
        f2 = str(tmp_path / "b.txt")
        with open(f1, "w") as f:
            f.write("0 0.5 0.5 0.3 0.4\n1 0.2 0.3 0.1 0.2\n")
        with open(f2, "w") as f:
            f.write("0 0.1 0.1 0.2 0.2\n2 0.5 0.5 0.1 0.1\n")

        counts = extract_classes_from_labels([f1, f2])
        assert counts[0] == 2
        assert counts[1] == 1
        assert counts[2] == 1


class TestRemapLabelFile:
    """Test class ID remapping"""

    def test_remap_basic(self, tmp_path):
        label_path = str(tmp_path / "remap.txt")
        with open(label_path, "w") as f:
            f.write("0 0.5 0.5 0.3 0.4\n1 0.2 0.3 0.1 0.2\n0 0.7 0.7 0.1 0.1\n")

        mapping = {0: 2, 1: 3}
        count = remap_label_file(label_path, mapping)
        assert count == 3

        result = YOLOLabelFile.parse(label_path)
        assert result.boxes[0].class_id == 2
        assert result.boxes[1].class_id == 3
        assert result.boxes[2].class_id == 2

    def test_remap_dry_run(self, tmp_path):
        label_path = str(tmp_path / "dryrun.txt")
        with open(label_path, "w") as f:
            f.write("0 0.5 0.5 0.3 0.4\n")

        count = remap_label_file(label_path, {0: 5}, dry_run=True)
        assert count == 1
        # File should not be modified
        result = YOLOLabelFile.parse(label_path)
        assert result.boxes[0].class_id == 0

    def test_remap_partial_mapping(self, tmp_path):
        label_path = str(tmp_path / "partial.txt")
        with open(label_path, "w") as f:
            f.write("0 0.5 0.5 0.3 0.4\n1 0.2 0.3 0.1 0.2\n2 0.7 0.7 0.1 0.1\n")

        # Only remap class 1 -> 5, leave others unchanged
        count = remap_label_file(label_path, {1: 5})
        assert count == 1

        result = YOLOLabelFile.parse(label_path)
        assert result.boxes[0].class_id == 0  # unchanged
        assert result.boxes[1].class_id == 5  # remapped
        assert result.boxes[2].class_id == 2  # unchanged
