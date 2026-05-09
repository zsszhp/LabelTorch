"""
标炬（LabelTorch）领域枚举定义
"""
from enum import Enum


class ModelFamily(str, Enum):
    """YOLO 模型族"""
    YOLOV5 = "yolov5"
    YOLOV8 = "yolov8"
    YOLOV8_OBB = "yolov8_obb"
    YOLOV10 = "yolov10"
    YOLOV11 = "yolov11"


class TrainJobStatus(str, Enum):
    """训练任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STOPPED = "stopped"


class ExportFormat(str, Enum):
    """导出格式"""
    PT = "pt"
    ONNX = "onnx"


class ExportStatus(str, Enum):
    """导出任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AnnotationSource(str, Enum):
    """标注来源"""
    MANUAL = "manual"
    ASSISTED = "assisted"


class SampleStatus(str, Enum):
    """样本状态"""
    VALID = "valid"
    INVALID = "invalid"
    MISSING_LABEL = "missing_label"
    INVALID_COORD = "invalid_coord"
