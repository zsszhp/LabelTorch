"""SQLite database connection management and initialization"""

import os
import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DB_VERSION = 1


class Database:
    """SQLite database manager with WAL mode"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self._conn is None:
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not self.db_path.startswith(":"):
                os.makedirs(db_dir, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            if not self.db_path.startswith(":"):
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.execute("PRAGMA busy_timeout=5000")
            logger.info("Database connected: %s", self.db_path)
        return self._conn

    def close(self):
        """Close database connection"""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL statement"""
        conn = self.connect()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error("SQL error: %s, SQL: %s", e, sql)
            raise

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Query single record"""
        conn = self.connect()
        cursor = conn.execute(sql, params)
        return cursor.fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        """Query all records"""
        conn = self.connect()
        cursor = conn.execute(sql, params)
        return cursor.fetchall()

    def get_version(self) -> int:
        """Get current database schema version"""
        try:
            row = self.fetchone("SELECT version FROM schema_version WHERE id = 1")
            return row["version"] if row else 0
        except sqlite3.OperationalError:
            return 0

    def set_version(self, version: int):
        """Set database schema version"""
        self.execute(
            "INSERT OR REPLACE INTO schema_version (id, version) VALUES (1, ?)",
            (version,),
        )


def init_database(db_path: str) -> Database:
    """Initialize database and run migrations"""
    db = Database(db_path)
    db.connect()

    # Ensure schema_version table exists
    db.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY,
            version INTEGER NOT NULL
        )
    """)

    current_version = db.get_version()
    logger.info("Current DB version: %d, target: %d", current_version, DB_VERSION)

    # Run migrations
    if current_version < 1:
        from labeltorch.app.infra.db.migrations.v001_initial import migrate
        migrate(db)
        db.set_version(1)
        logger.info("Migration v001_initial completed")

    return db
