"""应用上下文：持有数据库、服务等全局对象"""

import os
import logging
from labeltorch.app.infra.db.sqlite import Database, init_database
from labeltorch.app.services.project_service import ProjectService

logger = logging.getLogger(__name__)


class AppContext:
    """应用全局上下文"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认数据库路径：用户主目录下 .labeltorch/metadata.db
            db_dir = os.path.join(os.path.expanduser("~"), ".labeltorch")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "metadata.db")

        self.db: Database = init_database(db_path)
        self.project_service: ProjectService = ProjectService(self.db)
        logger.info("应用上下文初始化完成，数据库: %s", db_path)

    def close(self):
        """关闭所有资源"""
        self.db.close()
        logger.info("应用上下文已关闭")
