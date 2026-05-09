"""标炬请求与响应 Schema"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProjectCreateRequest:
    """创建项目请求"""
    name: str
    root_path: str


@dataclass
class DatasetImportRequest:
    """导入数据集请求"""
    project_id: str
    image_dir: str
    label_dir: str
    format: str = "yolo_txt"


@dataclass
class DatasetImportResult:
    """导入数据集结果"""
    dataset_id: str
    total_samples: int = 0
    valid_samples: int = 0
    invalid_samples: int = 0
    errors: list = field(default_factory=list)


@dataclass
class ValidationReport:
    """校验报告"""
    dataset_id: str
    total: int = 0
    valid: int = 0
    missing_labels: int = 0
    invalid_coords: int = 0
    details: list = field(default_factory=list)


@dataclass
class SplitResult:
    """切分结果"""
    dataset_id: str
    train_count: int = 0
    val_count: int = 0
    yaml_path: Optional[str] = None


@dataclass
class RemapRequest:
    """类别重映射请求"""
    dataset_id: str
    mapping: dict = field(default_factory=dict)  # {original_id: mapped_id}


@dataclass
class RemapResult:
    """类别重映射结果"""
    dataset_id: str
    remapped_count: int = 0
    errors: list = field(default_factory=list)


@dataclass
class TrainJobCreateRequest:
    """创建训练任务请求"""
    project_id: str
    dataset_id: str
    model_family: str = "yolov8"
    model_size: str = "n"
    img_size: int = 640
    batch: int = 16
    epochs: int = 100
    patience: int = 50
    device: str = "cpu"
    workers: int = 4
    pretrained_weights: Optional[str] = None


@dataclass
class TrainJobStatus:
    """训练任务状态"""
    job_id: str
    status: str = "pending"
    current_epoch: int = 0
    total_epochs: int = 0
    metrics: dict = field(default_factory=dict)
    log_tail: str = ""


@dataclass
class AssistedAnnotationRequest:
    """辅助标注请求"""
    project_id: str
    dataset_id: str
    version_id: str
    conf_thres: float = 0.25
    device: str = "cpu"


@dataclass
class BoxEdit:
    """框编辑操作"""
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float


@dataclass
class AssistedAnnotationBatch:
    """辅助标注批次结果"""
    batch_id: str
    dataset_id: str
    total_images: int = 0
    total_boxes: int = 0
    filtered_boxes: int = 0


@dataclass
class BulkConfirmResult:
    """批量确认结果"""
    confirmed_count: int = 0
    errors: list = field(default_factory=list)


@dataclass
class ExportRequest:
    """导出请求"""
    version_id: str
    format: str = "pt"
    # ONNX 参数
    opset: int = 13
    dynamic: bool = True
    simplify: bool = True
