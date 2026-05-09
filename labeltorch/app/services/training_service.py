"""Training service: create/start/stop train jobs, state machine"""

import os
import uuid
import json
import logging
import subprocess
import threading
from datetime import datetime
from typing import Optional

from labeltorch.app.infra.db.sqlite import Database
from labeltorch.app.domain.enums import TrainJobStatus, ModelFamily

logger = logging.getLogger(__name__)

# Valid state transitions
VALID_TRANSITIONS = {
    TrainJobStatus.PENDING: {TrainJobStatus.RUNNING, TrainJobStatus.STOPPED},
    TrainJobStatus.RUNNING: {TrainJobStatus.SUCCEEDED, TrainJobStatus.FAILED, TrainJobStatus.STOPPED},
    # Terminal states - no transitions out
    TrainJobStatus.SUCCEEDED: set(),
    TrainJobStatus.FAILED: set(),
    TrainJobStatus.STOPPED: set(),
}


class TrainConfig:
    """Training configuration with validation"""

    VALID_FAMILIES = {f.value for f in ModelFamily}
    VALID_SIZES = {"n", "s", "m", "l", "x"}

    def __init__(self, model_family: str = "yolov8", model_size: str = "n",
                 img_size: int = 640, batch: int = 16, epochs: int = 100,
                 patience: int = 50, device: str = "cpu", workers: int = 4,
                 pretrained_weights: Optional[str] = None):
        self.model_family = model_family
        self.model_size = model_size
        self.img_size = img_size
        self.batch = batch
        self.epochs = epochs
        self.patience = patience
        self.device = device
        self.workers = workers
        self.pretrained_weights = pretrained_weights

    def validate(self) -> list:
        """Validate config, return list of error messages"""
        errors = []
        if self.model_family not in self.VALID_FAMILIES:
            errors.append(f"Invalid model_family: {self.model_family}")
        if self.model_size not in self.VALID_SIZES:
            errors.append(f"Invalid model_size: {self.model_size}")
        if self.img_size < 32 or self.img_size > 4096:
            errors.append(f"Invalid img_size: {self.img_size}")
        if self.batch < 1:
            errors.append(f"Invalid batch: {self.batch}")
        if self.epochs < 1:
            errors.append(f"Invalid epochs: {self.epochs}")
        if self.patience < 0:
            errors.append(f"Invalid patience: {self.patience}")
        if self.workers < 0:
            errors.append(f"Invalid workers: {self.workers}")
        return errors

    def get_model_name(self) -> str:
        """Get Ultralytics model name (e.g. yolov8n, yolov8m-obb)"""
        family = self.model_family
        if family == "yolov8_obb":
            return f"yolov8{self.model_size}-obb"
        return f"{family}{self.model_size}"

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)

    @staticmethod
    def from_json(s: str) -> "TrainConfig":
        d = json.loads(s)
        return TrainConfig(**{k: v for k, v in d.items() if k in TrainConfig.__init__.__code__.co_varnames})


class TrainJob:
    """Training job state machine"""

    VALID_TRANSITIONS = {
        TrainJobStatus.PENDING: {TrainJobStatus.RUNNING, TrainJobStatus.STOPPED},
        TrainJobStatus.RUNNING: {TrainJobStatus.SUCCEEDED, TrainJobStatus.FAILED, TrainJobStatus.STOPPED},
        TrainJobStatus.SUCCEEDED: set(),
        TrainJobStatus.FAILED: set(),
        TrainJobStatus.STOPPED: set(),
    }

    def __init__(self, id: str, status: str):
        self.id = id
        self.status = status

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.VALID_TRANSITIONS.get(TrainJobStatus(self.status), set())


class TrainingService:
    """Training job management service"""

    def __init__(self, db: Database):
        self.db = db
        self._process: Optional[subprocess.Popen] = None
        self._monitor_thread: Optional[threading.Thread] = None

    def create_train_job(self, project_id: str, dataset_id: str,
                         config: TrainConfig) -> dict:
        """Create a new training job with config snapshot (immutable)"""
        errors = config.validate()
        if errors:
            return {"job_id": None, "errors": errors}

        job_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        self.db.execute(
            "INSERT INTO train_jobs (id, project_id, dataset_id, model_family, "
            "config_json, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, project_id, dataset_id, config.model_family,
             config.to_json(), TrainJobStatus.PENDING, created_at),
        )

        logger.info("Train job created: %s (%s)", job_id, config.model_family)
        return {"job_id": job_id, "errors": []}

    def get_job(self, job_id: str) -> Optional[dict]:
        """Get train job by ID"""
        row = self.db.fetchone("SELECT * FROM train_jobs WHERE id = ?", (job_id,))
        return dict(row) if row else None

    def list_jobs(self, project_id: str) -> list:
        """List train jobs for a project"""
        rows = self.db.fetchall(
            "SELECT * FROM train_jobs WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        )
        return [dict(row) for row in rows]

    def _transition_status(self, job_id: str, new_status: str) -> bool:
        """Transition job status with state machine validation"""
        job = self.get_job(job_id)
        if not job:
            return False

        current = TrainJobStatus(job["status"])
        target = TrainJobStatus(new_status)

        if target not in VALID_TRANSITIONS.get(current, set()):
            logger.warning("Invalid transition: %s -> %s for job %s", current, target, job_id)
            return False

        now = datetime.now().isoformat()
        updates = {"status": new_status}
        if new_status == TrainJobStatus.RUNNING:
            updates["started_at"] = now
        elif new_status in (TrainJobStatus.SUCCEEDED, TrainJobStatus.FAILED, TrainJobStatus.STOPPED):
            updates["finished_at"] = now

        set_clauses = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [job_id]
        self.db.execute(f"UPDATE train_jobs SET {set_clauses} WHERE id = ?", values)

        logger.info("Job %s: %s -> %s", job_id, current, target)
        return True

    def start_train_job(self, job_id: str, yaml_path: str, project_root: str) -> bool:
        """Start a training job as subprocess"""
        job = self.get_job(job_id)
        if not job:
            return False

        config = TrainConfig.from_json(job["config_json"])

        # Build Ultralytics training command
        model_name = config.get_model_name()
        log_path = os.path.join(project_root, "models", job_id, "train.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        cmd = [
            "python", "-m", "ultralytics",
            "train",
            f"model={model_name}",
            f"data={yaml_path}",
            f"epochs={config.epochs}",
            f"imgsz={config.img_size}",
            f"batch={config.batch}",
            f"patience={config.patience}",
            f"device={config.device}",
            f"workers={config.workers}",
            f"project={os.path.join(project_root, 'models')}",
            f"name={job_id}",
        ]

        if config.pretrained_weights:
            cmd.append(f"resume={config.pretrained_weights}")

        try:
            with open(log_path, "w") as log_file:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

            self._transition_status(job_id, TrainJobStatus.RUNNING)

            # Update log path
            self.db.execute(
                "UPDATE train_jobs SET log_path = ? WHERE id = ?",
                (log_path, job_id),
            )

            # Start monitor thread
            self._monitor_thread = threading.Thread(
                target=self._monitor_process,
                args=(job_id,),
                daemon=True,
            )
            self._monitor_thread.start()

            logger.info("Training started: %s, PID=%d", job_id, self._process.pid)
            return True

        except Exception as e:
            logger.error("Failed to start training: %s", e)
            self._transition_status(job_id, TrainJobStatus.FAILED)
            return False

    def stop_train_job(self, job_id: str) -> bool:
        """Stop a running training job"""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
            logger.info("Training process terminated: %s", job_id)

        return self._transition_status(job_id, TrainJobStatus.STOPPED)

    def _monitor_process(self, job_id: str):
        """Monitor training subprocess and update status on completion"""
        if not self._process:
            return
        return_code = self._process.wait()
        if return_code == 0:
            self._transition_status(job_id, TrainJobStatus.SUCCEEDED)
            # Auto-create model version
            self._create_version_on_success(job_id)
        else:
            self._transition_status(job_id, TrainJobStatus.FAILED)

    def _create_version_on_success(self, job_id: str):
        """Create model version after successful training"""
        from labeltorch.app.services.version_service import VersionService
        job = self.get_job(job_id)
        if not job:
            return

        vs = VersionService(self.db)
        # Look for best.pt in the training output directory
        best_pt = os.path.join(
            json.loads(job.get("config_json", "{}")).get("project_root", ""),
            "models", job_id, "weights", "best.pt",
        )
        if not os.path.exists(best_pt):
            # Try Ultralytics default path
            best_pt = None

        vs.create_version(
            project_id=job["project_id"],
            job_id=job_id,
            best_pt_path=best_pt,
        )

    def get_train_log(self, job_id: str, tail: int = 100) -> str:
        """Get last N lines of training log"""
        job = self.get_job(job_id)
        if not job or not job.get("log_path"):
            return ""
        log_path = job["log_path"]
        if not os.path.exists(log_path):
            return ""
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            return "".join(lines[-tail:])
        except Exception:
            return ""
