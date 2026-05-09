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
from labeltorch.app.infra.startup_check import StartupCheck


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

    # Startup self-check
    checker = StartupCheck()
    results = checker.run_all()
    if checker.has_errors():
        logger.error("Startup check failed")
        # Still try to start, but warn user
        try:
            app = QApplication(sys.argv)
            QMessageBox.warning(
                None, "Startup Check Failed",
                f"Some checks failed:\n\n{checker.get_summary_text()}\n\n"
                "The application may not work correctly.",
            )
        except Exception:
            pass

    # Create Qt application
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("LabelTorch")
    app.setOrganizationName("LabelTorch")

    # Initialize app context
    ctx = AppContext()

    # Create main window
    window = MainWindow()
    window.set_app_context(ctx)
    window.show()

    if checker.has_warnings():
        logger.warning("Startup warnings: %s", checker.get_summary_text())

    logger.info("LabelTorch started")
    logger.info("Startup check:\n%s", checker.get_summary_text())

    # Event loop
    exit_code = app.exec()

    # Cleanup
    ctx.close()
    logger.info("LabelTorch exited")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
