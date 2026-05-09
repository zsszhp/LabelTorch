"""Model version management service"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from labeltorch.app.infra.db.sqlite import Database

logger = logging.getLogger(__name__)


class VersionService:
    """Model version management"""

    def __init__(self, db: Database):
        self.db = db

    def create_version(self, project_id: str, job_id: str,
                       best_pt_path: str = None,
                       metrics_json: str = None,
                       parent_version_id: str = None) -> dict:
        """Create a model version record"""
        version_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        self.db.execute(
            "INSERT INTO model_versions (id, project_id, job_id, parent_version_id, best_pt_path, metrics_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (version_id, project_id, job_id, parent_version_id,
             best_pt_path, metrics_json, created_at),
        )

        logger.info("Model version created: %s", version_id)
        return {"version_id": version_id}

    def list_versions(self, project_id: str) -> list:
        """List model versions for a project"""
        rows = self.db.fetchall(
            "SELECT * FROM model_versions WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        )
        return [dict(row) for row in rows]

    def get_version(self, version_id: str) -> Optional[dict]:
        """Get version by id"""
        row = self.db.fetchone("SELECT * FROM model_versions WHERE id = ?", (version_id,))
        return dict(row) if row else None

    def get_versions_by_job(self, job_id: str) -> list:
        """Get versions produced by a training job"""
        rows = self.db.fetchall(
            "SELECT * FROM model_versions WHERE job_id = ?",
            (job_id,),
        )
        return [dict(row) for row in rows]
