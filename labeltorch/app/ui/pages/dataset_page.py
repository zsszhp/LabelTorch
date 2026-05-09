"""数据集管理页面：导入、校验、切分、类别映射"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QDoubleSpinBox, QHeaderView, QSplitter,
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class DatasetPage(QWidget):
    """数据集管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app_context = None
        self._current_project = None
        self._setup_ui()

    def set_app_context(self, ctx):
        self._app_context = ctx

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("数据集管理")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        self.no_project_label = QLabel("请先在「项目管理」中打开一个项目")
        self.no_project_label.setAlignment(Qt.AlignCenter)
        self.no_project_label.setStyleSheet("font-size: 16px; color: #95a5a6; margin-top: 100px;")
        layout.addWidget(self.no_project_label)

        # 主内容区域（初始隐藏）
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)

        # 导入区域
        import_group = QGroupBox("导入YOLO数据集")
        import_layout = QFormLayout()

        self.dataset_name_input = QLineEdit()
        self.dataset_name_input.setPlaceholderText("输入数据集名称")
        import_layout.addRow("数据集名称:", self.dataset_name_input)

        img_layout = self._make_path_row("选择图片目录", "image_dir_input")
        import_layout.addRow("图片目录:", img_layout)

        lbl_layout = self._make_path_row("选择标签目录", "label_dir_input")
        import_layout.addRow("标签目录:", lbl_layout)

        import_btn = QPushButton("导入数据集")
        import_btn.setObjectName("primaryButton")
        import_btn.setMinimumHeight(36)
        import_btn.clicked.connect(self._import_dataset)
        import_layout.addRow(import_btn)

        import_group.setLayout(import_layout)
        content_layout.addWidget(import_group)

        # 导入报告区域
        self.report_group = QGroupBox("导入报告")
        report_layout = QVBoxLayout()
        self.report_label = QLabel("尚未导入数据集")
        report_layout.addWidget(self.report_label)
        self.report_group.setLayout(report_layout)
        content_layout.addWidget(self.report_group)

        # 类别映射区域
        self.class_group = QGroupBox("类别映射")
        class_layout = QVBoxLayout()
        self.class_table = QTableWidget()
        self.class_table.setColumnCount(3)
        self.class_table.setHorizontalHeaderLabels(["原始ID", "映射ID", "类别名称"])
        self.class_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        class_layout.addWidget(self.class_table)

        remap_btn = QPushButton("执行类别重映射")
        remap_btn.setObjectName("primaryButton")
        remap_btn.clicked.connect(self._remap_classes)
        class_layout.addWidget(remap_btn)

        self.class_group.setLayout(class_layout)
        content_layout.addWidget(self.class_group)

        # 切分区域
        split_group = QGroupBox("数据集切分")
        split_layout = QFormLayout()
        self.train_ratio_spin = QDoubleSpinBox()
        self.train_ratio_spin.setRange(0.1, 0.99)
        self.train_ratio_spin.setValue(0.8)
        self.train_ratio_spin.setSingleStep(0.05)
        split_layout.addRow("训练集比例:", self.train_ratio_spin)

        split_btn = QPushButton("执行切分")
        split_btn.setObjectName("primaryButton")
        split_btn.clicked.connect(self._split_dataset)
        split_layout.addRow(split_btn)

        split_group.setLayout(split_layout)
        content_layout.addWidget(split_group)

        layout.addWidget(self.content_widget)
        self.content_widget.hide()

        self.setStyleSheet("""
            QPushButton#primaryButton {
                background-color: #3498db; color: white; border: none;
                padding: 8px 16px; border-radius: 4px; font-size: 14px;
            }
            QPushButton#primaryButton:hover { background-color: #2980b9; }
            QGroupBox {
                font-size: 14px; font-weight: bold; border: 1px solid #bdc3c7;
                border-radius: 6px; margin-top: 12px; padding-top: 16px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)

    def _make_path_row(self, placeholder: str, attr_name: str):
        """创建路径选择行"""
        row = QHBoxLayout()
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        setattr(self, attr_name, line_edit)
        row.addWidget(line_edit)
        btn = QPushButton("浏览...")
        btn.clicked.connect(lambda: self._browse_dir(line_edit))
        row.addWidget(btn)
        return row

    def _browse_dir(self, line_edit: QLineEdit):
        path = QFileDialog.getExistingDirectory(self, "选择目录")
        if path:
            line_edit.setText(path)

    def _import_dataset(self):
        """导入数据集"""
        if not self._app_context or not self._current_project:
            return
        name = self.dataset_name_input.text().strip()
        image_dir = self.image_dir_input.text().strip()
        label_dir = self.label_dir_input.text().strip()
        if not all([name, image_dir, label_dir]):
            QMessageBox.warning(self, "提示", "请填写完整信息")
            return
        try:
            result = self._app_context.dataset_service.import_dataset(
                project_id=self._current_project["id"],
                name=name,
                image_dir=image_dir,
                label_dir=label_dir,
            )
            self.report_label.setText(
                f"总样本: {result['total_samples']} | "
                f"有效: {result['valid_samples']} | "
                f"异常: {result['invalid_samples']}"
            )
            # 刷新类别表
            self._load_class_mappings(result["dataset_id"])
            QMessageBox.information(self, "成功", "数据集导入完成！")
        except Exception as e:
            logger.error("导入数据集失败: %s", e)
            QMessageBox.critical(self, "错误", f"导入失败: {e}")

    def _load_class_mappings(self, dataset_id: str):
        """加载类别映射表"""
        rows = self._app_context.dataset_service.get_class_mappings(dataset_id)
        self.class_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.class_table.setItem(i, 0, QTableWidgetItem(str(row["original_id"])))
            self.class_table.setItem(i, 1, QTableWidgetItem(str(row["mapped_id"])))
            self.class_table.setItem(i, 2, QTableWidgetItem(row["class_name"]))
        self._current_dataset_id = dataset_id

    def _remap_classes(self):
        """执行类别重映射"""
        if not hasattr(self, '_current_dataset_id') or not self._current_dataset_id:
            QMessageBox.warning(self, "提示", "请先导入数据集")
            return
        # 从表格读取映射
        mapping = {}
        for i in range(self.class_table.rowCount()):
            orig = int(self.class_table.item(i, 0).text())
            mapped = int(self.class_table.item(i, 1).text())
            mapping[orig] = mapped
        try:
            result = self._app_context.dataset_service.remap_classes(
                self._current_dataset_id, mapping
            )
            QMessageBox.information(self, "成功", f"重映射完成，影响 {result['remapped_count']} 个样本")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重映射失败: {e}")

    def _split_dataset(self):
        """切分数据集"""
        if not hasattr(self, '_current_dataset_id') or not self._current_dataset_id:
            QMessageBox.warning(self, "提示", "请先导入数据集")
            return
        ratio = self.train_ratio_spin.value()
        try:
            result = self._app_context.dataset_service.split_dataset(
                self._current_dataset_id, ratio
            )
            QMessageBox.information(
                self, "成功",
                f"切分完成: 训练集 {result['train_count']} | 验证集 {result['val_count']}"
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"切分失败: {e}")

    def on_project_changed(self, project):
        """项目变更回调"""
        self._current_project = project
        if project:
            self.no_project_label.hide()
            self.content_widget.show()
        else:
            self.no_project_label.show()
            self.content_widget.hide()
