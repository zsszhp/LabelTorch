"""Unit tests for TrainingService and VersionService"""

import os
import pytest

from labeltorch.app.infra.db.sqlite import init_database
from labeltorch.app.services.project_service import ProjectService
from labeltorch.app.services.dataset_service import DatasetService
from labeltorch.app.services.training_service import TrainingService, TrainConfig, TrainJob
from labeltorch.app.services.version_service import VersionService
from labeltorch.app.domain.enums import TrainJobStatus


@pytest.fixture
def services(tmp_path):
    db = init_database(":memory:")
    ps = ProjectService(db)
    ds = DatasetService(db)
    ts = TrainingService(db)
    vs = VersionService(db)
    yield ps, ds, ts, vs
    db.close()


def _make_project_and_dataset(services, tmp_path):
    ps, ds, ts, vs = services
    project = ps.create_project("test", str(tmp_path / "proj"))
    img_dir = str(tmp_path / "images")
    lbl_dir = str(tmp_path / "labels")
    os.makedirs(img_dir)
    os.makedirs(lbl_dir)
    from PIL import Image
    for i in range(3):
        Image.new("RGB", (64, 64)).save(os.path.join(img_dir, f"img_{i}.png"))
        with open(os.path.join(lbl_dir, f"img_{i}.txt"), "w") as f:
            f.write("0 0.5 0.5 0.3 0.3\n")
    result = ds.import_dataset(project["id"], "ds1", img_dir, lbl_dir)
    return project["id"], result["dataset_id"]


class TestTrainConfig:
    """Test TrainConfig validation"""

    def test_valid_config(self):
        config = TrainConfig()
        assert config.validate() == []

    def test_invalid_model_family(self):
        config = TrainConfig(model_family="invalid")
        assert len(config.validate()) > 0

    def test_invalid_model_size(self):
        config = TrainConfig(model_size="xxl")
        assert len(config.validate()) > 0

    def test_invalid_batch(self):
        config = TrainConfig(batch=0)
        assert len(config.validate()) > 0

    def test_get_model_name(self):
        config = TrainConfig(model_family="yolov8", model_size="s")
        name = config.get_model_name()
        assert "yolov8" in name and "s" in name

    def test_get_model_name_obb(self):
        config = TrainConfig(model_family="yolov8_obb", model_size="m")
        name = config.get_model_name()
        assert "yolov8" in name and "obb" in name.lower()

    def test_json_roundtrip(self):
        config = TrainConfig(model_family="yolov11", model_size="l", epochs=50)
        json_str = config.to_json()
        restored = TrainConfig.from_json(json_str)
        assert restored.model_family == "yolov11"
        assert restored.model_size == "l"
        assert restored.epochs == 50


class TestTrainJobStateMachine:
    """Test TrainJob state transitions"""

    def test_pending_to_running(self):
        job = TrainJob("j1", TrainJobStatus.PENDING)
        assert job.can_transition_to(TrainJobStatus.RUNNING)

    def test_pending_to_stopped(self):
        job = TrainJob("j1", TrainJobStatus.PENDING)
        assert job.can_transition_to(TrainJobStatus.STOPPED)

    def test_running_to_succeeded(self):
        job = TrainJob("j1", TrainJobStatus.RUNNING)
        assert job.can_transition_to(TrainJobStatus.SUCCEEDED)

    def test_running_to_failed(self):
        job = TrainJob("j1", TrainJobStatus.RUNNING)
        assert job.can_transition_to(TrainJobStatus.FAILED)

    def test_succeeded_no_transition(self):
        job = TrainJob("j1", TrainJobStatus.SUCCEEDED)
        assert not job.can_transition_to(TrainJobStatus.RUNNING)
        assert not job.can_transition_to(TrainJobStatus.PENDING)

    def test_failed_no_transition(self):
        job = TrainJob("j1", TrainJobStatus.FAILED)
        assert not job.can_transition_to(TrainJobStatus.RUNNING)


class TestTrainingService:
    """Test TrainingService CRUD"""

    def test_create_train_job(self, services, tmp_path):
        ps, ds, ts, vs = services
        project_id, dataset_id = _make_project_and_dataset(services, tmp_path)
        config = TrainConfig(model_family="yolov8", model_size="n")
        result = ts.create_train_job(project_id, dataset_id, config)
        assert result["job_id"] is not None
        assert result["errors"] == []

    def test_create_train_job_invalid_config(self, services, tmp_path):
        ps, ds, ts, vs = services
        project_id, dataset_id = _make_project_and_dataset(services, tmp_path)
        config = TrainConfig(model_family="bad", model_size="xxl")
        result = ts.create_train_job(project_id, dataset_id, config)
        assert result["job_id"] is None
        assert len(result["errors"]) > 0

    def test_get_job(self, services, tmp_path):
        ps, ds, ts, vs = services
        project_id, dataset_id = _make_project_and_dataset(services, tmp_path)
        config = TrainConfig()
        result = ts.create_train_job(project_id, dataset_id, config)
        job = ts.get_job(result["job_id"])
        assert job is not None
        assert job["status"] == TrainJobStatus.PENDING

    def test_list_jobs(self, services, tmp_path):
        ps, ds, ts, vs = services
        project_id, dataset_id = _make_project_and_dataset(services, tmp_path)
        config = TrainConfig()
        ts.create_train_job(project_id, dataset_id, config)
        ts.create_train_job(project_id, dataset_id, config)
        jobs = ts.list_jobs(project_id)
        assert len(jobs) == 2


class TestVersionService:
    """Test VersionService"""

    def test_create_version(self, services, tmp_path):
        ps, ds, ts, vs = services
        project_id, dataset_id = _make_project_and_dataset(services, tmp_path)
        config = TrainConfig()
        job_result = ts.create_train_job(project_id, dataset_id, config)
        job = ts.get_job(job_result["job_id"])

        result = vs.create_version(
            project_id, job["id"],
            best_pt_path="/tmp/best.pt",
        )
        assert result["version_id"] is not None

    def test_list_versions(self, services, tmp_path):
        ps, ds, ts, vs = services
        project_id, dataset_id = _make_project_and_dataset(services, tmp_path)
        config = TrainConfig()
        job_result = ts.create_train_job(project_id, dataset_id, config)

        vs.create_version(project_id, job_result["job_id"], best_pt_path="/tmp/a.pt")
        vs.create_version(project_id, job_result["job_id"], best_pt_path="/tmp/b.pt")

        versions = vs.list_versions(project_id)
        assert len(versions) == 2

    def test_get_version(self, services, tmp_path):
        ps, ds, ts, vs = services
        project_id, dataset_id = _make_project_and_dataset(services, tmp_path)
        config = TrainConfig()
        job_result = ts.create_train_job(project_id, dataset_id, config)

        result = vs.create_version(project_id, job_result["job_id"])
        version = vs.get_version(result["version_id"])
        assert version is not None
        assert version["job_id"] == job_result["job_id"]

    def test_parent_version(self, services, tmp_path):
        ps, ds, ts, vs = services
        project_id, dataset_id = _make_project_and_dataset(services, tmp_path)
        config = TrainConfig()
        job_result = ts.create_train_job(project_id, dataset_id, config)

        v1 = vs.create_version(project_id, job_result["job_id"])
        v2 = vs.create_version(
            project_id, job_result["job_id"],
            parent_version_id=v1["version_id"],
        )
        version = vs.get_version(v2["version_id"])
        assert version["parent_version_id"] == v1["version_id"]
