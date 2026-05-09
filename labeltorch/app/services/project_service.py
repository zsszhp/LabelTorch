"""Project service: create, open, list, delete projects"""

import os
import uuid
import logging
from datetime import datetime
from typing import Optional

from labeltorch.app.infra.db.sqlite import Database, init_database

logger = logging.getLogger(__name__)


class ProjectService:
    """Project management service"""

    def __init__(self, db: Database):
        self.db = db

    def create_project(self, name: str, root_path: str) -> dict:
        """Create a new project

        Args:
            name: project name
            root_path: project root directory

        Returns:
            project dict
        """
        project_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        os.makedirs(root_path, exist_ok=True)
        for subdir in ["datasets", "models", "exports", ".cache"]:
            os.makedirs(os.path.join(root_path, subdir), exist_ok=True)

        self.db.execute(
            "INSERT INTO projects (id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
            (project_id, name, root_path, created_at),
        )
        logger.info("Project created: %s (%s)", name, project_id)

        # Initialize project-local database
        project_db_path = os.path.join(root_path, "labeltorch.db")
        init_database(project_db_path)

        return {
            "id": project_id,
            "name": name,
            "root_path": root_path,
            "created_at": created_at,
        }

    def list_projects(self) -> list:
        """List all projects"""
        rows = self.db.fetchall("SELECT * FROM projects ORDER BY created_at DESC")
        return [dict(row) for row in rows]

    def get_project(self, project_id: str) -> Optional[dict]:
        """Get project by ID"""
        row = self.db.fetchone("SELECT * FROM projects WHERE id = ?", (project_id,))
        return dict(row) if row else None

    def delete_project(self, project_id: str) -> bool:
        """Delete project (metadata only, files untouched)"""
        project = self.get_project(project_id)
        if project is None:
            logger.warning("Project not found: %s", project_id)
            return False
        self.db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        logger.info("Project deleted: %s", project_id)
        return True

    def open_project_db(self, project_id: str) -> Optional[Database]:
        """Open project-local database"""
        project = self.get_project(project_id)
        if project is None:
            return None
        db_path = os.path.join(project["root_path"], "labeltorch.db")
        if not os.path.exists(db_path):
            return init_database(db_path)
        db = Database(db_path)
        db.connect()
        return db
