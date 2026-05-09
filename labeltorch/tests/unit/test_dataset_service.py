"""Unit tests for DatasetService and AnnotationService"""

import os
import pytest

from labeltorch.app.infra.db.sqlite import init_database
from labeltorch.app.services.dataset_service import DatasetService
from labeltorch.app.services.annotation_service import AnnotationService
from labeltorch.app.services.project_service import ProjectService


@pytest.fixture
def services(tmp_path):
    """Create DatasetService, AnnotationService and ProjectService with test database"""
    db = init_database(":memory:")
    ps = ProjectService(db)
    ds = DatasetService(db)
    ans = AnnotationService(db)
    yield ps, ds, ans
    db.close()


def _create_yolo_dataset(tmp_path, num_images=3, num_classes=2):
    """Helper: create a minimal YOLO dataset on disk"""
    img_dir = str(tmp_path / "images")
    lbl_dir = str(tmp_path / "labels")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)

    from PIL import Image
    for i in range(num_images):
        # Create small test image
        img = Image.new("RGB", (100, 100), color=(i * 50, i * 50, i * 50))
        img.save(os.path.join(img_dir, f"{i:04d}.png"))

        # Create label with boxes
        with open(os.path.join(lbl_dir, f"{i:04d}.txt"), "w") as f:
            f.write(f"{i % num_classes} 0.5 0.5 0.3 0.3\n")

    return img_dir, lbl_dir


def _import_dataset_helper(services, tmp_path, name="ds1", num_images=3, num_classes=2):
    """Helper: create a project and import a YOLO dataset, return (project, import_result)"""
    ps, ds, ans = services
    project = ps.create_project("test", str(tmp_path / "proj"))
    img_dir, lbl_dir = _create_yolo_dataset(tmp_path, num_images=num_images, num_classes=num_classes)
    result = ds.import_dataset(project["id"], name, img_dir, lbl_dir)
    return project, result


# ---------------------------------------------------------------------------
# DatasetService tests
# ---------------------------------------------------------------------------


class TestDatasetImport:
    """Test dataset import"""

    def test_import_basic(self, services, tmp_path):
        ps, ds, ans = services
        project = ps.create_project("test", str(tmp_path / "proj"))
        img_dir, lbl_dir = _create_yolo_dataset(tmp_path)

        result = ds.import_dataset(project["id"], "ds1", img_dir, lbl_dir)
        assert result["dataset_id"] is not None
        assert result["valid_samples"] == 3
        assert result["invalid_samples"] == 0

    def test_import_missing_labels(self, services, tmp_path):
        ps, ds, ans = services
        project = ps.create_project("test", str(tmp_path / "proj"))
        img_dir, lbl_dir = _create_yolo_dataset(tmp_path, num_images=3)

        # Delete one label file
        os.remove(os.path.join(lbl_dir, "0001.txt"))

        result = ds.import_dataset(project["id"], "ds2", img_dir, lbl_dir)
        assert result["valid_samples"] == 2
        assert result["invalid_samples"] == 1

    def test_import_no_images(self, services, tmp_path):
        ps, ds, ans = services
        project = ps.create_project("test", str(tmp_path / "proj"))
        empty_dir = str(tmp_path / "empty")
        os.makedirs(empty_dir)

        result = ds.import_dataset(project["id"], "ds3", empty_dir, empty_dir)
        assert result["total_samples"] == 0
        assert result["dataset_id"] is None


class TestDatasetListAndGet:
    """Test listing and getting datasets"""

    def test_list_datasets(self, services, tmp_path):
        ps, ds, ans = services
        project = ps.create_project("test", str(tmp_path / "proj"))
        img_dir, lbl_dir = _create_yolo_dataset(tmp_path)

        ds.import_dataset(project["id"], "ds1", img_dir, lbl_dir)
        ds.import_dataset(project["id"], "ds2", img_dir, lbl_dir)

        datasets = ds.list_datasets(project["id"])
        assert len(datasets) == 2

    def test_get_dataset(self, services, tmp_path):
        ps, ds, ans = services
        project = ps.create_project("test", str(tmp_path / "proj"))
        img_dir, lbl_dir = _create_yolo_dataset(tmp_path)

        result = ds.import_dataset(project["id"], "ds1", img_dir, lbl_dir)
        dataset = ds.get_dataset(result["dataset_id"])
        assert dataset is not None
        assert dataset["name"] == "ds1"

    def test_get_samples(self, services, tmp_path):
        ps, ds, ans = services
        project = ps.create_project("test", str(tmp_path / "proj"))
        img_dir, lbl_dir = _create_yolo_dataset(tmp_path)

        result = ds.import_dataset(project["id"], "ds1", img_dir, lbl_dir)
        samples = ds.get_samples(result["dataset_id"])
        assert len(samples) == 3


class TestClassRemap:
    """Test class ID remapping"""

    def test_remap_classes(self, services, tmp_path):
        ps, ds, ans = services
        project = ps.create_project("test", str(tmp_path / "proj"))
        img_dir, lbl_dir = _create_yolo_dataset(tmp_path, num_classes=3)

        result = ds.import_dataset(project["id"], "ds1", img_dir, lbl_dir)
        dataset_id = result["dataset_id"]

        # Remap class 0 -> 10, 1 -> 11
        mapping = {0: 10, 1: 11}
        remap_result = ds.remap_classes(dataset_id, mapping)
        assert remap_result["remapped_count"] > 0

        # Verify labels updated
        samples = ds.get_samples(dataset_id, status="valid")
        from labeltorch.app.infra.storage.yolo_parser import YOLOLabelFile
        for sample in samples:
            if sample["label_path"]:
                label = YOLOLabelFile.parse(sample["label_path"])
                for box in label.boxes:
                    assert box.class_id in (10, 11, 2)

    def test_get_classes(self, services, tmp_path):
        ps, ds, ans = services
        project, result = _import_dataset_helper(services, tmp_path, num_classes=3)
        dataset_id = result["dataset_id"]

        classes = ds.get_classes(dataset_id)
        assert len(classes) == 3
        # Classes should have original_id, mapped_id, class_name
        original_ids = {c["original_id"] for c in classes}
        assert original_ids == {0, 1, 2}

    def test_validate_dataset(self, services, tmp_path):
        ps, ds, ans = services
        project, result = _import_dataset_helper(services, tmp_path)
        dataset_id = result["dataset_id"]

        report = ds.validate_dataset(dataset_id)
        assert report["total"] == 3
        assert report["valid"] == 3
        assert report["missing_labels"] == 0
        assert report["invalid_coords"] == 0


class TestDatasetSplit:
    """Test dataset splitting"""

    def test_split_dataset(self, services, tmp_path):
        ps, ds, ans = services
        project = ps.create_project("test", str(tmp_path / "proj"))
        img_dir, lbl_dir = _create_yolo_dataset(tmp_path, num_images=10)

        result = ds.import_dataset(project["id"], "ds1", img_dir, lbl_dir)
        split_result = ds.split_dataset(result["dataset_id"], train_ratio=0.8)
        assert split_result["train_count"] == 8
        assert split_result["val_count"] == 2
        assert split_result["yaml_path"] is not None
        assert os.path.exists(split_result["yaml_path"])


# ---------------------------------------------------------------------------
# AnnotationService tests
# ---------------------------------------------------------------------------


class TestAnnotationService:
    """Test AnnotationService: save edits, get boxes, history, bulk confirm"""

    def _get_valid_sample_id(self, ds, dataset_id):
        """Helper: get the first valid sample ID from a dataset"""
        samples = ds.get_samples(dataset_id, status="valid")
        assert len(samples) > 0, "No valid samples found"
        return samples[0]["id"]

    def test_get_sample_boxes(self, services, tmp_path):
        ps, ds, ans = services
        project, result = _import_dataset_helper(services, tmp_path)
        dataset_id = result["dataset_id"]
        sample_id = self._get_valid_sample_id(ds, dataset_id)

        boxes = ans.get_sample_boxes(sample_id)
        assert len(boxes) > 0
        assert boxes[0]["class_id"] is not None
        assert "x_center" in boxes[0]
        assert "y_center" in boxes[0]
        assert "width" in boxes[0]
        assert "height" in boxes[0]

    def test_get_sample_boxes_missing_label(self, services, tmp_path):
        ps, ds, ans = services
        project = ps.create_project("test", str(tmp_path / "proj"))
        img_dir, lbl_dir = _create_yolo_dataset(tmp_path, num_images=3)
        # Remove a label so one sample has missing_label status
        os.remove(os.path.join(lbl_dir, "0001.txt"))

        result = ds.import_dataset(project["id"], "ds1", img_dir, lbl_dir)
        samples = ds.get_samples(result["dataset_id"])
        # Find the sample with missing_label status (no label_path)
        missing_samples = [s for s in samples if s["status"] == "missing_label"]
        assert len(missing_samples) == 1

        boxes = ans.get_sample_boxes(missing_samples[0]["id"])
        assert boxes == []

    def test_save_annotation_edit(self, services, tmp_path):
        ps, ds, ans = services
        project, result = _import_dataset_helper(services, tmp_path)
        dataset_id = result["dataset_id"]
        sample_id = self._get_valid_sample_id(ds, dataset_id)

        new_boxes = [
            {"class_id": 5, "x_center": 0.25, "y_center": 0.25, "width": 0.1, "height": 0.1}
        ]
        edit_result = ans.save_annotation_edit(sample_id, new_boxes, source="manual")
        assert edit_result["success"] is True
        assert edit_result["box_count"] == 1

        # Verify the boxes were actually written
        boxes = ans.get_sample_boxes(sample_id)
        assert len(boxes) == 1
        assert boxes[0]["class_id"] == 5
        assert abs(boxes[0]["x_center"] - 0.25) < 1e-5

    def test_save_annotation_edit_not_found(self, services, tmp_path):
        ps, ds, ans = services
        result = ans.save_annotation_edit("nonexistent-id", [], source="manual")
        assert result["success"] is False
        assert "error" in result

    def test_save_annotation_edit_assisted(self, services, tmp_path):
        ps, ds, ans = services
        project, result = _import_dataset_helper(services, tmp_path)
        dataset_id = result["dataset_id"]
        sample_id = self._get_valid_sample_id(ds, dataset_id)

        new_boxes = [
            {"class_id": 0, "x_center": 0.5, "y_center": 0.5, "width": 0.2, "height": 0.2}
        ]
        edit_result = ans.save_annotation_edit(sample_id, new_boxes, source="assisted")
        assert edit_result["success"] is True

    def test_get_annotation_history(self, services, tmp_path):
        ps, ds, ans = services
        project, result = _import_dataset_helper(services, tmp_path)
        dataset_id = result["dataset_id"]
        sample_id = self._get_valid_sample_id(ds, dataset_id)

        # Initially no history
        history = ans.get_annotation_history(sample_id)
        assert len(history) == 0

        # Make an edit
        new_boxes = [
            {"class_id": 3, "x_center": 0.5, "y_center": 0.5, "width": 0.3, "height": 0.3}
        ]
        ans.save_annotation_edit(sample_id, new_boxes, source="manual")

        # Now should have one history entry
        history = ans.get_annotation_history(sample_id)
        assert len(history) == 1
        assert history[0]["action"] == "edit"
        assert history[0]["source"] == "manual"

        # Make another edit
        new_boxes2 = [
            {"class_id": 4, "x_center": 0.6, "y_center": 0.6, "width": 0.2, "height": 0.2}
        ]
        ans.save_annotation_edit(sample_id, new_boxes2, source="assisted")

        history = ans.get_annotation_history(sample_id)
        assert len(history) == 2

    def test_bulk_confirm(self, services, tmp_path):
        ps, ds, ans = services
        project, result = _import_dataset_helper(services, tmp_path, num_images=3)
        dataset_id = result["dataset_id"]

        samples = ds.get_samples(dataset_id, status="valid")
        sample_ids = [s["id"] for s in samples]
        assert len(sample_ids) == 3

        confirm_result = ans.bulk_confirm(sample_ids)
        assert confirm_result["confirmed_count"] == 3
        assert confirm_result["errors"] == []

        # Each sample should now have a "confirm" action in history
        for sid in sample_ids:
            history = ans.get_annotation_history(sid)
            confirm_entries = [h for h in history if h["action"] == "confirm"]
            assert len(confirm_entries) == 1

    def test_bulk_confirm_empty_list(self, services, tmp_path):
        ps, ds, ans = services
        confirm_result = ans.bulk_confirm([])
        assert confirm_result["confirmed_count"] == 0

    def test_bulk_confirm_with_invalid_id(self, services, tmp_path):
        ps, ds, ans = services
        project, result = _import_dataset_helper(services, tmp_path)
        dataset_id = result["dataset_id"]
        valid_sample_id = self._get_valid_sample_id(ds, dataset_id)

        # Mix valid and invalid sample IDs; the invalid one has no boxes so is skipped
        confirm_result = ans.bulk_confirm([valid_sample_id, "nonexistent-id"])
        assert confirm_result["confirmed_count"] == 1
