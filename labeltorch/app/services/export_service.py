"""Export service: pt/onnx model export"""

import os
import uuid
import json
import shutil
import logging
import subprocess
import threading
from datetime import datetime
from typing import Optional, Callable

from labeltorch.app.infra.db.sqlite import Database
from labeltorch.app.domain.enums import ExportStatus

logger = logging.getLogger(__name__)


class ExportService:
    """Model export service"""

    def __init__(self, db: Database):
        self.db = db

    def create_export_task(self, version_id: str, fmt: str = "pt",
                           options: dict = None) -> dict:
        """Create an export task"""
        task_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        options_json = json.dumps(options) if options else None

        self.db.execute(
            "INSERT INTO export_tasks (id, version_id, format, options_json, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, version_id, fmt, options_json, ExportStatus.PENDING, created_at),
        )

        logger.info("Export task created: %s (format=%s)", task_id, fmt)
        return {"task_id": task_id}

    def run_export_pt(self, task_id: str, project_root: str) -> bool:
        """Export model as .pt (copy best.pt to export directory)"""
        task = self.get_task(task_id)
        if not task:
            return False

        version_id = task["version_id"]
        version_row = self.db.fetchone("SELECT * FROM model_versions WHERE id = ?", (version_id,))
        if not version_row or not version_row["best_pt_path"]:
            self._update_status(task_id, ExportStatus.FAILED)
            return False

        src = version_row["best_pt_path"]
        if not os.path.exists(src):
            self._update_status(task_id, ExportStatus.FAILED)
            return False

        # Copy to exports directory
        export_dir = os.path.join(project_root, "exports", task_id)
        os.makedirs(export_dir, exist_ok=True)
        dst = os.path.join(export_dir, os.path.basename(src))

        self._update_status(task_id, ExportStatus.RUNNING)
        try:
            shutil.copy2(src, dst)
            self.db.execute(
                "UPDATE export_tasks SET output_path = ?, status = ?, finished_at = ? WHERE id = ?",
                (dst, ExportStatus.SUCCEEDED, datetime.now().isoformat(), task_id),
            )
            logger.info("PT export succeeded: %s -> %s", src, dst)
            return True
        except Exception as e:
            logger.error("PT export failed: %s", e)
            self._update_status(task_id, ExportStatus.FAILED)
            return False

    def run_export_onnx(self, task_id: str, project_root: str,
                        opset: int = 13, dynamic: bool = True,
                        simplify: bool = True,
                        log_callback: Optional[Callable] = None) -> bool:
        """Export model as ONNX using Ultralytics export API"""
        task = self.get_task(task_id)
        if not task:
            return False

        version_id = task["version_id"]
        version_row = self.db.fetchone("SELECT * FROM model_versions WHERE id = ?", (version_id,))
        if not version_row or not version_row["best_pt_path"]:
            self._update_status(task_id, ExportStatus.FAILED)
            return False

        pt_path = version_row["best_pt_path"]
        if not os.path.exists(pt_path):
            self._update_status(task_id, ExportStatus.FAILED)
            return False

        self._update_status(task_id, ExportStatus.RUNNING)

        # Build export script
        export_dir = os.path.join(project_root, "exports", task_id)
        os.makedirs(export_dir, exist_ok=True)

        script = (
            f"from ultralytics import YOLO\n"
            f"model = YOLO(r'{pt_path}')\n"
            f"model.export(format='onnx', imgsz=640, opset={opset}, "
            f"dynamic={dynamic}, simplify={simplify})\n"
        )
        script_path = os.path.join(export_dir, "_export_onnx.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        # Run in subprocess
        def _run():
            try:
                proc = subprocess.Popen(
                    ["python", script_path],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                    cwd=export_dir,
                )
                for line in proc.stdout:
                    if log_callback:
                        log_callback(line.strip())

                proc.wait()

                # Find the exported onnx file
                onnx_path = pt_path.replace(".pt", ".onnx")
                # Ultralytics typically saves alongside the .pt file
                possible_paths = [
                    onnx_path,
                    os.path.join(os.path.dirname(pt_path), "best.onnx"),
                ]
                found_path = None
                for p in possible_paths:
                    if os.path.exists(p):
                        # Move to export dir
                        dst = os.path.join(export_dir, os.path.basename(p))
                        shutil.move(p, dst)
                        found_path = dst
                        break

                if proc.returncode == 0 and found_path:
                    self.db.execute(
                        "UPDATE export_tasks SET output_path = ?, status = ?, finished_at = ? WHERE id = ?",
                        (found_path, ExportStatus.SUCCEEDED, datetime.now().isoformat(), task_id),
                    )
                    logger.info("ONNX export succeeded: %s", found_path)
                else:
                    self._update_status(task_id, ExportStatus.FAILED)
                    logger.error("ONNX export failed: rc=%d", proc.returncode)

            except Exception as e:
                self._update_status(task_id, ExportStatus.FAILED)
                logger.error("ONNX export exception: %s", e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return True

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get export task by id"""
        row = self.db.fetchone("SELECT * FROM export_tasks WHERE id = ?", (task_id,))
        return dict(row) if row else None

    def list_tasks(self, version_id: str) -> list:
        """List export tasks for a version"""
        rows = self.db.fetchall(
            "SELECT * FROM export_tasks WHERE version_id = ? ORDER BY created_at DESC",
            (version_id,),
        )
        return [dict(row) for row in rows]

    def _update_status(self, task_id: str, new_status: str):
        """Update export task status"""
        if new_status in (ExportStatus.SUCCEEDED, ExportStatus.FAILED):
            self.db.execute(
                "UPDATE export_tasks SET status = ?, finished_at = ? WHERE id = ?",
                (new_status, datetime.now().isoformat(), task_id),
            )
        else:
            self.db.execute(
                "UPDATE export_tasks SET status = ? WHERE id = ?",
                (new_status, task_id),
            )
