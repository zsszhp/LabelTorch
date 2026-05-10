# LabelTorch

Industrial Defect Detection Annotation & Training Tool. Based on PySide6 + SQLite + Ultralytics.

## Quick Start

### 1. One-click Launch (Windows)

Double-click `start.bat` in the project root.

Or manually:

```bash
# Activate conda environment
conda activate labeltorch

# Run
python -m labeltorch
```

### 2. Install from Source

```bash
git clone https://gitee.com/zzsszhp/LabelTorch.git
cd LabelTorch
pip install -e .
labeltorch
```

### 3. Build Release Package

```bash
# Windows
build_release.bat

# Output: dist/LabelTorch/LabelTorch.exe
```

## Dependencies

- Python >= 3.10
- PySide6 >= 6.5
- Pillow >= 9.0
- Ultralytics >= 8.0
- ONNXRuntime >= 1.15 (optional, for ONNX export)

## Features

- **Project Management**: Create/open/delete projects
- **Dataset Import**: Import YOLO-format datasets with validation
- **Annotation**: BBox drawing, selection, move, resize with ImageCanvas
- **Class Remapping**: Remap class IDs across datasets
- **Dataset Split**: Train/val split with data.yaml generation
- **Training**: YOLOv5/v8/v8-OBB/v10/v11 training via Ultralytics
- **Model Versioning**: Track model versions with parent linkage
- **Export**: PT copy and ONNX export with verification
- **Assisted Annotation**: Model inference for pre-labeling

## Project Structure

```
labeltorch/
  app/
    context.py           # AppContext (7 services)
    domain/enums.py      # Domain enums
    infra/
      db/                # SQLite + migrations
      storage/           # file_repo, yolo_parser
      logging/           # Structured logger
      startup_check.py   # Environment diagnostics
    services/            # 7 services
    ui/
      main_window.py     # MainWindow
      pages/             # 5 pages
      widgets/           # ImageCanvas
  main.py                # Entry point
  tests/unit/            # 73 unit tests
```

## Test

```bash
python -m pytest labeltorch/tests/unit/ -v
```

## License

MIT
