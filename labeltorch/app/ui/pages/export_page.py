"""Export page: model export (pt/onnx), status tracking"""

import os
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QFormLayout, QComboBox,
    QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox,
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class ExportPage(QWidget):
    """Model export page"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app_context = None
        self._current_project = None
        self._setup_ui()

    def set_app_context(self, ctx):
        self._app_context = ctx

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Export config
        config_group = QGroupBox("Export Configuration")
        config_layout = QFormLayout()

        self.version_combo = QComboBox()
        config_layout.addRow("Model Version:", self.version_combo)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["pt", "onnx"])
        config_layout.addRow("Export Format:", self.format_combo)

        # ONNX options
        self.opset_spin = QSpinBox()
        self.opset_spin.setRange(7, 20)
        self.opset_spin.setValue(13)
        config_layout.addRow("ONNX Opset:", self.opset_spin)

        self.dynamic_check = QCheckBox("Dynamic Axes")
        self.dynamic_check.setChecked(True)
        config_layout.addRow(self.dynamic_check)

        self.simplify_check = QCheckBox("Simplify")
        self.simplify_check.setChecked(True)
        config_layout.addRow(self.simplify_check)

        export_btn = QPushButton("Export")
        export_btn.setObjectName("primaryButton")
        export_btn.setMinimumHeight(36)
        export_btn.clicked.connect(self._do_export)
        config_layout.addRow(export_btn)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Export history
        history_group = QGroupBox("Export History")
        history_layout = QVBoxLayout()
        self.export_table = QTableWidget()
        self.export_table.setColumnCount(4)
        self.export_table.setHorizontalHeaderLabels(["Version", "Format", "Status", "Output Path"])
        self.export_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        history_layout.addWidget(self.export_table)

        open_dir_btn = QPushButton("Open Export Directory")
        open_dir_btn.clicked.connect(self._open_export_dir)
        history_layout.addWidget(open_dir_btn)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        layout.addStretch()
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

    def _do_export(self):
        if not self._app_context or not self._current_project:
            QMessageBox.warning(self, "Warning", "Please open a project first")
            return

        version_id = self.version_combo.currentData()
        if not version_id:
            QMessageBox.warning(self, "Warning", "Please select a model version")
            return

        fmt = self.format_combo.currentText()
        options = {}
        if fmt == "onnx":
            options = {
                "opset": self.opset_spin.value(),
                "dynamic": self.dynamic_check.isChecked(),
                "simplify": self.simplify_check.isChecked(),
            }

        result = self._app_context.export_service.create_export_task(
            version_id, fmt, options,
        )
        task_id = result["task_id"]

        success = self._app_context.export_service.run_export(
            task_id, self._current_project["root_path"],
        )
        if success:
            QMessageBox.information(self, "Success", f"Export started (format={fmt})")
        else:
            QMessageBox.critical(self, "Error", "Export failed")
        self._refresh_table()

    def _open_export_dir(self):
        if not self._current_project:
            return
        export_dir = os.path.join(self._current_project["root_path"], "exports")
        if os.path.exists(export_dir):
            os.startfile(export_dir)

    def _refresh_versions(self):
        if not self._app_context or not self._current_project:
            return
        versions = self._app_context.version_service.list_versions(self._current_project["id"])
        self.version_combo.clear()
        for v in versions:
            label = f"v{v['id'][:8]} ({v.get('created_at', '')[:10]})"
            self.version_combo.addItem(label, v["id"])

    def _refresh_table(self):
        if not self._app_context or not self._current_project:
            return
        tasks = self._app_context.export_service.list_all_exports(self._current_project["id"])
        self.export_table.setRowCount(len(tasks))
        for i, t in enumerate(tasks):
            self.export_table.setItem(i, 0, QTableWidgetItem(t.get("version_id", "")[:8]))
            self.export_table.setItem(i, 1, QTableWidgetItem(t.get("format", "")))
            self.export_table.setItem(i, 2, QTableWidgetItem(t.get("status", "")))
            self.export_table.setItem(i, 3, QTableWidgetItem(t.get("output_path", "")))

    def on_project_changed(self, project):
        self._current_project = project
        if project:
            self._refresh_versions()
            self._refresh_table()
