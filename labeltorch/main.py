"""LabelTorch main entry point"""

import sys
import os
import logging
import traceback

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from labeltorch.app.infra.logging.logger import setup_logger
from labeltorch.app.context import AppContext
from labeltorch.app.ui.main_window import MainWindow


def global_exception_handler(exc_type, exc_value, exc_tb):
    """Global uncaught exception handler"""
    logger = logging.getLogger("labeltorch")
    logger.critical(
        "Uncaught exception:\n%s",
        "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
    )
    try:
        QMessageBox.critical(
            None,
            "Unexpected Error",
            f"An unexpected error occurred:\n{exc_value}\n\nCheck logs for details.",
        )
    except Exception:
        pass


def main():
    """Application main function"""
    # Setup logging
    log_dir = os.path.join(os.path.expanduser("~"), ".labeltorch", "logs")
    logger = setup_logger(log_dir=log_dir)
    logger.info("LabelTorch starting...")

    # Global exception handler
    sys.excepthook = global_exception_handler

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("LabelTorch")
    app.setOrganizationName("LabelTorch")

    # Initialize app context
    ctx = AppContext()

    # Create main window and inject project service
    window = MainWindow(project_service=ctx.project_service)
    window.show()
    logger.info("LabelTorch started")

    # Event loop
    exit_code = app.exec()

    # Cleanup
    ctx.close()
    logger.info("LabelTorch exited")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
