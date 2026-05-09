# 标炬（LabelTorch）完整产品实施文档

## 1. 项目概述

标炬（LabelTorch）是一款面向工业缺陷检测场景的本地离线桌面软件，基于 Python + PySide6 + Ultralytics + SQLite 构建。核心目标是打通"数据导入-标注编辑-模型训练-辅助标注-增量训练-模型导出"完整闭环，显著降低 YOLO 数据准备与训练迭代的复杂度。

## 2. 需求场景与处理逻辑

### 2.1 核心用户场景

**场景A - 首次数据准备与训练**：用户导入图片+YOLO标签 → 校验数据 → 调整类别映射 → 配置训练参数 → 启动训练 → 获得模型版本 → 导出模型

**场景B - 辅助标注与增量迭代**：用户选择历史模型 → 推理生成候选框 → 阈值筛选 → 批量确认/人工修正 → 基于新数据+历史权重增量训练 → 获得新版本

**场景C - 模型部署**：用户选择版本 → 配置导出参数 → 导出 pt/onnx → 验证导出可用性

### 2.2 版本规划

| 版本 | 目标 | 核心范围 |
|------|------|----------|
| V0.1 MVP | 最小可用闭环 | 导入/标注/训练/版本/辅助标注/导出/打包 |
| V0.2 | 效率与恢复 | 断点续训/AMP/实验对比/COCO-VOC导入 |
| V0.3 | 规模化训练 | 多卡/超参搜索/OBB增强/数据健康度 |
| V0.4 | 任务扩展 | 分类/异常检测/多任务空间 |
| V0.5 | 工程治理 | 插件化/配置模板/诊断包 |
| V1.0 | 成熟发布 | 全量回归/跨版本兼容/LTS策略/性能优化 |

## 3. 架构与技术方案

### 3.1 技术栈

- **语言**: Python 3.11+
- **UI框架**: PySide6（Qt for Python）
- **训练引擎**: Ultralytics（统一 v5/v8/v8_obb/v10/v11 接口）
- **数据库**: SQLite（元数据）
- **导出**: Ultralytics 导出 + onnxruntime 验证
- **打包**: PyInstaller 构建 Windows 绿色包

### 3.2 四层架构

```
Presentation Layer (PySide6 UI)
    ↓
Application Layer (Service 编排)
    ↓
Domain Layer (实体与规则)
    ↓
Infrastructure Layer (DB/FS/ML引擎)
```

### 3.3 运行时架构

- UI 主进程 + Task Manager 调度
- 训练/推理/导出在独立子进程执行，避免 UI 阻塞
- 子进程通过 stdout/文件与主进程通信
- 异常隔离：子进程崩溃不影响主进程

### 3.4 参考项目借鉴策略

| 参考项目 | 借鉴要点 |
|----------|----------|
| X-AnyLabeling | 标注交互设计（画框/选类/快捷键）、PySide6 工程结构 |
| Labelme | 图片浏览与标注编辑的 UI 交互模式 |
| Ultralytics | 训练 API 调用方式、参数映射、日志解析 |

## 4. 文件结构与模块设计

### 4.1 源码结构

```
labeltorch/
  app/
    ui/
      __init__.py
      main_window.py          # 主窗口与导航
      pages/
        __init__.py
        project_page.py       # 项目管理页
        dataset_page.py       # 数据集管理页
        annotation_page.py    # 标注编辑页
        train_page.py         # 训练配置与监控页
        export_page.py        # 导出管理页
      widgets/
        __init__.py
        image_canvas.py       # 图片画布（缩放/拖拽/框绘制）
        class_mapping_table.py # 类别映射表格
        train_log_panel.py    # 训练日志面板
        model_version_card.py # 模型版本卡片
    services/
      __init__.py
      project_service.py      # 项目 CRUD
      dataset_service.py      # 数据导入/校验/切分
      annotation_service.py   # 标注编辑/辅助标注/批量确认
      training_service.py     # 训练任务管理
      version_service.py      # 模型版本管理
      export_service.py       # 导出任务管理
    domain/
      __init__.py
      models.py               # 数据模型定义
      enums.py                # 枚举定义
      schemas.py              # 请求/响应 schema
    infra/
      __init__.py
      db/
        __init__.py
        sqlite.py             # SQLite 连接与初始化
        migrations/
          __init__.py
          v001_initial.py     # 初始表结构
      storage/
        __init__.py
        file_repo.py          # 文件系统操作
      ml/
        __init__.py
        ultralytics_runner.py # Ultralytics 训练执行器
        onnx_exporter.py      # ONNX 导出器
      logging/
        __init__.py
        logger.py             # 日志系统
    tasks/
      __init__.py
      task_manager.py         # 任务调度器
      worker_process.py       # 子进程工作器
  main.py                     # 入口
  tests/
    __init__.py
    unit/
      test_yolo_parser.py
      test_class_mapping.py
      test_annotation_edit.py
      test_train_config.py
    integration/
      test_import_train_export.py
      test_assisted_annotation.py
  packaging/
    build_cpu.py              # CPU 包构建脚本
    build_cuda.py             # CUDA 包构建脚本
    spec_cpu.spec             # PyInstaller spec (CPU)
    spec_cuda.spec            # PyInstaller spec (CUDA)
```

### 4.2 数据目录约定

```
<project_root>/
  datasets/
    <dataset_name>/
      images/
      labels/
      splits/
  models/
    <version_id>/
      weights/
      metrics/
      logs/
  exports/
    <version_id>/
      model.pt
      model.onnx
  .cache/                     # 临时文件，周期清理
  labeltorch.db               # SQLite 元数据库
```

## 5. 里程碑实施计划

### M1: 项目骨架

**目标**: 可打开主界面并创建本地项目

**实现内容**:
1. 初始化 PySide6 应用壳（主窗口、侧边导航、页面切换）
2. 建立 SQLite 数据模型与迁移（projects/datasets/classes 等核心表）
3. 搭建日志系统与全局异常捕获
4. 项目 Service 实现创建/打开/列表
5. 项目页面 UI（创建项目对话框、项目列表）

**验收**: 可启动应用，创建项目并在 SQLite 中持久化

### M2: 数据与标注

**目标**: 导入后可完成编辑并正确回写标签文件

**实现内容**:
1. YOLO txt 导入器（扫描 images/labels 目录，解析标签文件）
2. 样本校验器（图片完整性、坐标合法性、类别一致性）
3. 类别抽取与 class 重映射（抽取→排序→重映射→批量写回）
4. 数据集管理页面 UI
5. bbox 编辑器（图片浏览/缩放/拖拽，框新增/删除/移动/缩放，类别切换，批量保存）
6. 标注编辑页面 UI（含图片画布、标注列表、类别选择）

**验收**: 导入 YOLO 数据集，完成框编辑，保存后标签文件正确更新

### M3: 训练与版本

**目标**: 支持 v5/v8/v8_obb/v10/v11 训练，训练完成自动生成版本

**实现内容**:
1. 训练任务实体与状态机（pending→running→succeeded/failed/stopped）
2. Ultralytics 子进程执行器（配置生成、进程启动、日志收集、指标解析）
3. 参数配置面板（模型族选择、img_size/batch/epochs/patience/device/workers）
4. 训练监控面板（实时日志、epoch 进度、指标图表、早停控制）
5. 训练完成自动入库 ModelVersion
6. 版本列表与指标展示页面
7. Task Manager 实现（子进程调度、状态轮询）

**验收**: 配置并启动训练，查看实时日志，训练完成自动生成版本记录

### M4: 辅助标注与增量训练

**目标**: 完成"老模型辅助新数据标注+增量训练"闭环

**实现内容**:
1. 历史模型推理接口（加载 pt 权重，对指定数据集推理）
2. 推理结果渲染（候选框+置信度显示在画布上）
3. 置信度阈值筛选滑块
4. 批量确认逻辑（一键确认所有高置信度候选框）
5. 候选框与手工编辑统一交互
6. 选择 parent version 权重继续训练（增量训练配置）
7. 辅助标注页面 UI

**验收**: 选择历史模型推理→阈值筛选→批量确认→增量训练→新版本生成

### M5: 导出与发布

**目标**: 双包均可解压即用并完成导出

**实现内容**:
1. pt 导出（复制 best.pt 到导出目录）
2. onnx 导出（调用 Ultralytics export，参数可配置）
3. ONNX 参数界面（opset/dynamic/simplify 配置）
4. 导出任务状态管理
5. 导出结果验证（onnxruntime 加载检查）
6. Windows CPU/CUDA 双包打包脚本（PyInstaller）
7. 启动自检与错误提示（可写目录/SQLite/CUDA 检查）
8. 数据集切分功能（train/val 比例配置与 YAML 生成）

**验收**: 双包解压即用，pt/onnx 导出并验证可用

### V0.2: 效率增强与可恢复性

1. 断点续训（基于 Ultralytics resume 参数）
2. 自动混合精度 AMP 配置
3. 实验对比页（多版本指标并排比较）
4. COCO/VOC 单向导入

### V0.3: 规模化训练能力

1. 多卡训练配置
2. 超参搜索接口
3. OBB 交互增强（旋转框编辑）
4. 数据健康度分析（类别分布/框尺寸分布）

### V0.4: 任务类型扩展

1. 分类任务标注与训练
2. 异常检测任务
3. 多任务统一项目空间

### V0.5: 工程化与企业级稳定性

1. 插件化模型适配器
2. 配置模板市场（本地）
3. 异常诊断与一键导出诊断包

### V1.0: 成熟产品发布

1. 完整回归测试矩阵
2. 跨版本兼容策略
3. 发布节奏与 LTS 维护策略
4. 关键路径性能优化
5. 中英文 README
6. Release 发布（符合语义化版本规范）

## 6. 关键接口定义

### 6.1 Dataset Service
```python
import_dataset(path: str, format: str = "yolo_txt") -> DatasetImportResult
validate_dataset(dataset_id: str) -> ValidationReport
split_dataset(dataset_id: str, train_ratio: float, val_ratio: float) -> SplitResult
remap_classes(dataset_id: str, mapping: dict[int, int]) -> RemapResult
```

### 6.2 Training Service
```python
create_train_job(req: TrainJobCreateRequest) -> TrainJob
start_train_job(job_id: str) -> None
stop_train_job(job_id: str) -> None
get_train_job_status(job_id: str) -> TrainJobStatus
```

### 6.3 Version Service
```python
create_model_version(job_id: str) -> ModelVersion
list_model_versions(project_id: str) -> list[ModelVersion]
link_parent_version(version_id: str, parent_version_id: str) -> None
```

### 6.4 Annotation Service
```python
run_assisted_annotation(req: AssistedAnnotationRequest) -> AssistedAnnotationBatch
apply_threshold(batch_id: str, conf_thres: float) -> AssistedAnnotationBatch
save_annotation_edit(sample_id: str, edits: list[BoxEdit]) -> None
bulk_confirm(sample_ids: list[str]) -> BulkConfirmResult
```

### 6.5 Export Service
```python
export_model(req: ExportRequest) -> ExportTask
get_export_status(task_id: str) -> ExportStatus
```

## 7. 数据模型

### SQLite 核心表

```sql
-- 项目表
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    root_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- 数据集表
CREATE TABLE datasets (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    name TEXT NOT NULL,
    image_dir TEXT NOT NULL,
    label_dir TEXT NOT NULL,
    format TEXT NOT NULL DEFAULT 'yolo_txt',
    sample_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

-- 数据集样本表
CREATE TABLE dataset_samples (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL REFERENCES datasets(id),
    image_path TEXT NOT NULL,
    label_path TEXT,
    width INTEGER,
    height INTEGER,
    status TEXT DEFAULT 'valid'
);

-- 类别映射表
CREATE TABLE class_mappings (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL REFERENCES datasets(id),
    original_id INTEGER NOT NULL,
    mapped_id INTEGER NOT NULL,
    class_name TEXT NOT NULL
);

-- 训练任务表
CREATE TABLE train_jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    dataset_id TEXT NOT NULL REFERENCES datasets(id),
    model_family TEXT NOT NULL,
    config_json TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    metrics_json TEXT,
    log_path TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT
);

-- 模型版本表
CREATE TABLE model_versions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    job_id TEXT NOT NULL REFERENCES train_jobs(id),
    parent_version_id TEXT REFERENCES model_versions(id),
    best_pt_path TEXT,
    metrics_json TEXT,
    created_at TEXT NOT NULL
);

-- 标注记录表
CREATE TABLE annotation_changes (
    id TEXT PRIMARY KEY,
    sample_id TEXT NOT NULL REFERENCES dataset_samples(id),
    action TEXT NOT NULL,
    boxes_json TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    created_at TEXT NOT NULL
);

-- 导出任务表
CREATE TABLE export_tasks (
    id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL REFERENCES model_versions(id),
    format TEXT NOT NULL,
    options_json TEXT,
    status TEXT DEFAULT 'pending',
    output_path TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT
);
```

## 8. 边界条件与异常处理

### 8.1 边界条件

1. **GPU 环境差异**: CPU/CUDA 双包分发；启动时检测 CUDA 可用性；CUDA 不可用时自动降级 CPU 并提示
2. **大数据集性能**: 缩略图缓存、分页加载（每页50张）、后台预取、懒加载
3. **标签重映射误操作**: 执行前预览 diff、二次确认弹窗、保留回滚点
4. **训练异常隔离**: 子进程崩溃仅更新状态为 failed，主进程不退出
5. **标签原子写入**: 先写临时文件再 rename 替换，避免部分写入

### 8.2 异常处理策略

| 异常场景 | 处理方式 |
|----------|----------|
| 数据集校验错误 | 按样本粒度收集，不阻断整体导入 |
| 训练子进程异常退出 | 更新状态为 failed，保留日志 |
| 显存不足 | 可读提示 + 建议降低 batch/device |
| ONNX 导出失败 | 保留失败日志，提示可读原因 |
| SQLite 锁冲突 | WAL 模式 + 重试机制 |
| 图片格式不支持 | 标记为 invalid，跳过并报告 |

## 9. 数据流路径

### 9.1 数据导入流
```
用户选择目录 → DatasetService.import_dataset()
  → 扫描 images/labels 目录
  → 解析 YOLO txt 标签
  → 校验坐标合法性
  → 写入 dataset_samples 表
  → 抽取类别写入 class_mappings 表
  → 返回导入报告
```

### 9.2 标注编辑流
```
用户编辑框 → AnnotationService.save_annotation_edit()
  → 校验框坐标合法性
  → 写入 annotation_changes 审计表
  → 原子写回 YOLO txt 标签文件（temp→rename）
```

### 9.3 训练执行流
```
用户配置参数 → TrainingService.create_train_job()
  → 生成配置快照（不可变）→ 写入 train_jobs 表
  → TrainingService.start_train_job()
    → TaskManager 启动子进程
    → 子进程执行 UltralyticsRunner
    → 实时解析 stdout 日志 → 更新 UI
    → 训练完成 → 创建 ModelVersion
    → 训练失败 → 更新状态为 failed
```

### 9.4 辅助标注流
```
用户选择历史模型 → AnnotationService.run_assisted_annotation()
  → 加载模型权重
  → 对数据集逐张推理
  → 生成候选框 + 置信度
  → 阈值筛选
  → 用户批量确认 → 写回标签文件
```

### 9.5 导出流
```
用户选择版本与格式 → ExportService.export_model()
  → 创建导出任务
  → pt: 复制 best.pt 到导出目录
  → onnx: 调用 Ultralytics export API
  → 验证导出结果（onnxruntime 加载检查）
  → 更新导出任务状态
```

## 10. 测试策略

### 10.1 单元测试
- YOLO 坐标解析与合法性校验
- 类别重映射一致性
- 标注编辑回写正确性
- TrainConfig 参数校验
- 标签原子写入机制

### 10.2 集成测试
- 导入→训练→导出完整 happy path
- 辅助标注→批量确认→增量训练闭环
- 数据集切分与 YAML 生成

### 10.3 稳定性测试
- 100/1000/10000 张样本导入与浏览
- 训练期间 UI 长时间可响应

### 10.4 打包测试
- CPU 包解压即用验证
- CUDA 包解压即用验证
- pt/onnx 导出可用性验证

## 11. 预期成果

### 11.1 MVP (V0.1) 交付物
1. 可运行的 LabelTorch 桌面应用
2. Windows CPU 绿色包（labeltorch-windows-cpu.zip）
3. Windows CUDA 绿色包（labeltorch-windows-cuda121.zip）
4. 完整单元测试与集成测试
5. 中英文 README

### 11.2 V1.0 交付物
1. 功能完整的成熟产品
2. 全量回归测试通过
3. 跨版本兼容验证
4. 符合语义化版本的 Release
5. 完善的中英文文档

## 12. 环境与工具

- Python 3.11+（使用现有 Anaconda 环境）
- PySide6
- Ultralytics
- onnxruntime
- PyInstaller（打包）
- pytest（测试）
- Git（版本管理，双平台备份）
