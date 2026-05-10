"""ImageCanvas: image display with zoom/pan and bbox editing

Supports: image loading, zoom, pan, bbox drawing (drag),
box selection/move/resize, class switching, deletion.
"""

import math
import logging
from typing import Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QPoint
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPixmap, QCursor,
    QMouseEvent, QWheelEvent, QPaintEvent,
)

logger = logging.getLogger(__name__)

# Class colors for rendering
CLASS_COLORS = [
    QColor(255, 0, 0, 180),     # red
    QColor(0, 255, 0, 180),     # green
    QColor(0, 0, 255, 180),     # blue
    QColor(255, 255, 0, 180),   # yellow
    QColor(255, 0, 255, 180),   # magenta
    QColor(0, 255, 255, 180),   # cyan
    QColor(255, 128, 0, 180),   # orange
    QColor(128, 0, 255, 180),   # purple
]

HANDLE_SIZE = 6  # resize handle size in pixels


class BBoxItem:
    """A bounding box with class info for display/editing"""

    def __init__(self, class_id: int, x_center: float, y_center: float,
                 width: float, height: float, class_name: str = ""):
        self.class_id = class_id
        self.class_name = class_name or f"class_{class_id}"
        # YOLO normalized coords [0,1]
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
        self.selected = False

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "x_center": self.x_center,
            "y_center": self.y_center,
            "width": self.width,
            "height": self.height,
        }

    def get_rect_normalized(self) -> QRectF:
        """Get QRectF in normalized coords (top-left origin)"""
        x = self.x_center - self.width / 2
        y = self.y_center - self.height / 2
        return QRectF(x, y, self.width, self.height)

    def color(self) -> QColor:
        return CLASS_COLORS[self.class_id % len(CLASS_COLORS)]


class ImageCanvas(QWidget):
    """Image canvas with bbox drawing and editing"""

    boxes_changed = Signal()           # boxes modified
    box_selected = Signal(int)         # box index selected (-1 for none)
    sample_navigate = Signal(int)      # navigate: -1 prev, +1 next

    MODE_VIEW = 0
    MODE_DRAW = 1
    MODE_SELECT = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: Optional[QPixmap] = None
        self._image_path: Optional[str] = None
        self._boxes: list[BBoxItem] = []
        self._selected_idx: int = -1

        # View transform
        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0

        # Interaction state
        self._mode = self.MODE_VIEW
        self._drag_start: Optional[QPointF] = None
        self._drawing_box: Optional[BBoxItem] = None
        self._moving = False
        self._move_start: Optional[QPointF] = None
        self._resizing_handle: int = -1  # 0-7 for 8 handles
        self._resize_start_box: Optional[dict] = None
        self._panning = False
        self._pan_start: Optional[QPoint] = None

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(400, 300)
        self._class_names: list[str] = []
        self._draw_class_id: int = 0

    # --- Image loading ---

    def load_image(self, image_path: str):
        """Load image from file path"""
        self._pixmap = QPixmap(image_path)
        self._image_path = image_path
        if self._pixmap.isNull():
            logger.warning("Failed to load image: %s", image_path)
            self._pixmap = None
        self._boxes = []
        self._selected_idx = -1
        self.fit_to_view()
        self.update()

    def set_boxes(self, boxes: list):
        """Set boxes from list of dicts {class_id, x_center, y_center, width, height, class_name?}"""
        self._boxes = []
        for b in boxes:
            self._boxes.append(BBoxItem(
                class_id=b["class_id"],
                x_center=b["x_center"],
                y_center=b["y_center"],
                width=b["width"],
                height=b["height"],
                class_name=b.get("class_name", ""),
            ))
        self._selected_idx = -1
        self.update()

    def get_boxes(self) -> list:
        """Return boxes as list of dicts"""
        return [b.to_dict() for b in self._boxes]

    def clear(self):
        """Clear image and boxes"""
        self._pixmap = None
        self._image_path = None
        self._boxes = []
        self._selected_idx = -1
        self._scale = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self.update()

    # --- View transforms ---

    def fit_to_view(self):
        """Scale and center image to fit widget"""
        if not self._pixmap:
            return
        pw = self._pixmap.width()
        ph = self._pixmap.height()
        ww = self.width()
        wh = self.height()
        if pw <= 0 or ph <= 0 or ww <= 0 or wh <= 0:
            return
        self._scale = min(ww / pw, wh / ph) * 0.9
        self._offset_x = (ww - pw * self._scale) / 2
        self._offset_y = (wh - ph * self._scale) / 2
        self.update()

    def _img_to_screen(self, img_pt: QPointF) -> QPointF:
        """Convert image coordinate to screen coordinate"""
        return QPointF(
            img_pt.x() * self._scale + self._offset_x,
            img_pt.y() * self._scale + self._offset_y,
        )

    def _screen_to_img(self, screen_pt: QPointF) -> QPointF:
        """Convert screen coordinate to image coordinate"""
        return QPointF(
            (screen_pt.x() - self._offset_x) / self._scale,
            (screen_pt.y() - self._offset_y) / self._scale,
        )

    def _norm_to_screen(self, norm_rect: QRectF) -> QRectF:
        """Convert normalized [0,1] rect to screen rect"""
        if not self._pixmap:
            return QRectF()
        pw = self._pixmap.width()
        ph = self._pixmap.height()
        img_rect = QRectF(
            norm_rect.x() * pw, norm_rect.y() * ph,
            norm_rect.width() * pw, norm_rect.height() * ph,
        )
        tl = self._img_to_screen(img_rect.topLeft())
        br = self._img_to_screen(img_rect.bottomRight())
        return QRectF(tl, br)

    def _screen_to_norm(self, screen_pt: QPointF) -> QPointF:
        """Convert screen point to normalized [0,1] coordinate"""
        if not self._pixmap:
            return QPointF()
        img_pt = self._screen_to_img(screen_pt)
        return QPointF(
            img_pt.x() / self._pixmap.width(),
            img_pt.y() / self._pixmap.height(),
        )

    # --- Mode ---

    def set_mode(self, mode: int):
        self._mode = mode
        if mode == self.MODE_DRAW:
            self.setCursor(Qt.CrossCursor)
        elif mode == self.MODE_SELECT:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    # --- Resize handles ---

    def _get_handles(self, box: BBoxItem) -> list[QPointF]:
        """Get 8 resize handle positions in screen coords"""
        rect = self._norm_to_screen(box.get_rect_normalized())
        cx, cy = rect.center().x(), rect.center().y()
        tl, tr, bl, br = rect.topLeft(), rect.topRight(), rect.bottomLeft(), rect.bottomRight()
        tm = QPointF(cx, rect.top())
        bm = QPointF(cx, rect.bottom())
        ml = QPointF(rect.left(), cy)
        mr = QPointF(rect.right(), cy)
        return [tl, tm, tr, mr, br, bm, bl, ml]

    def _hit_handle(self, screen_pt: QPointF) -> int:
        """Check if screen point hits a resize handle of selected box"""
        if self._selected_idx < 0 or self._selected_idx >= len(self._boxes):
            return -1
        handles = self._get_handles(self._boxes[self._selected_idx])
        for i, h in enumerate(handles):
            if (QPointF(screen_pt) - h).manhattanLength() < HANDLE_SIZE + 2:
                return i
        return -1

    def _hit_box(self, screen_pt: QPointF) -> int:
        """Check if screen point hits any box, return index"""
        norm_pt = self._screen_to_norm(screen_pt)
        # Check in reverse order (top boxes first)
        for i in range(len(self._boxes) - 1, -1, -1):
            rect = self._boxes[i].get_rect_normalized()
            if rect.contains(norm_pt):
                return i
        return -1

    # --- Mouse events ---

    def mousePressEvent(self, event: QMouseEvent):
        pos = QPointF(event.position())

        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = pos.toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            return

        if event.button() == Qt.RightButton:
            # Navigate: right-click = next
            self.sample_navigate.emit(1)
            return

        if event.button() != Qt.LeftButton:
            return

        if self._mode == self.MODE_DRAW and self._pixmap:
            # Start drawing a new box
            norm_pt = self._screen_to_norm(pos)
            self._drag_start = norm_pt
            cls_name = self._class_names[self._draw_class_id] if self._draw_class_id < len(self._class_names) else f"class_{self._draw_class_id}"
            self._drawing_box = BBoxItem(self._draw_class_id, norm_pt.x(), norm_pt.y(), 0, 0, cls_name)
            return

        if self._mode == self.MODE_SELECT:
            # Check resize handle first
            handle = self._hit_handle(pos)
            if handle >= 0:
                self._resizing_handle = handle
                self._resize_start_box = self._boxes[self._selected_idx].to_dict()
                self._move_start = pos
                return

            # Check box hit
            idx = self._hit_box(pos)
            self._select_box(idx)

            if idx >= 0:
                self._moving = True
                self._move_start = pos
            return

        # View mode: pan
        if event.button() == Qt.LeftButton:
            self._panning = True
            self._pan_start = pos.toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = QPointF(event.position())

        if self._panning and self._pan_start is not None:
            delta = pos.toPoint() - self._pan_start
            self._offset_x += delta.x()
            self._offset_y += delta.y()
            self._pan_start = pos.toPoint()
            self.update()
            return

        if self._mode == self.MODE_DRAW and self._drag_start is not None:
            norm_pt = self._screen_to_norm(pos)
            x1, y1 = self._drag_start.x(), self._drag_start.y()
            x2, y2 = norm_pt.x(), norm_pt.y()
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            self._drawing_box = BBoxItem(self._draw_class_id, cx, cy, w, h)
            self.update()
            return

        if self._mode == self.MODE_SELECT and self._moving and self._move_start and self._selected_idx >= 0:
            box = self._boxes[self._selected_idx]
            delta_screen = pos - self._move_start
            if self._pixmap:
                dx_norm = delta_screen.x() / (self._pixmap.width() * self._scale)
                dy_norm = delta_screen.y() / (self._pixmap.height() * self._scale)
                box.x_center += dx_norm
                box.y_center += dy_norm
                self._move_start = pos
                self.update()
            return

        if self._mode == self.MODE_SELECT and self._resizing_handle >= 0 and self._selected_idx >= 0:
            self._do_resize(pos)
            return

        # Update cursor based on hover
        if self._mode == self.MODE_SELECT:
            handle = self._hit_handle(pos)
            if handle >= 0:
                cursors = [Qt.SizeFDiagCursor, Qt.SizeVerCursor, Qt.SizeBDiagCursor,
                           Qt.SizeHorCursor, Qt.SizeFDiagCursor, Qt.SizeVerCursor,
                           Qt.SizeBDiagCursor, Qt.SizeHorCursor]
                self.setCursor(cursors[handle])
            elif self._hit_box(pos) >= 0:
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor if self._mode == self.MODE_VIEW else Qt.CrossCursor)
            return

        if event.button() != Qt.LeftButton:
            return

        if self._mode == self.MODE_DRAW and self._drawing_box:
            box = self._drawing_box
            if box.width > 0.005 and box.height > 0.005:  # minimum size
                self._boxes.append(box)
                self._selected_idx = len(self._boxes) - 1
                self.boxes_changed.emit()
            self._drawing_box = None
            self._drag_start = None
            self.update()
            return

        if self._mode == self.MODE_SELECT:
            if self._moving:
                self._moving = False
                self._move_start = None
                self.boxes_changed.emit()
            if self._resizing_handle >= 0:
                self._resizing_handle = -1
                self._resize_start_box = None
                self.boxes_changed.emit()
            return

        if self._panning:
            self._panning = False
            self._pan_start = None

    def wheelEvent(self, event: QWheelEvent):
        """Zoom with mouse wheel"""
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 1 / 1.1
        # Zoom towards cursor position
        pos = QPointF(event.position())
        old_pos = self._screen_to_img(pos)
        self._scale *= factor
        self._scale = max(0.05, min(self._scale, 50.0))
        # Adjust offset to keep cursor point stable
        new_screen = self._img_to_screen(old_pos)
        self._offset_x += pos.x() - new_screen.x()
        self._offset_y += pos.y() - new_screen.y()
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Delete and self._selected_idx >= 0:
            self.delete_selected()
        elif key == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            self.set_mode(self.MODE_DRAW)
        elif key == Qt.Key_S and event.modifiers() & Qt.ControlModifier:
            self.set_mode(self.MODE_SELECT)
        elif key == Qt.Key_V:
            self.set_mode(self.MODE_VIEW)
        elif key == Qt.Key_Left or key == Qt.Key_PageUp:
            self.sample_navigate.emit(-1)
        elif key == Qt.Key_Right or key == Qt.Key_PageDown:
            self.sample_navigate.emit(1)
        else:
            super().keyPressEvent(event)

    # --- Box operations ---

    def _select_box(self, idx: int):
        for b in self._boxes:
            b.selected = False
        self._selected_idx = idx
        if 0 <= idx < len(self._boxes):
            self._boxes[idx].selected = True
        self.box_selected.emit(idx)
        self.update()

    def delete_selected(self):
        if 0 <= self._selected_idx < len(self._boxes):
            self._boxes.pop(self._selected_idx)
            self._selected_idx = -1
            self.boxes_changed.emit()
            self.update()

    def set_selected_class(self, class_id: int, class_name: str = ""):
        if 0 <= self._selected_idx < len(self._boxes):
            self._boxes[self._selected_idx].class_id = class_id
            self._boxes[self._selected_idx].class_name = class_name or f"class_{class_id}"
            self.boxes_changed.emit()
            self.update()

    def set_class_names(self, names: list):
        """Set class name list for display"""
        self._class_names = names

    def set_draw_class(self, class_id: int):
        """Set class ID for new box drawing"""
        self._draw_class_id = class_id

    def _do_resize(self, screen_pos: QPointF):
        """Handle resize by dragging a handle"""
        if self._selected_idx < 0 or not self._resize_start_box:
            return
        box = self._boxes[self._selected_idx]
        orig = self._resize_start_box
        norm_pos = self._screen_to_norm(screen_pos)

        # Get original rect (top-left origin)
        ox = orig["x_center"] - orig["width"] / 2
        oy = orig["y_center"] - orig["height"] / 2
        ow = orig["width"]
        oh = orig["height"]

        h = self._resizing_handle
        # Handle indices: 0=TL, 1=TM, 2=TR, 3=MR, 4=BR, 5=BM, 6=BL, 7=ML
        left, top, right, bottom = ox, oy, ox + ow, oy + oh

        if h in (0, 6, 7):
            left = norm_pos.x()
        if h in (2, 3, 4):
            right = norm_pos.x()
        if h in (0, 1, 2):
            top = norm_pos.y()
        if h in (4, 5, 6):
            bottom = norm_pos.y()

        # Ensure minimum size
        if right - left < 0.005:
            right = left + 0.005
        if bottom - top < 0.005:
            bottom = top + 0.005

        box.x_center = (left + right) / 2
        box.y_center = (top + bottom) / 2
        box.width = right - left
        box.height = bottom - top
        self.update()

    # --- Paint ---

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(45, 45, 48))

        if not self._pixmap or self._pixmap.isNull():
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignCenter, "No image loaded")
            painter.end()
            return

        # Draw image
        target_rect = QRectF(
            self._offset_x, self._offset_y,
            self._pixmap.width() * self._scale,
            self._pixmap.height() * self._scale,
        )
        painter.drawPixmap(target_rect, self._pixmap, QRectF(self._pixmap.rect()))

        # Draw boxes
        for i, box in enumerate(self._boxes):
            self._draw_box(painter, box, selected=(i == self._selected_idx))

        # Draw currently drawing box
        if self._drawing_box:
            self._draw_box(painter, self._drawing_box, selected=True, dashed=True)

        painter.end()

    def _draw_box(self, painter: QPainter, box: BBoxItem,
                  selected: bool = False, dashed: bool = False):
        rect = self._norm_to_screen(box.get_rect_normalized())
        if rect.width() < 1 or rect.height() < 1:
            return

        color = box.color()

        # Pen
        pen = QPen(color)
        pen.setWidth(2 if selected else 1)
        if dashed:
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        # Fill (semi-transparent)
        fill_color = QColor(color)
        fill_color.setAlpha(30 if not selected else 60)
        painter.setBrush(QBrush(fill_color))

        painter.drawRect(rect)

        # Label
        label = f"{box.class_name}"
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        text_rect = QRectF(rect.topLeft().x(), rect.topLeft().y() - 16,
                           rect.width(), 16)
        bg_color = QColor(color)
        bg_color.setAlpha(200)
        painter.fillRect(text_rect, bg_color)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, label)

        # Resize handles for selected box
        if selected:
            handles = self._get_handles(box)
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setBrush(QBrush(QColor(0, 120, 215)))
            for h in handles:
                painter.drawRect(QRectF(
                    h.x() - HANDLE_SIZE / 2, h.y() - HANDLE_SIZE / 2,
                    HANDLE_SIZE, HANDLE_SIZE,
                ))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pixmap:
            self.fit_to_view()
