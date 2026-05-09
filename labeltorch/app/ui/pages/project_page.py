"""项目管理页面"""

import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QDialog, QFormLayout,
    QLineEdit, QFileDialog, QMessageBox, QLabel, QGroupBox,
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class ProjectPage(QWidget):
    """项目管理页面"""

    def __init__(self):
        super().__init__()
        self._project_service = None
        self._main_window = None
        self._setup_ui()

    def _setup_ui(self):
        """构建UI"""
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("项目管理")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 16px;")
        layout.addWidget(title)

        # 操作按钮区
        btn_layout = QHBoxLayout()
        self.btn_new = QPushButton("新建项目")
        self.btn_new.setStyleSheet(
            "QPushButton { background-color: #3498db; color: white; padding: 10px 24px; "
            "border-radius: 6px; font-size: 14px; }"
            "QPushButton:hover { background-color: #2980b9; }"
        )
        self.btn_new.clicked.connect(self._on_new_project)
        btn_layout.addWidget(self.btn_new)

        self.btn_open = QPushButton("打开项目")
        self.btn_open.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; padding: 10px 24px; "
            "border-radius: 6px; font-size: 14px; }"
            "QPushButton:hover { background-color: #219a52; }"
        )
        self.btn_open.clicked.connect(self._on_open_project)
        btn_layout.addWidget(self.btn_open)

        self.btn_delete = QPushButton("删除项目")
        self.btn_delete.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; padding: 10px 24px; "
            "border-radius: 6px; font-size: 14px; }"
            "QPushButton:hover { background-color: #c0392b; }"
        )
        self.btn_delete.clicked.connect(self._on_delete_project)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 项目列表
        group = QGroupBox("项目列表")
        group.setStyleSheet(
            "QGroupBox { font-size: 14px; font-weight: bold; border: 1px solid #ddd; "
            "border-radius: 6px; margin-top: 12px; padding-top: 16px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }"
        )
        group_layout = QVBoxLayout(group)
        self.project_list = QListWidget()
        self.project_list.setStyleSheet(
            "QListWidget { border: none; font-size: 13px; }"
            "QListWidget::item { padding: 10px; border-bottom: 1px solid #eee; }"
            "QListWidget::item:selected { background-color: #e8f4fd; color: #2c3e50; }"
        )
        self.project_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        group_layout.addWidget(self.project_list)
        layout.addWidget(group)

        # 项目详情区
        self.detail_label = QLabel("请选择或创建项目")
        self.detail_label.setStyleSheet("color: #7f8c8d; font-size: 13px; margin-top: 8px;")
        layout.addWidget(self.detail_label)

        layout.addStretch()

    def set_services(self, project_service, main_window):
        """注入服务依赖"""
        self._project_service = project_service
        self._main_window = main_window
        self._refresh_list()

    def on_project_changed(self, project: dict):
        """项目变更回调"""
        if project:
            self.detail_label.setText(
                f"当前项目: {project['name']}  路径: {project['root_path']}"
            )

    def _refresh_list(self):
        """刷新项目列表"""
        self.project_list.clear()
        if not self._project_service:
            return
        projects = self._project_service.list_projects()
        for p in projects:
            item = QListWidgetItem(f"{p['name']}  ({p['root_path']})")
            item.setData(Qt.UserRole, p)
            self.project_list.addItem(item)

    def _on_new_project(self):
        """新建项目"""
        dialog = _NewProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name = dialog.name_edit.text().strip()
            path = dialog.path_edit.text().strip()
            if not name or not path:
                QMessageBox.warning(self, "提示", "项目名称和路径不能为空")
                return
            try:
                project = self._project_service.create_project(name, path)
                self._refresh_list()
                QMessageBox.information(self, "成功", f"项目 '{name}' 创建成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建项目失败: {e}")
                logger.error("创建项目失败: %s", e)

    def _on_open_project(self):
        """打开选中项目"""
        item = self.project_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个项目")
            return
        project = item.data(Qt.UserRole)
        if self._main_window:
            self._main_window.set_current_project(project)
        self.detail_label.setText(
            f"当前项目: {project['name']}  路径: {project['root_path']}"
        )

    def _on_delete_project(self):
        """删除选中项目"""
        item = self.project_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个项目")
            return
        project = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除项目 '{project['name']}' 吗？（仅删除元数据，不删除文件）",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._project_service.delete_project(project["id"])
            self._refresh_list()
            self.detail_label.setText("请选择或创建项目")

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """双击打开项目"""
        project = item.data(Qt.UserRole)
        if self._main_window:
            self._main_window.set_current_project(project)
        self.detail_label.setText(
            f"当前项目: {project['name']}  路径: {project['root_path']}"
        )


class _NewProjectDialog(QDialog):
    """新建项目对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("输入项目名称")
        layout.addRow("项目名称:", self.name_edit)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择项目存储路径")
        path_layout.addWidget(self.path_edit)
        btn_browse = QPushButton("浏览...")
        btn_browse.clicked.connect(self._browse_path)
        path_layout.addWidget(btn_browse)
        layout.addRow("项目路径:", path_layout)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("创建")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)

    def _browse_path(self):
        """浏览选择目录"""
        path = QFileDialog.getExistingDirectory(self, "选择项目目录")
        if path:
            self.path_edit.setText(path)
