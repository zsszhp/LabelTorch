"""Unit tests for ProjectService"""

import os
import tempfile
import pytest

from labeltorch.app.infra.db.sqlite import init_database
from labeltorch.app.services.project_service import ProjectService


@pytest.fixture
def project_service(tmp_path):
    """Create a ProjectService with in-memory DB for testing"""
    db = init_database(":memory:")
    svc = ProjectService(db)
    yield svc
    db.close()


class TestProjectServiceCreate:
    """Test project creation"""

    def test_create_project(self, project_service, tmp_path):
        """Create a project returns dict with expected fields"""
        root = str(tmp_path / "proj1")
        p = project_service.create_project("TestProj", root)
        assert p["name"] == "TestProj"
        assert p["root_path"] == root
        assert "id" in p
        assert "created_at" in p

    def test_create_project_makes_dirs(self, project_service, tmp_path):
        """Creating a project creates the data subdirectories"""
        root = str(tmp_path / "proj2")
        project_service.create_project("DirTest", root)
        assert os.path.isdir(os.path.join(root, "datasets"))
        assert os.path.isdir(os.path.join(root, "models"))
        assert os.path.isdir(os.path.join(root, "exports"))
        assert os.path.isdir(os.path.join(root, ".cache"))


class TestProjectServiceList:
    """Test project listing"""

    def test_list_empty(self, project_service):
        """List returns empty when no projects"""
        result = project_service.list_projects()
        assert result == []

    def test_list_after_create(self, project_service, tmp_path):
        """List returns created projects"""
        project_service.create_project("A", str(tmp_path / "a"))
        project_service.create_project("B", str(tmp_path / "b"))
        result = project_service.list_projects()
        assert len(result) >= 2
        names = [p["name"] for p in result]
        assert "A" in names
        assert "B" in names


class TestProjectServiceGet:
    """Test project retrieval"""

    def test_get_existing(self, project_service, tmp_path):
        """Get returns the correct project"""
        p = project_service.create_project("GetTest", str(tmp_path / "g"))
        result = project_service.get_project(p["id"])
        assert result is not None
        assert result["name"] == "GetTest"

    def test_get_nonexistent(self, project_service):
        """Get returns None for nonexistent project"""
        result = project_service.get_project("nonexistent-id")
        assert result is None


class TestProjectServiceDelete:
    """Test project deletion"""

    def test_delete_existing(self, project_service, tmp_path):
        """Delete removes project from database"""
        p = project_service.create_project("DelTest", str(tmp_path / "d"))
        assert project_service.delete_project(p["id"]) is True
        assert project_service.get_project(p["id"]) is None

    def test_delete_nonexistent(self, project_service):
        """Delete returns False for nonexistent project"""
        assert project_service.delete_project("nonexistent-id") is False
