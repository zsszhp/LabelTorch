"""应用上下文：管理数据库、服务等全局资源"""

import os
import logging
from labeltorch.app.infra.db.sqlite import Database, init_database
from labeltorch.app.services.project_service import ProjectService

logger = logging.getLogger(__name__)


class AppContext:
    """应用全局上下文"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认在用户目录下存储
            db_path = os.path.join(os.path.expanduser("~"), ".labeltorch", "labeltorch.db")

        self.db: Database = init_database(db_path)
        self.project_service = ProjectService(self.db)
        logger.info("应用上下文初始化完成")

    def close(self):
        """释放资源"""
        self.db.close()
        logger.info("应用上下文已关闭")
