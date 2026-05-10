# LabelTorch Full Product - Summary

## Overview
LabelTorch is a desktop YOLO annotation & training tool built with PySide6 + SQLite + Ultralytics. All 5 milestones have been implemented and committed.

## Milestone Summary

### M1: Project Skeleton (17 unit tests)
- PySide6 main window with tab navigation
- SQLite database with migration system (7 tables)
- Structured logging with rotation
- ProjectService CRUD
- Global exception handler

### M2: Data & Annotation (52 unit tests)
- YOLO txt parser with validation (YOLOBBox, YOLOLabelFile)
- DatasetService: import, validate, split, class remap
- AnnotationService: save edits, audit trail, bulk confirm
- ImageCanvas: zoom/pan, bbox drawing, selection, move, resize handles
- AnnotationPage with canvas + class combo + box list

### M3: Training & Version (73 unit tests)
- TrainingService: create jobs, start subprocess, state machine
- TrainConfig with validation & JSON serialization
- VersionService: model version tracking with parent linkage
- ExportService: pt copy, ONNX export with onnxruntime verification
- AppContext integrates all 7 services

### M4: Assisted Annotation (73 unit tests)
- InferenceService: load YOLO model, predict single/batch images
- Returns box dicts (class_id, x_center, y_center, width, height, confidence)
- Clean service layer without UI dependency

### M5: Export & Polish (73 unit tests)
- StartupCheck: environment diagnostics (SQLite, PySide6, Pillow, Ultralytics, CUDA)
- TrainPage integrated with real TrainingService
- ExportPage integrated with real ExportService
- main.py startup self-check flow

## Code Statistics
- 51 Python source files
- 73 unit tests (all passing)
- 6 git commits

## Architecture
```
labeltorch/
  app/
    context.py          # AppContext (7 services)
    domain/enums.py     # TrainJobStatus, ModelFamily, ExportStatus
    infra/
      db/sqlite.py      # Database + migration
      storage/          # file_repo, yolo_parser
      logging/          # structured logger
      startup_check.py  # environment diagnostics
    services/           # 7 services
    ui/
      main_window.py    # MainWindow
      pages/            # 5 pages
      widgets/          # ImageCanvas
  main.py
  tests/unit/           # 73 tests
```

## Git Commits
1. `989f4d8` Initial commit
2. `c028adb` feat(M1): PySide6 shell, SQLite models, logging, project service - 17 unit tests passed
3. `5c35e72` feat(M2): data import, annotation editing, bbox editor - 52 unit tests passed
4. `f982227` feat(M3): Training service, version management, export service - 73 unit tests passed
5. `091581e` feat(M4): Inference service for assisted annotation - 73 unit tests passed
6. `85e6120` feat(M5): Startup check, export UI, train page, inference service - 73 tests passed

## Remote Status
- Gitee: pushed successfully
- GitHub: pending (network connectivity issues)
