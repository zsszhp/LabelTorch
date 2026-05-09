"""标炬领域数据模型定义"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from labeltorch.app.domain.enums import (
    AnnotationSource,
    ExportFormat,
    ExportStatus,
    ModelFamily,
    SampleStatus,
    TrainJobStatus,
)


@dataclass
class Project:
    """项目"""
    id: str
    name: str
    root_path: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Dataset:
    """数据集"""
    id: str
    project_id: str
    name: str
    image_dir: str
    label_dir: str
    format: str = "yolo_txt"
    sample_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DatasetSample:
    """数据集样本"""
    id: str
    dataset_id: str
    image_path: str
    label_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    status: SampleStatus = SampleStatus.VALID


@dataclass
class ClassMapping:
    """类别映射"""
    id: str
    dataset_id: str
    original_id: int
    mapped_id: int
    class_name: str


@dataclass
class TrainConfig:
    """训练配置（快照不可变）"""
    model_family: ModelFamily
    img_size: int = 640
    batch: int = 16
    epochs: int = 100
    patience: int = 50
    device: str = "cuda:0"
    workers: int = 8
    pretrained_weights: Optional[str] = None

    def validate(self) -> list[str]:
        """校验配置合法性，返回错误列表"""
        errors = []
        if self.img_size < 32 or self.img_size % 32 != 0:
            errors.append(f"img_size={self.img_size} 必须为32的倍数且>=32")
        if self.batch < 1:
            errors.append(f"batch={self.batch} 必须>=1")
        if self.epochs < 1:
            errors.append(f"epochs={self.epochs} 必须>=1")
        if self.patience < 1:
            errors.append(f"patience={self.patience} 必须>=1")
        if self.workers < 0:
            errors.append(f"workers={self.workers} 必须>=0")
        return errors


@dataclass
class TrainJob:
    """训练任务"""
    id: str
    project_id: str
    dataset_id: str
    model_family: str
    config_json: str
    status: TrainJobStatus = TrainJobStatus.PENDING
    metrics_json: Optional[str] = None
    log_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


@dataclass
class ModelVersion:
    """模型版本"""
    id: str
    project_id: str
    job_id: str
    parent_version_id: Optional[str] = None
    best_pt_path: Optional[str] = None
    metrics_json: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AnnotationChange:
    """标注变更记录"""
    id: str
    sample_id: str
    action: str
    boxes_json: str
    source: AnnotationSource = AnnotationSource.MANUAL
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExportTask:
    """导出任务"""
    id: str
    version_id: str
    format: ExportFormat
    options_json: Optional[str] = None
    status: ExportStatus = ExportStatus.PENDING
    output_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: Optional[str] = None
