"""训练任务页面：配置、启动、监控、早停"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QFormLayout, QComboBox,
    QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit,
    QProgressBar, QMessageBox,
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class TrainPage(QWidget):
    """训练任务页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app_context = None
        self._current_project = None
        self._setup_ui()

    def set_app_context(self, ctx):
        self._app_context = ctx

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("训练任务")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        # 训练配置区域
        config_group = QGroupBox("训练配置")
        config_layout = QFormLayout()

        self.model_family_combo = QComboBox()
        self.model_family_combo.addItems(["yolov5", "yolov8", "yolov8_obb", "yolov10", "yolov11"])
        config_layout.addRow("模型族:", self.model_family_combo)

        self.model_size_combo = QComboBox()
        self.model_size_combo.addItems(["n", "s", "m", "l", "x"])
        config_layout.addRow("模型尺寸:", self.model_size_combo)

        self.img_size_spin = QSpinBox()
        self.img_size_spin.setRange(32, 1280)
        self.img_size_spin.setValue(640)
        self.img_size_spin.setSingleStep(32)
        config_layout.addRow("图片尺寸:", self.img_size_spin)

        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 128)
        self.batch_spin.setValue(16)
        config_layout.addRow("批大小:", self.batch_spin)

        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 10000)
        self.epochs_spin.setValue(100)
        config_layout.addRow("训练轮数:", self.epochs_spin)

        self.patience_spin = QSpinBox()
        self.patience_spin.setRange(0, 1000)
        self.patience_spin.setValue(50)
        config_layout.addRow("早停耐心:", self.patience_spin)

        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "cuda:0"])
        config_layout.addRow("设备:", self.device_combo)

        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(0, 32)
        self.workers_spin.setValue(4)
        config_layout.addRow("数据加载线程:", self.workers_spin)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 控制按钮
        ctrl_layout = QHBoxLayout()
        start_btn = QPushButton("开始训练")
        start_btn.setObjectName("primaryButton")
        start_btn.setMinimumHeight(40)
        start_btn.clicked.connect(self._start_train)
        ctrl_layout.addWidget(start_btn)

        stop_btn = QPushButton("停止训练")
        stop_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px 16px; border-radius: 4px;")
        stop_btn.clicked.connect(self._stop_train)
        ctrl_layout.addWidget(stop_btn)
        layout.addLayout(ctrl_layout)

        # 训练进度
        progress_group = QGroupBox("训练进度")
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.setMaximumHeight(200)
        self.log_panel.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        progress_layout.addWidget(self.log_panel)
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

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

    def _start_train(self):
        QMessageBox.information(self, "提示", "训练功能将在M3阶段完善")

    def _stop_train(self):
        QMessageBox.information(self, "提示", "训练功能将在M3阶段完善")

    def on_project_changed(self, project):
        self._current_project = project
