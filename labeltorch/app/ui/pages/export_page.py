"""模型导出页面：pt/onnx导出与参数配置"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QFormLayout, QComboBox,
    QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox,
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class ExportPage(QWidget):
    """模型导出页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app_context = None
        self._current_project = None
        self._setup_ui()

    def set_app_context(self, ctx):
        self._app_context = ctx

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("模型导出")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # 导出配置
        config_group = QGroupBox("导出配置")
        config_layout = QFormLayout()

        self.version_combo = QComboBox()
        config_layout.addRow("模型版本:", self.version_combo)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["pt", "onnx"])
        config_layout.addRow("导出格式:", self.format_combo)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # ONNX参数
        onnx_group = QGroupBox("ONNX参数")
        onnx_layout = QFormLayout()

        self.opset_spin = QSpinBox()
        self.opset_spin.setRange(7, 20)
        self.opset_spin.setValue(13)
        onnx_layout.addRow("Opset:", self.opset_spin)

        self.dynamic_check = QCheckBox("动态轴")
        self.dynamic_check.setChecked(True)
        onnx_layout.addRow(self.dynamic_check)

        self.simplify_check = QCheckBox("简化模型")
        self.simplify_check.setChecked(True)
        onnx_layout.addRow(self.simplify_check)

        onnx_group.setLayout(onnx_layout)
        layout.addWidget(onnx_group)

        # 导出按钮
        export_btn = QPushButton("开始导出")
        export_btn.setObjectName("primaryButton")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self._export)
        layout.addWidget(export_btn)

        # 导出记录
        history_group = QGroupBox("导出记录")
        history_layout = QVBoxLayout()
        self.export_table = QTableWidget(0, 4)
        self.export_table.setHorizontalHeaderLabels(["版本", "格式", "状态", "输出路径"])
        self.export_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        history_layout.addWidget(self.export_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        layout.addStretch()
        self.setStyleSheet("""
            QPushButton#primaryButton {
                background-color: #3498db; color: white; border: none;
                padding: 8px 16px; border-radius: 4px; font-size: 14px;
            }
            QPushButton#primaryButton:hover { background-color: #2980b9; }
            QGroupBox { font-size: 16px; font-weight: bold; border: 1px solid #bdc3c7;
                border-radius: 6px; margin-top: 12px; padding-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)

    def _export(self):
        QMessageBox.information(self, "提示", "导出功能将在M5阶段完善")

    def on_project_changed(self, project):
        self._current_project = project
