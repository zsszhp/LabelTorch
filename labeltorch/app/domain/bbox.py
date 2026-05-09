"""BBox: shared bounding box data class used by services and UI"""

from PySide6.QtCore import QRectF, QPointF


# Default colors for class IDs
CLASS_COLORS = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
    "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4",
    "#469990", "#dcbeff", "#9A6324", "#800000", "#aaffc3",
    "#808000", "#ffd8b1", "#000075", "#a9a9a9", "#000000",
]


class BBox:
    """Bounding box in normalized YOLO format"""

    def __init__(self, class_id: int, x_center: float, y_center: float,
                 width: float, height: float, confidence: float = 1.0):
        self.class_id = class_id
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
        self.confidence = confidence
        self.selected = False

    def to_rect(self, img_w: int, img_h: int) -> QRectF:
        """Convert normalized coords to pixel QRectF"""
        cx = self.x_center * img_w
        cy = self.y_center * img_h
        w = self.width * img_w
        h = self.height * img_h
        return QRectF(cx - w / 2, cy - h / 2, w, h)

    @staticmethod
    def from_rect(rect: QRectF, class_id: int, img_w: int, img_h: int,
                  confidence: float = 1.0) -> "BBox":
        """Create BBox from pixel QRectF"""
        cx = (rect.x() + rect.width() / 2) / img_w
        cy = (rect.y() + rect.height() / 2) / img_h
        w = rect.width() / img_w
        h = rect.height() / img_h
        return BBox(class_id, cx, cy, w, h, confidence)

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "x_center": self.x_center,
            "y_center": self.y_center,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
        }

    def get_color(self):
        from PySide6.QtGui import QColor
        return QColor(CLASS_COLORS[self.class_id % len(CLASS_COLORS)])

    def get_handle_points(self, img_w: int, img_h: int) -> list:
        """Return 8 resize handle positions in pixel coords"""
        r = self.to_rect(img_w, img_h)
        return [
            QPointF(r.left(), r.top()),       # TL
            QPointF(r.center().x(), r.top()),  # TC
            QPointF(r.right(), r.top()),       # TR
            QPointF(r.right(), r.center().y()),  # MR
            QPointF(r.right(), r.bottom()),    # BR
            QPointF(r.center().x(), r.bottom()),  # BC
            QPointF(r.left(), r.bottom()),     # BL
            QPointF(r.left(), r.center().y()),  # ML
        ]
