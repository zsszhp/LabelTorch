"""Annotation page: image browsing, bbox editing, class switching, save"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QListWidget, QListWidgetItem,
    QSplitter,
)
from PySide6.QtCore import Qt

from labeltorch.app.ui.widgets.image_canvas import ImageCanvas, BBoxItem

logger = logging.getLogger(__name__)


class AnnotationPage(QWidget):
    """Annotation editing page with ImageCanvas"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._app_context = None
        self._current_project = None
        self._samples = []
        self._current_idx = -1
        self._current_dataset_id = None
        self._setup_ui()

    def set_app_context(self, ctx):
        self._app_context = ctx

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 4, 8, 4)

        self.btn_prev = QPushButton("< Prev")
        self.btn_prev.clicked.connect(self._go_prev)
        toolbar.addWidget(self.btn_prev)

        self.btn_next = QPushButton("Next >")
        self.btn_next.clicked.connect(self._go_next)
        toolbar.addWidget(self.btn_next)

        self.lbl_index = QLabel("0 / 0")
        self.lbl_index.setStyleSheet("padding: 0 12px; color: #666;")
        toolbar.addWidget(self.lbl_index)

        toolbar.addStretch()

        self.btn_draw = QPushButton("Draw Box")
        self.btn_draw.setCheckable(True)
        self.btn_draw.toggled.connect(self._toggle_draw_mode)
        self.btn_draw.setStyleSheet("padding: 4px 12px;")
        toolbar.addWidget(self.btn_draw)

        self.btn_select = QPushButton("Select")
        self.btn_select.setCheckable(True)
        self.btn_select.setChecked(True)
        self.btn_select.toggled.connect(self._toggle_select_mode)
        self.btn_select.setStyleSheet("padding: 4px 12px;")
        toolbar.addWidget(self.btn_select)

        self.btn_delete = QPushButton("Delete Box")
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_delete.setStyleSheet("padding: 4px 12px; background-color: #e74c3c; color: white; border-radius: 3px;")
        toolbar.addWidget(self.btn_delete)

        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self._save_current)
        self.btn_save.setStyleSheet("padding: 4px 12px; background-color: #27ae60; color: white; border-radius: 3px;")
        toolbar.addWidget(self.btn_save)

        self.btn_fit = QPushButton("Fit")
        self.btn_fit.clicked.connect(lambda: self.canvas.fit_to_view())
        self.btn_fit.setStyleSheet("padding: 4px 8px;")
        toolbar.addWidget(self.btn_fit)

        layout.addLayout(toolbar)

        # Main content: canvas + side panel
        splitter = QSplitter(Qt.Horizontal)

        # Image canvas
        self.canvas = ImageCanvas()
        self.canvas.boxes_changed.connect(self._on_boxes_changed)
        self.canvas.box_selected.connect(self._on_box_selected)
        self.canvas.sample_navigate.connect(self._on_navigate)
        splitter.addWidget(self.canvas)

        # Side panel
        side = QWidget()
        side.setFixedWidth(220)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(8, 8, 8, 8)

        side_layout.addWidget(QLabel("Class:"))
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self._on_class_changed)
        side_layout.addWidget(self.class_combo)

        side_layout.addWidget(QLabel("Boxes:"))
        self.box_list = QListWidget()
        side_layout.addWidget(self.box_list)

        side_layout.addStretch()

        # Status
        self.status_label = QLabel("No dataset loaded")
        self.status_label.setStyleSheet("color: #999; font-size: 11px;")
        side_layout.addWidget(self.status_label)

        splitter.addWidget(side)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter, 1)

    def load_dataset(self, dataset_id: str):
        """Load dataset samples for annotation"""
        if not self._app_context:
            return
        self._current_dataset_id = dataset_id
        self._samples = self._app_context.dataset_service.get_samples(
            dataset_id, status="valid"
        )
        self._current_idx = -1

        # Load class names
        mappings = self._app_context.dataset_service.get_classes(dataset_id)
        class_names = {}
        for m in mappings:
            class_names[m["mapped_id"]] = m["class_name"]
        sorted_names = [class_names[k] for k in sorted(class_names.keys())]
        self.canvas.set_class_names(sorted_names)

        self.class_combo.blockSignals(True)
        self.class_combo.clear()
        self.class_combo.addItems(sorted_names)
        self.class_combo.blockSignals(False)

        if self._samples:
            self._go_to(0)
        else:
            self.lbl_index.setText("0 / 0")

    def _go_prev(self):
        if self._current_idx > 0:
            self._go_to(self._current_idx - 1)

    def _go_next(self):
        if self._current_idx < len(self._samples) - 1:
            self._go_to(self._current_idx + 1)

    def _on_navigate(self, direction: int):
        if direction < 0:
            self._go_prev()
        else:
            self._go_next()

    def _go_to(self, idx: int):
        if idx < 0 or idx >= len(self._samples):
            return
        # Save current before switching
        if self._current_idx >= 0:
            self._save_current()

        self._current_idx = idx
        sample = self._samples[idx]
        self.canvas.load_image(sample["image_path"])

        # Load existing boxes from label file
        boxes = self._app_context.annotation_service.get_sample_boxes(sample["id"])
        bbox_items = [
            BBoxItem(
                class_id=b["class_id"],
                x_center=b["x_center"],
                y_center=b["y_center"],
                width=b["width"],
                height=b["height"],
            )
            for b in boxes
        ]
        # set_boxes expects list of dicts
        self.canvas.set_boxes([b.to_dict() for b in bbox_items])
        self._update_box_list()
        self.lbl_index.setText(f"{idx + 1} / {len(self._samples)}")

        fname = sample["image_path"].replace("\\", "/").split("/")[-1]
        self.status_label.setText(f"Sample: {fname}")

    def _update_box_list(self):
        """Update box list widget from canvas boxes"""
        self.box_list.clear()
        for i, bdict in enumerate(self.canvas.get_boxes()):
            cls_name = f"Class {bdict['class_id']}"
            idx = bdict["class_id"]
            if idx < self.class_combo.count():
                cls_name = self.class_combo.itemText(idx)
            self.box_list.addItem(f"{i}: {cls_name}")

    def _toggle_draw_mode(self, checked):
        if checked:
            self.btn_select.setChecked(False)
            self.canvas.set_mode(ImageCanvas.MODE_DRAW)
        elif not self.btn_select.isChecked():
            self.canvas.set_mode(ImageCanvas.MODE_VIEW)

    def _toggle_select_mode(self, checked):
        if checked:
            self.btn_draw.setChecked(False)
            self.canvas.set_mode(ImageCanvas.MODE_SELECT)
        elif not self.btn_draw.isChecked():
            self.canvas.set_mode(ImageCanvas.MODE_VIEW)

    def _delete_selected(self):
        self.canvas.delete_selected()
        self._update_box_list()

    def _save_current(self):
        """Save current sample's boxes"""
        if not self._app_context or self._current_idx < 0:
            return
        sample = self._samples[self._current_idx]
        boxes = self.canvas.get_boxes()
        result = self._app_context.annotation_service.save_annotation_edit(
            sample["id"], boxes
        )
        if result.get("success"):
            self.status_label.setText("Saved")
        else:
            self.status_label.setText(f"Save failed: {result.get('error', '')}")

    def _on_boxes_changed(self):
        self._update_box_list()

    def _on_box_selected(self, idx: int):
        if 0 <= idx < self.box_list.count():
            self.box_list.setCurrentRow(idx)

    def _on_class_changed(self, idx: int):
        if idx >= 0:
            cls_name = self.class_combo.itemText(idx) if idx < self.class_combo.count() else ""
            self.canvas.set_selected_class(idx, cls_name)

    def on_project_changed(self, project):
        self._current_project = project
