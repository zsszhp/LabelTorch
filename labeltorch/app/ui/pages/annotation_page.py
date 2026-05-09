"""标注编辑页面：图片浏览、框编辑、类别切换"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QToolBar, QScrollArea, QMessageBox,
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class AnnotationPage(QWidget):
    """标注编辑页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app_context = None
        self._current_project = None
        self._setup_ui()

    def set_app_context(self, ctx):
        self._app_context = ctx

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("标注编辑")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # 工具栏
        toolbar = QHBoxLayout()
        for text, action in [("上一张", "prev"), ("下一张", "next"),
                             ("放大", "zoom_in"), ("缩小", "zoom_out"),
                             ("适应窗口", "fit"), ("添加框", "add_box"),
                             ("删除框", "del_box"), ("保存", "save")]:
            btn = QPushButton(text)
            btn.setMinimumHeight(32)
            toolbar.addWidget(btn)
        layout.addLayout(toolbar)

        # 画布占位
        canvas_label = QLabel("标注画布区域\n（M2阶段实现bbox编辑器）")
        canvas_label.setAlignment(Qt.AlignCenter)
        canvas_label.setMinimumHeight(500)
        canvas_label.setStyleSheet(
            "background-color: #ecf0f1; border: 2px dashed #bdc3c7; "
            "font-size: 18px; color: #7f8c8d; border-radius: 8px;"
        )
        layout.addWidget(canvas_label, 1)

        # 状态栏
        status = QLabel("就绪")
        status.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(status)

    def on_project_changed(self, project):
        self._current_project = project
