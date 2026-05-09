"""App context: manages database, services and global resources"""

import os
import logging
from labeltorch.app.infra.db.sqlite import Database, init_database
from labeltorch.app.services.project_service import ProjectService
from labeltorch.app.services.dataset_service import DatasetService
from labeltorch.app.services.annotation_service import AnnotationService

logger = logging.getLogger(__name__)


class AppContext:
    """Application global context"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.expanduser("~"), ".labeltorch", "labeltorch.db")

        self.db: Database = init_database(db_path)
        self.project_service = ProjectService(self.db)
        self.dataset_service = DatasetService(self.db)
        self.annotation_service = AnnotationService(self.db)
        logger.info("App context initialized")

    def close(self):
        """Release resources"""
        self.db.close()
        logger.info("App context closed")
