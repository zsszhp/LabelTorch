"""Train page: configure, start, monitor, stop training"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QFormLayout, QComboBox,
    QSpinBox, QTextEdit, QProgressBar, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt

from labeltorch.app.services.training_service import TrainConfig

logger = logging.getLogger(__name__)


class TrainPage(QWidget):
    """Training task page"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app_context = None
        self._current_project = None
        self._current_dataset_id = None
        self._current_job_id = None
        self._setup_ui()

    def set_app_context(self, ctx):
        self._app_context = ctx

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Training config
        config_group = QGroupBox("Training Configuration")
        config_layout = QFormLayout()

        self.model_family_combo = QComboBox()
        self.model_family_combo.addItems(["yolov5", "yolov8", "yolov8_obb", "yolov10", "yolov11"])
        config_layout.addRow("Model Family:", self.model_family_combo)

        self.model_size_combo = QComboBox()
        self.model_size_combo.addItems(["n", "s", "m", "l", "x"])
        config_layout.addRow("Model Size:", self.model_size_combo)

        self.img_size_spin = QSpinBox()
        self.img_size_spin.setRange(32, 2048)
        self.img_size_spin.setValue(640)
        self.img_size_spin.setSingleStep(32)
        config_layout.addRow("Image Size:", self.img_size_spin)

        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 256)
        self.batch_spin.setValue(16)
        config_layout.addRow("Batch Size:", self.batch_spin)

        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 10000)
        self.epochs_spin.setValue(100)
        config_layout.addRow("Epochs:", self.epochs_spin)

        self.patience_spin = QSpinBox()
        self.patience_spin.setRange(0, 500)
        self.patience_spin.setValue(50)
        config_layout.addRow("Patience:", self.patience_spin)

        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "cuda:0", "cuda:1"])
        config_layout.addRow("Device:", self.device_combo)

        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(0, 32)
        self.workers_spin.setValue(4)
        config_layout.addRow("Workers:", self.workers_spin)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Control buttons
        ctrl_layout = QHBoxLayout()
        start_btn = QPushButton("Start Training")
        start_btn.setObjectName("primaryButton")
        start_btn.setMinimumHeight(40)
        start_btn.clicked.connect(self._start_train)
        ctrl_layout.addWidget(start_btn)

        stop_btn = QPushButton("Stop")
        stop_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px 16px; border-radius: 4px;")
        stop_btn.clicked.connect(self._stop_train)
        ctrl_layout.addWidget(stop_btn)
        layout.addLayout(ctrl_layout)

        # Progress
        progress_group = QGroupBox("Training Progress")
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

        # Job history
        history_group = QGroupBox("Training History")
        history_layout = QVBoxLayout()
        self.job_table = QTableWidget()
        self.job_table.setColumnCount(4)
        self.job_table.setHorizontalHeaderLabels(["Model", "Status", "Created", "Finished"])
        self.job_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        history_layout.addWidget(self.job_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        self.setStyleSheet("""
            QPushButton#primaryButton {
                background-color: #3498db; color: white; border: none;
                padding: 8px 16px; border-radius: 4px; font-size: 14px;
            }
            QPushButton#primaryButton:hover { background-color: #2980b9; }
            QGroupBox { font-size: 14px; font-weight: bold; border: 1px solid #bdc3c7;
                border-radius: 6px; margin-top: 12px; padding-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        """)

    def _start_train(self):
        if not self._app_context or not self._current_project:
            QMessageBox.warning(self, "Warning", "Please open a project first")
            return
        if not self._current_dataset_id:
            QMessageBox.warning(self, "Warning", "Please import and split a dataset first")
            return

        config = TrainConfig(
            model_family=self.model_family_combo.currentText(),
            model_size=self.model_size_combo.currentText(),
            img_size=self.img_size_spin.value(),
            batch=self.batch_spin.value(),
            epochs=self.epochs_spin.value(),
            patience=self.patience_spin.value(),
            device=self.device_combo.currentText(),
            workers=self.workers_spin.value(),
        )

        result = self._app_context.training_service.create_train_job(
            self._current_project["id"], self._current_dataset_id, config,
        )
        if result["errors"]:
            QMessageBox.critical(self, "Error", "\n".join(result["errors"]))
            return

        job_id = result["job_id"]
        self._current_job_id = job_id

        # Get data.yaml from split
        dataset = self._app_context.dataset_service.get_dataset(self._current_dataset_id)
        split_result = self._app_context.dataset_service.split_dataset(self._current_dataset_id)

        if not split_result.get("yaml_path"):
            QMessageBox.warning(self, "Warning", "Please split the dataset first")
            return

        self.log_panel.clear()
        self.log_panel.append(f"Starting training job {job_id[:8]}...")
        self.progress_bar.setValue(0)

        success = self._app_context.training_service.start_train_job(
            job_id,
            split_result["yaml_path"],
            self._current_project["root_path"],
            log_callback=self._on_log_line,
        )
        if success:
            self.log_panel.append("Training started.")
        else:
            self.log_panel.append("Failed to start training.")
        self._refresh_job_table()

    def _stop_train(self):
        if self._current_job_id and self._app_context:
            self._app_context.training_service.stop_train_job(self._current_job_id)
            self.log_panel.append("Training stopped.")
            self._refresh_job_table()

    def _on_log_line(self, line: str):
        self.log_panel.append(line)
        # Try to extract epoch progress
        if "epoch" in line.lower():
            try:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p.startswith("epoch") and i + 1 < len(parts):
                        epoch_info = parts[i + 1]
                        if "/" in epoch_info:
                            current, total = epoch_info.split("/")
                            pct = int(int(current) / int(total) * 100)
                            self.progress_bar.setValue(pct)
            except Exception:
                pass

    def _refresh_job_table(self):
        if not self._app_context or not self._current_project:
            return
        jobs = self._app_context.training_service.list_jobs(self._current_project["id"])
        self.job_table.setRowCount(len(jobs))
        for i, job in enumerate(jobs):
            config = TrainConfig.from_json(job["config_json"])
            self.job_table.setItem(i, 0, QTableWidgetItem(config.get_model_name()))
            self.job_table.setItem(i, 1, QTableWidgetItem(job["status"]))
            self.job_table.setItem(i, 2, QTableWidgetItem(job.get("created_at", "")[:19]))
            self.job_table.setItem(i, 3, QTableWidgetItem(job.get("finished_at", "")[:19] if job.get("finished_at") else ""))

    def set_dataset(self, dataset_id: str):
        self._current_dataset_id = dataset_id

    def on_project_changed(self, project):
        self._current_project = project
        if project:
            self._refresh_job_table()
