"""Main window: sidebar navigation + content area + page switching"""

import logging

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel,
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class NavButton(QPushButton):
    """Sidebar navigation button"""

    def __init__(self, text: str, page_index: int, parent=None):
        super().__init__(text, parent)
        self.page_index = page_index
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("navButton")


class MainWindow(QMainWindow):
    """LabelTorch main window"""

    PAGE_PROJECT = 0
    PAGE_DATASET = 1
    PAGE_ANNOTATION = 2
    PAGE_TRAIN = 3
    PAGE_EXPORT = 4

    def __init__(self, app_context=None):
        super().__init__()
        self._app_context = app_context
        self._current_project = None

        self.setWindowTitle("LabelTorch - Industrial Defect Detection Tool")
        self.setMinimumSize(1200, 800)
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        nav_widget = QWidget()
        nav_widget.setObjectName("navPanel")
        nav_widget.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(8, 16, 8, 16)

        logo = QLabel("LabelTorch")
        logo.setObjectName("logoLabel")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(logo)
        nav_layout.addSpacing(20)

        self.nav_buttons = []
        pages = [
            ("Project", self.PAGE_PROJECT),
            ("Dataset", self.PAGE_DATASET),
            ("Annotation", self.PAGE_ANNOTATION),
            ("Training", self.PAGE_TRAIN),
            ("Export", self.PAGE_EXPORT),
        ]
        for text, idx in pages:
            btn = NavButton(text, idx)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            self.nav_buttons.append(btn)
            nav_layout.addWidget(btn)

        nav_layout.addStretch()

        ver = QLabel("V0.1.0 MVP")
        ver.setObjectName("versionLabel")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(ver)

        main_layout.addWidget(nav_widget)

        # --- Content area ---
        content = QWidget()
        content.setObjectName("contentPanel")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)

        # Status bar
        self.status_label = QLabel("Create or select a project to begin")
        self.status_label.setObjectName("statusLabel")
        content_layout.addWidget(self.status_label)

        # Page stack
        self.page_stack = QStackedWidget()
        content_layout.addWidget(self.page_stack)

        main_layout.addWidget(content, 1)

        # Load page widgets
        self._pages = []
        self._load_pages()

        # Default page
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)

        self._apply_style()

    def _load_pages(self):
        from labeltorch.app.ui.pages.project_page import ProjectPage
        from labeltorch.app.ui.pages.dataset_page import DatasetPage
        from labeltorch.app.ui.pages.annotation_page import AnnotationPage
        from labeltorch.app.ui.pages.train_page import TrainPage
        from labeltorch.app.ui.pages.export_page import ExportPage

        page_classes = [ProjectPage, DatasetPage, AnnotationPage, TrainPage, ExportPage]
        for cls in page_classes:
            page = cls()
            if self._app_context and hasattr(page, 'set_app_context'):
                page.set_app_context(self._app_context)
            self._pages.append(page)
            self.page_stack.addWidget(page)

    def _switch_page(self, index: int):
        self.page_stack.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.setChecked(btn.page_index == index)

    def set_current_project(self, project: dict):
        self._current_project = project
        self.status_label.setText(
            "Project: {}  |  Path: {}".format(project["name"], project["root_path"])
        )
        for page in self._pages:
            if hasattr(page, 'on_project_changed'):
                page.on_project_changed(project)
        self._switch_page(self.PAGE_DATASET)
        self.nav_buttons[self.PAGE_DATASET].setChecked(True)

    def get_current_project(self):
        return self._current_project

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            #navPanel {
                background-color: #2c3e50;
                border-right: 1px solid #34495e;
            }
            #logoLabel {
                color: #ecf0f1; font-size: 18px; font-weight: bold; padding: 8px;
            }
            #versionLabel {
                color: #95a5a6; font-size: 12px; padding: 4px;
            }
            QPushButton#navButton {
                background-color: transparent; color: #bdc3c7; border: none;
                text-align: left; padding: 10px 16px; font-size: 14px;
                border-radius: 6px; margin: 2px 0;
            }
            QPushButton#navButton:hover {
                background-color: #34495e; color: #ecf0f1;
            }
            QPushButton#navButton:checked {
                background-color: #3498db; color: #ffffff;
            }
            #contentPanel { background-color: #ffffff; }
            #statusLabel { font-size: 13px; color: #666; padding: 4px 0; }
        """)
