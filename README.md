<div align="center">

# 标炬 LabelTorch

**工业缺陷检测标注与训练工具**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ultralytics](https://img.shields.io/badge/Ultralytics-8.0+-FF6F00.svg)](https://github.com/ultralytics/ultralytics)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-41CD52.svg)](https://doc.qt.io/qtforpython-6/)

端到端的桌面应用程序，集成图像标注、YOLO 模型训练与模型导出——专为工业缺陷检测工作流打造。

[English Documentation](#english-documentation) | 中文文档

</div>

---

## 功能特性

- **项目管理** — 创建、打开、删除项目，每个项目拥有独立的数据目录和 SQLite 数据库
- **数据集导入** — 导入 YOLO 格式数据集（图像 + `.txt` 标签），自动验证标签完整性
- **标注编辑** — 在自定义 `ImageCanvas` 画布上绘制、选择、移动、缩放边界框，支持按类别着色
- **数据集操作** — 训练/验证集划分并自动生成 Ultralytics 所需的 `data.yaml`，支持跨数据集类别 ID 重映射
- **模型训练** — 通过 Ultralytics 配置并启动 YOLOv5/v8/v8-OBB/v10/v11 训练任务，支持实时日志监控和状态机生命周期管理
- **ML 辅助标注** — 加载已训练模型，批量推理自动生成候选边界框，可按置信度阈值批量确认
- **模型版本管理** — 训练完成后自动创建版本记录，支持父版本溯源
- **模型导出** — 将训练好的模型导出为 `.pt`（PyTorch）或 `.onnx`（ONNX）格式，可选择性验证
- **启动自检** — 启动时自动检测运行环境（Python 包、CUDA、SQLite、ONNX Runtime 等 7 项检查）

## 软件架构

```
┌─────────────────────────────────────────────────┐
│                    UI 层                         │
│   主窗口 │ 5 个页面 │ ImageCanvas 画布组件       │
├─────────────────────────────────────────────────┤
│                 服务层                           │
│  项目 │ 数据集 │ 标注 │ 训练                     │
│  版本 │ 导出  │ 推理 │ 辅助标注                  │
├─────────────────────────────────────────────────┤
│                 领域层                           │
│  模型 (9) │ 枚举 (6) │ 模式 (13) │ BBox        │
├─────────────────────────────────────────────────┤
│               基础设施层                         │
│  SQLite+WAL │ 数据库迁移 │ 文件仓库 │ 日志      │
│  YOLO解析器 │ 启动检查                          │
└─────────────────────────────────────────────────┘
```

应用采用分层架构，职责清晰分离：

- **领域层** — 数据模型、枚举、请求/响应模式、共享值对象
- **服务层** — 业务逻辑，通过构造函数注入 `Database` 依赖
- **基础设施层** — SQLite 持久化、文件 I/O、日志、环境检测
- **UI 层** — 基于 PySide6 的桌面界面，侧边栏导航 + 页面栈

所有服务注册在 `AppContext` 中，作为全局服务定位器注入到 UI 页面。

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| UI 框架 | PySide6 (Qt for Python) | ≥ 6.5 |
| ML 框架 | Ultralytics | ≥ 8.0 |
| 图像处理 | Pillow | ≥ 9.0 |
| 数据库 | SQLite (WAL 模式) | 内置 |
| ONNX 运行时 | onnxruntime（可选） | ≥ 1.15 |
| 打包工具 | PyInstaller | — |
| 测试框架 | pytest | ≥ 7.0 |

## 快速开始

### 环境要求

- **Python** ≥ 3.10
- **CUDA**（可选，推荐用于 GPU 加速训练）

### 安装

#### 方式一：从源码安装（推荐）

```bash
git clone https://github.com/your-username/LabelTorch.git
cd LabelTorch
pip install -e .
```

#### 方式二：pip 安装

```bash
pip install labeltorch
```

#### 方式三：使用 Conda

```bash
conda create -n labeltorch python=3.10
conda activate labeltorch
git clone https://github.com/your-username/LabelTorch.git
cd LabelTorch
pip install -e .
```

如需 ONNX 导出支持，安装可选依赖：

```bash
pip install -e ".[export]"
```

### 运行

安装后，通过以下命令启动应用：

```bash
labeltorch
```

或直接以 Python 模块方式运行：

```bash
python -m labeltorch
```

Windows 用户也可以双击 `start.bat` 启动（请先编辑文件中的 Python 路径以匹配你的环境）。

## 配置说明

LabelTorch 开箱即用，无需额外配置。所有数据存储在以下目录：

```
~/.labeltorch/
├── labeltorch.db          # 全局数据库（SQLite，WAL 模式）
├── logs/                  # 应用日志
│   └── labeltorch.log     # 滚动日志（10MB × 5 个备份）
└── （项目目录）
    ├── datasets/          # 导入的数据集图像和标签
    ├── models/            # 训练好的模型权重（.pt）
    ├── exports/           # 导出的模型（.pt / .onnx）
    └── .cache/            # 临时缓存
```

### 启动自检

每次启动时，LabelTorch 自动执行 7 项检查：

| 检查项 | 严重程度 | 说明 |
|--------|----------|------|
| 可写目录 | 错误 | 能否写入 `~/.labeltorch/` |
| SQLite | 错误 | SQLite 版本及 WAL 模式支持 |
| PySide6 | 错误 | PySide6 是否已安装 |
| Pillow | 错误 | Pillow 是否已安装 |
| Ultralytics | 错误 | Ultralytics 是否已安装 |
| CUDA | 警告 | CUDA 是否可用于 GPU 训练 |
| ONNX Runtime | 警告 | ONNX Runtime 是否可用于导出验证 |

检查失败时会弹出警告对话框，但应用仍会尝试启动。警告仅记录在日志中，不会中断启动流程。

### CUDA 配置

如需 GPU 加速训练，请安装支持 CUDA 的 PyTorch：

```bash
# 示例：CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 示例：CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

未安装 CUDA 时，训练将回退到 CPU 模式（速度明显较慢）。

## 使用指南

### 工作流程

LabelTorch 的典型端到端工作流程：

```
创建项目 → 导入数据集 → 验证与划分 → 标注 → 训练 → 版本管理 → 导出
                        ↑                            │
                        └──── 辅助标注 ←─────────────┘
```

### 1. 创建项目

启动 LabelTorch，在项目页面点击 **"新建项目"**，输入项目名称并选择存储目录。每个项目维护独立的数据库和目录结构。

### 2. 导入数据集

进入数据集页面，点击 **"导入"**，选择 YOLO 格式的数据集目录。目录结构应为：

```
dataset/
├── images/
│   ├── img_001.jpg
│   ├── img_002.jpg
│   └── ...
└── labels/
    ├── img_001.txt      # YOLO 格式：类别 中心x 中心y 宽度 高度
    ├── img_002.txt
    └── ...
```

导入后，LabelTorch 自动验证标签完整性，检测缺失/多余标签，并报告统计信息。

### 3. 验证与划分

使用 **"验证"** 按钮检查标签错误（越界坐标、无效类别 ID、空标签等）。然后使用 **"划分"** 将数据集分为训练/验证集——此操作会自动生成 Ultralytics 训练所需的 `data.yaml` 文件。

### 4. 标注

打开标注页面，浏览图像并绘制边界框：
- **绘制**：在图像上点击并拖拽创建新框
- **选择**：点击已有框将其选中
- **移动**：拖拽选中的框进行重新定位
- **缩放**：拖拽选中框的角手柄调整大小
- **切换类别**：使用类别面板分配或更改框的类别

所有编辑操作均记录审计轨迹（手动/辅助来源、时间戳）。

### 5. 训练模型

进入训练页面：
1. 选择数据集
2. 选择模型系列（YOLOv5、YOLOv8、YOLOv8-OBB、YOLOv10、YOLOv11）和尺寸
3. 配置训练参数（轮次、批大小、图像尺寸、设备）
4. 点击 **"开始训练"** — 训练以子进程方式运行，日志实时显示
5. 训练完成后自动创建模型版本

### 6. 辅助标注

训练好模型后，可用其加速标注：
1. 在标注页面加载已训练的模型
2. 对选中图像运行推理 — 候选边界框带置信度分数显示
3. 逐一审核并确认/拒绝，或使用 **"批量确认"** 接受所有超过置信度阈值的结果

### 7. 导出

在导出页面选择模型版本和导出格式：
- **PT** — PyTorch 权重文件（直接复制 `best.pt`）
- **ONNX** — ONNX 格式（需安装 `onnxruntime` 以进行验证）

## 开发

### 运行测试

```bash
# 运行所有单元测试
python -m pytest labeltorch/tests/unit/ -v

# 运行并生成覆盖率报告
python -m pytest labeltorch/tests/unit/ -v --cov=labeltorch

# 运行指定测试模块
python -m pytest labeltorch/tests/unit/test_yolo_parser.py -v
```

项目目前包含 **73 个单元测试**，覆盖数据库、YOLO 解析器、项目/数据集/标注/训练服务。

### 项目结构

```
labeltorch/
├── __init__.py
├── __main__.py                  # 入口：python -m labeltorch
├── main.py                      # 应用启动（Qt + 上下文 + 主窗口）
├── app/
│   ├── context.py               # AppContext — 服务注册中心
│   ├── domain/
│   │   ├── models.py            # 9 个数据类实体
│   │   ├── enums.py             # 6 个枚举类型（模型系列、训练状态...）
│   │   ├── schemas.py           # 13 个请求/响应模式
│   │   └── bbox.py              # 共享 BBox 类
│   ├── services/
│   │   ├── project_service.py   # 项目增删改查 + 目录管理
│   │   ├── dataset_service.py   # 导入、验证、划分、重映射
│   │   ├── annotation_service.py# 保存、历史、批量确认
│   │   ├── training_service.py  # 训练任务生命周期 + 状态机
│   │   ├── version_service.py   # 模型版本追踪 + 溯源
│   │   ├── export_service.py    # PT / ONNX 导出
│   │   ├── inference_service.py # YOLO 模型推理
│   │   └── assisted_annotation_service.py  # ML 辅助标注工作流
│   ├── infra/
│   │   ├── startup_check.py     # 7 项环境诊断
│   │   ├── db/
│   │   │   ├── sqlite.py        # SQLite 数据库（WAL 模式、迁移）
│   │   │   └── migrations/
│   │   │       └── v001_initial.py  # 8 张表 + 7 个索引
│   │   ├── logging/
│   │   │   └── logger.py        # 滚动文件 + 控制台日志
│   │   └── storage/
│   │       ├── file_repo.py     # 原子写入、图像扫描、标签配对
│   │       └── yolo_parser.py   # YOLO txt 解析/验证/写入/重映射
│   ├── ui/
│   │   ├── main_window.py       # 主窗口：侧边栏 + 页面栈
│   │   ├── pages/
│   │   │   ├── project_page.py  # 项目管理
│   │   │   ├── dataset_page.py  # 数据集导入/划分/重映射
│   │   │   ├── annotation_page.py# 标注编辑 + 画布
│   │   │   ├── train_page.py    # 训练配置 + 监控
│   │   │   └── export_page.py   # 模型导出
│   │   └── widgets/
│   │       └── image_canvas.py  # 自定义 QWidget：图像 + 边界框编辑器
│   └── tasks/                   # （保留：异步任务）
└── tests/
    ├── unit/                    # 73 个单元测试
    │   ├── test_database.py
    │   ├── test_yolo_parser.py
    │   ├── test_project_service.py
    │   ├── test_dataset_service.py
    │   └── test_training_service.py
    └── integration/             # （保留：集成测试）
```

### 贡献指南

欢迎贡献！参与方式：

1. Fork 本仓库
2. 创建功能分支（`git checkout -b feature/my-feature`）
3. 进行修改并添加测试
4. 确保所有测试通过（`python -m pytest labeltorch/tests/unit/ -v`）
5. 提交描述性的 commit 消息
6. 推送并创建 Pull Request

请遵循现有的代码风格，并确保修改包含适当的测试覆盖。

## 打包发布

构建 Windows 独立可执行文件：

```bash
build_release.bat
```

输出：`dist/LabelTorch/LabelTorch.exe`

> **注意**：构建前请编辑 `build_release.bat`，将 Python 路径设置为你的环境路径。

## 常见问题

**Q：训练速度很慢，如何启用 GPU？**

A：安装支持 CUDA 的 PyTorch（参见 [CUDA 配置](#cuda-配置)）。启动 LabelTorch 后查看启动日志，CUDA 检查项应显示你的 GPU 设备名称。

**Q：ONNX 导出失败，提示导入错误。**

A：安装 ONNX Runtime：`pip install onnxruntime>=1.15`

**Q：Linux 上 PySide6 导入失败。**

A：确保安装了所需的系统库。Ubuntu 上执行：`sudo apt install libgl1-mesa-glx libxkbcommon-x11-0 libdbus-1-3`

**Q：`start.bat` 无法运行，提示找不到 Python。**

A：`start.bat` 中包含硬编码的 conda 路径。请打开文件，将 `PYTHON` 变量修改为你的 Python 可执行文件路径。

**Q：数据存储在哪里？**

A：所有数据存储在 `~/.labeltorch/` 目录下。全局数据库为 `~/.labeltorch/labeltorch.db`。项目相关的文件（数据集、模型、导出）位于你创建项目时选择的项目目录中。

**Q：没有 GPU 能用 LabelTorch 吗？**

A：可以。所有功能在 CPU 模式下均可用，但模型训练速度会明显较慢。标注、数据集管理和导出功能不受 GPU 影响即可全速运行。

## 开发路线

- [ ] 分割掩码标注支持
- [ ] OBB（旋转边界框）标注和训练
- [ ] 多语言界面（中英文）
- [ ] 插件系统支持自定义模型后端
- [ ] 云存储集成
- [ ] 团队协作功能

## 致谢

LabelTorch 的开发参考和借鉴了以下开源项目：

- [Ultralytics](https://github.com/ultralytics/ultralytics) — YOLO 模型训练和推理框架
- [X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) — AI 辅助标注工具
- [LabelImg](https://github.com/HumanSignal/labelImg) — 经典图像标注工具
- [Labelme](https://github.com/wkentaro/labelme) — 多形状标注工具
- [CVAT](https://github.com/cvat-ai/cvat) — 计算机视觉标注工具

## 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

---

<div align="center">

*The following is the English version of this document.*

[中文文档](#功能特性) | English Documentation

</div>

---

# English Documentation

## Features

- **Project Management** — Create, open, and delete projects, each with isolated data directories and SQLite databases
- **Dataset Import** — Import YOLO-format datasets (images + `.txt` labels) with automatic validation and integrity checks
- **Annotation Editing** — Draw, select, move, and resize bounding boxes on a custom `ImageCanvas` widget with per-class color coding
- **Dataset Operations** — Train/val split with Ultralytics `data.yaml` generation, class ID remapping across datasets
- **Model Training** — Configure and launch YOLOv5/v8/v8-OBB/v10/v11 training jobs via Ultralytics, with real-time log monitoring and state machine lifecycle management
- **ML-Assisted Annotation** — Load a trained model, run batch inference to auto-generate candidate bounding boxes, then bulk-confirm or filter by confidence threshold
- **Model Versioning** — Automatic version tracking after each training run with parent lineage linkage
- **Model Export** — Export trained models as `.pt` (PyTorch) or `.onnx` (ONNX) format with optional verification
- **Startup Self-Check** — Automatic environment diagnostics on launch (Python packages, CUDA, SQLite, ONNX Runtime)

## Architecture

```
┌─────────────────────────────────────────────────┐
│                    UI Layer                      │
│   MainWindow │ 5 Pages │ ImageCanvas Widget     │
├─────────────────────────────────────────────────┤
│                Services Layer                    │
│  Project │ Dataset │ Annotation │ Training      │
│  Version │ Export  │ Inference  │ Assisted      │
├─────────────────────────────────────────────────┤
│                Domain Layer                      │
│  Models (9) │ Enums (6) │ Schemas (13) │ BBox  │
├─────────────────────────────────────────────────┤
│            Infrastructure Layer                  │
│  SQLite+WAL │ Migrations │ FileRepo │ Logger   │
│  YOLOParser │ StartupCheck                     │
└─────────────────────────────────────────────────┘
```

The application follows a layered architecture with clear separation of concerns:

- **Domain Layer** — Data models, enums, request/response schemas, and shared value objects
- **Services Layer** — Business logic with constructor-injected `Database` dependency
- **Infrastructure Layer** — SQLite persistence, file I/O, logging, and environment checks
- **UI Layer** — PySide6-based desktop interface with sidebar navigation and page stack

All services are registered in `AppContext`, which serves as the application-wide service locator and is injected into UI pages.

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| UI Framework | PySide6 (Qt for Python) | ≥ 6.5 |
| ML Framework | Ultralytics | ≥ 8.0 |
| Image Processing | Pillow | ≥ 9.0 |
| Database | SQLite (WAL mode) | built-in |
| ONNX Runtime | onnxruntime (optional) | ≥ 1.15 |
| Packaging | PyInstaller | — |
| Testing | pytest | ≥ 7.0 |

## Getting Started

### Prerequisites

- **Python** ≥ 3.10
- **CUDA** (optional, recommended for GPU-accelerated training)

### Installation

#### Option 1: Install from Source (Recommended)

```bash
git clone https://github.com/your-username/LabelTorch.git
cd LabelTorch
pip install -e .
```

#### Option 2: Install with pip

```bash
pip install labeltorch
```

#### Option 3: Using Conda

```bash
conda create -n labeltorch python=3.10
conda activate labeltorch
git clone https://github.com/your-username/LabelTorch.git
cd LabelTorch
pip install -e .
```

For ONNX export support, install the optional dependency:

```bash
pip install -e ".[export]"
```

### Running

After installation, launch the application with:

```bash
labeltorch
```

Or run directly as a Python module:

```bash
python -m labeltorch
```

On Windows, you can also double-click `start.bat` (edit the Python path inside the file to match your environment first).

## Configuration

LabelTorch requires zero configuration to get started. All data is stored under:

```
~/.labeltorch/
├── labeltorch.db          # Global database (SQLite, WAL mode)
├── logs/                  # Application logs
│   └── labeltorch.log     # Rotating log (10MB × 5 backups)
└── (project directories)
    ├── datasets/          # Imported dataset images & labels
    ├── models/            # Trained model weights (.pt)
    ├── exports/           # Exported models (.pt / .onnx)
    └── .cache/            # Temporary cache
```

### Startup Self-Check

On every launch, LabelTorch runs 7 automatic checks:

| Check | Severity | Description |
|-------|----------|-------------|
| Writable Directory | Error | Can write to `~/.labeltorch/` |
| SQLite | Error | SQLite version and WAL mode support |
| PySide6 | Error | PySide6 is installed and importable |
| Pillow | Error | Pillow is installed and importable |
| Ultralytics | Error | Ultralytics is installed and importable |
| CUDA | Warning | CUDA availability for GPU training |
| ONNX Runtime | Warning | ONNX Runtime for export verification |

Errors will display a warning dialog but the application will still attempt to start. Warnings are logged but do not interrupt startup.

### CUDA Setup

For GPU-accelerated training, install PyTorch with CUDA support:

```bash
# Example: CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Example: CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Without CUDA, training will fall back to CPU (significantly slower).

## Usage

### Workflow

The typical end-to-end workflow in LabelTorch:

```
Create Project → Import Dataset → Validate & Split → Annotate → Train → Version → Export
                                    ↑                              │
                                    └──── Assisted Annotation ←────┘
```

### 1. Create a Project

Launch LabelTorch, click **"New Project"** on the Project page, enter a name and choose a storage directory. Each project maintains its own isolated database and directory structure.

### 2. Import a Dataset

Navigate to the Dataset page, click **"Import"**, and select a YOLO-format dataset directory. The directory should contain:

```
dataset/
├── images/
│   ├── img_001.jpg
│   ├── img_002.jpg
│   └── ...
└── labels/
    ├── img_001.txt      # YOLO format: class x_center y_center width height
    ├── img_002.txt
    └── ...
```

After import, LabelTorch validates label integrity, detects missing/extra labels, and reports statistics.

### 3. Validate & Split

Use the **"Validate"** button to check for label errors (out-of-bounds coordinates, invalid class IDs, empty labels). Then use **"Split"** to divide the dataset into train/val sets — this generates the `data.yaml` file required by Ultralytics training.

### 4. Annotate

Open the Annotation page to browse images and draw bounding boxes:
- **Draw**: Click and drag on the image to create a new box
- **Select**: Click on an existing box to select it
- **Move**: Drag a selected box to reposition it
- **Resize**: Drag the corner handles of a selected box
- **Class**: Use the class panel to assign or change the class of a box

All edits are recorded with an audit trail (manual vs. assisted source, timestamp).

### 5. Train a Model

Navigate to the Training page:
1. Select a dataset
2. Choose a model family (YOLOv5, YOLOv8, YOLOv8-OBB, YOLOv10, YOLOv11) and size
3. Configure training parameters (epochs, batch size, image size, device)
4. Click **"Start Training"** — training runs as a subprocess, with logs displayed in real-time
5. On completion, a model version is automatically created

### 6. Assisted Annotation

After training a model, use it to accelerate annotation:
1. Load the trained model on the Annotation page
2. Run inference on selected images — candidate bounding boxes appear with confidence scores
3. Review and confirm/reject each suggestion, or use **"Bulk Confirm"** to accept all above a confidence threshold

### 7. Export

On the Export page, select a model version and choose an export format:
- **PT** — PyTorch weight file (direct copy of `best.pt`)
- **ONNX** — ONNX format (requires `onnxruntime` for verification)

## Development

### Running Tests

```bash
# Run all unit tests
python -m pytest labeltorch/tests/unit/ -v

# Run with coverage
python -m pytest labeltorch/tests/unit/ -v --cov=labeltorch

# Run a specific test module
python -m pytest labeltorch/tests/unit/test_yolo_parser.py -v
```

The project currently has **73 unit tests** covering database, YOLO parser, project/dataset/annotation/training services.

### Project Structure

```
labeltorch/
├── __init__.py
├── __main__.py                  # Entry: python -m labeltorch
├── main.py                      # App bootstrap (Qt + context + window)
├── app/
│   ├── context.py               # AppContext — service registry
│   ├── domain/
│   │   ├── models.py            # 9 dataclass entities
│   │   ├── enums.py             # 6 enum types (ModelFamily, TrainJobStatus, ...)
│   │   ├── schemas.py           # 13 request/response schemas
│   │   └── bbox.py              # Shared BBox class
│   ├── services/
│   │   ├── project_service.py   # Project CRUD + directory management
│   │   ├── dataset_service.py   # Import, validate, split, remap
│   │   ├── annotation_service.py# Save, history, bulk confirm
│   │   ├── training_service.py  # Train job lifecycle + state machine
│   │   ├── version_service.py   # Model version tracking + lineage
│   │   ├── export_service.py    # PT / ONNX export
│   │   ├── inference_service.py # YOLO model inference
│   │   └── assisted_annotation_service.py  # ML-assisted workflow
│   ├── infra/
│   │   ├── startup_check.py     # 7-item environment diagnostics
│   │   ├── db/
│   │   │   ├── sqlite.py        # SQLite Database (WAL, migrations)
│   │   │   └── migrations/
│   │   │       └── v001_initial.py  # 8 tables + 7 indexes
│   │   ├── logging/
│   │   │   └── logger.py        # Rotating file + console logger
│   │   └── storage/
│   │       ├── file_repo.py     # Atomic write, image scan, label pairing
│   │       └── yolo_parser.py   # YOLO txt parse/validate/write/remap
│   ├── ui/
│   │   ├── main_window.py       # QMainWindow: sidebar + page stack
│   │   ├── pages/
│   │   │   ├── project_page.py  # Project management
│   │   │   ├── dataset_page.py  # Dataset import/split/remap
│   │   │   ├── annotation_page.py# Annotation editing + canvas
│   │   │   ├── train_page.py    # Training config + monitoring
│   │   │   └── export_page.py   # Model export
│   │   └── widgets/
│   │       └── image_canvas.py  # Custom QWidget: image + bbox editor
│   └── tasks/                   # (Reserved for async tasks)
└── tests/
    ├── unit/                    # 73 unit tests
    │   ├── test_database.py
    │   ├── test_yolo_parser.py
    │   ├── test_project_service.py
    │   ├── test_dataset_service.py
    │   └── test_training_service.py
    └── integration/             # (Reserved)
```

### Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`python -m pytest labeltorch/tests/unit/ -v`)
5. Commit with a descriptive message
6. Push and open a Pull Request

Please follow the existing code style and ensure your changes include appropriate test coverage.

## Building

To build a standalone Windows executable:

```bash
build_release.bat
```

Output: `dist/LabelTorch/LabelTorch.exe`

> **Note**: Edit `build_release.bat` to set the correct Python path for your environment before building.

## FAQ

**Q: Training is very slow — how do I enable GPU?**

A: Install PyTorch with CUDA support (see [CUDA Setup](#cuda-setup)). Launch LabelTorch and check the startup log — it should show your GPU device name under the CUDA check.

**Q: ONNX export fails with an import error.**

A: Install ONNX Runtime: `pip install onnxruntime>=1.15`

**Q: PySide6 fails to import on Linux.**

A: Make sure you have the required system libraries. On Ubuntu: `sudo apt install libgl1-mesa-glx libxkbcommon-x11-0 libdbus-1-3`

**Q: `start.bat` doesn't work — it says Python not found.**

A: `start.bat` contains a hardcoded conda path. Open the file and change the `PYTHON` variable to point to your Python executable.

**Q: Where is my data stored?**

A: All data is stored under `~/.labeltorch/`. The global database is `~/.labeltorch/labeltorch.db`. Project-specific files (datasets, models, exports) are in the project directory you chose when creating the project.

**Q: Can I use LabelTorch without a GPU?**

A: Yes. All features work on CPU, but model training will be significantly slower. Annotation, dataset management, and export work at full speed regardless of GPU availability.

## Roadmap

- [ ] Segmentation mask annotation support
- [ ] OBB (Oriented Bounding Box) annotation and training
- [ ] Multi-language UI (English/Chinese)
- [ ] Plugin system for custom model backends
- [ ] Cloud storage integration
- [ ] Team collaboration features

## Acknowledgments

LabelTorch was inspired by and references the following open-source projects:

- [Ultralytics](https://github.com/ultralytics/ultralytics) — YOLO model training and inference framework
- [X-AnyLabeling](https://github.com/CVHub520/X-AnyLabeling) — AI-assisted annotation tool
- [LabelImg](https://github.com/HumanSignal/labelImg) — Classic image annotation tool
- [Labelme](https://github.com/wkentaro/labelme) — Multi-shape annotation tool
- [CVAT](https://github.com/cvat-ai/cvat) — Computer Vision Annotation Tool

## License

This project is licensed under the [MIT License](LICENSE).
