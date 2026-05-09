"""Unit tests for database initialization and CRUD operations"""

import os
import tempfile
import pytest

from labeltorch.app.infra.db.sqlite import Database, init_database


class TestDatabaseInit:
    """Test database initialization and migration"""

    def test_init_in_memory(self):
        """Database can be initialized with in-memory SQLite"""
        db = init_database(":memory:")
        assert db is not None
        assert db._conn is not None
        db.close()

    def test_init_file_based(self):
        """Database can be initialized with file path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = init_database(db_path)
            assert os.path.exists(db_path)
            db.close()

    def test_migration_creates_tables(self):
        """Migration v001 creates all 7 core tables"""
        db = init_database(":memory:")
        tables = db.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [row["name"] for row in tables]
        expected = [
            "annotation_changes",
            "class_mappings",
            "dataset_samples",
            "datasets",
            "export_tasks",
            "model_versions",
            "projects",
            "schema_version",
            "train_jobs",
        ]
        for t in expected:
            assert t in table_names, f"Table {t} not found"
        db.close()

    def test_migration_idempotent(self):
        """Running migration twice does not fail"""
        db = init_database(":memory:")
        # Re-run init - should not raise
        from labeltorch.app.infra.db.migrations.v001_initial import migrate
        migrate(db)  # IF NOT EXISTS protects this
        db.close()

    def test_schema_version_tracked(self):
        """Schema version is tracked after migration"""
        db = init_database(":memory:")
        version = db.get_version()
        assert version == 1
        db.close()


class TestDatabaseCRUD:
    """Test basic CRUD on core tables"""

    def _get_db(self):
        return init_database(":memory:")

    def test_project_crud(self):
        """Projects can be created, read, and deleted"""
        db = self._get_db()

        # Create
        db.execute(
            "INSERT INTO projects (id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
            ("p1", "test_project", "/tmp/test", "2026-01-01T00:00:00"),
        )

        # Read
        row = db.fetchone("SELECT * FROM projects WHERE id = ?", ("p1",))
        assert row is not None
        assert row["name"] == "test_project"
        assert row["root_path"] == "/tmp/test"

        # List
        rows = db.fetchall("SELECT * FROM projects")
        assert len(rows) >= 1

        # Delete
        db.execute("DELETE FROM projects WHERE id = ?", ("p1",))
        row = db.fetchone("SELECT * FROM projects WHERE id = ?", ("p1",))
        assert row is None

        db.close()

    def test_dataset_with_project(self):
        """Dataset can be created linked to a project"""
        db = self._get_db()

        db.execute(
            "INSERT INTO projects (id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
            ("p1", "proj", "/tmp/p1", "2026-01-01T00:00:00"),
        )
        db.execute(
            "INSERT INTO datasets (id, project_id, name, image_dir, label_dir, format, sample_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("d1", "p1", "dataset1", "/tmp/img", "/tmp/lbl", "yolo_txt", 100, "2026-01-01T00:00:00"),
        )

        row = db.fetchone("SELECT * FROM datasets WHERE id = ?", ("d1",))
        assert row is not None
        assert row["project_id"] == "p1"
        assert row["sample_count"] == 100

        db.close()

    def test_train_job_with_status(self):
        """TrainJob can be created and status tracked"""
        db = self._get_db()

        db.execute(
            "INSERT INTO projects (id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
            ("p1", "proj", "/tmp/p1", "2026-01-01T00:00:00"),
        )
        db.execute(
            "INSERT INTO datasets (id, project_id, name, image_dir, label_dir, format, sample_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("d1", "p1", "ds", "/tmp/img", "/tmp/lbl", "yolo_txt", 10, "2026-01-01T00:00:00"),
        )
        db.execute(
            "INSERT INTO train_jobs (id, project_id, dataset_id, model_family, config_json, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("j1", "p1", "d1", "yolov8", '{"epochs":100}', "pending", "2026-01-01T00:00:00"),
        )

        row = db.fetchone("SELECT * FROM train_jobs WHERE id = ?", ("j1",))
        assert row["status"] == "pending"

        # Update status
        db.execute("UPDATE train_jobs SET status = ? WHERE id = ?", ("running", "j1"))
        row = db.fetchone("SELECT * FROM train_jobs WHERE id = ?", ("j1",))
        assert row["status"] == "running"

        db.close()

    def test_foreign_key_cascade(self):
        """Deleting project cascades to datasets"""
        db = self._get_db()

        db.execute(
            "INSERT INTO projects (id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
            ("p1", "proj", "/tmp/p1", "2026-01-01T00:00:00"),
        )
        db.execute(
            "INSERT INTO datasets (id, project_id, name, image_dir, label_dir, format, sample_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("d1", "p1", "ds", "/tmp/img", "/tmp/lbl", "yolo_txt", 10, "2026-01-01T00:00:00"),
        )

        # Delete project
        db.execute("DELETE FROM projects WHERE id = ?", ("p1",))

        # Dataset should be gone
        row = db.fetchone("SELECT * FROM datasets WHERE id = ?", ("d1",))
        assert row is None

        db.close()
