# Open-Source README Documentation

## Requirement Scenario

The user wants to open-source the LabelTorch project and needs a professional, comprehensive bilingual (Chinese + English) README that follows open-source conventions. The current README is minimal and lacks the depth expected of a serious open-source project.

## Processing Logic

1. Replace the existing `README.md` with a fully bilingual, convention-compliant open-source README
2. Create the missing `LICENSE` file (MIT, as declared in pyproject.toml)
3. The README should be structured with English first, then Chinese version, as is common for projects targeting both international and Chinese audiences

## Architecture & Content Design

### README Structure (per language)

1. **Header** - Project name, tagline, badges (Python version, License, Platform)
2. **Features** - Key feature list with icons/emojis for scanability
3. **Screenshots** - Placeholder section (project has no screenshots yet, note this)
4. **Architecture** - Layered architecture diagram (Domain → Services → Infra → UI), data flow description
5. **Tech Stack** - Core dependencies with versions
6. **Getting Started** - Prerequisites, installation (pip, conda, from source), running
7. **Configuration** - Data directory, database location, CUDA setup, environment checks
8. **Usage Guide** - Step-by-step workflow: Project → Dataset → Annotation → Training → Export → Assisted Annotation
9. **Development** - Running tests, project structure in detail, contribution guidelines
10. **Building** - PyInstaller packaging
11. **FAQ / Troubleshooting** - Common issues (CUDA not found, ONNX export, etc.)
12. **Roadmap** - Future plans placeholder
13. **License** - MIT
14. **Acknowledgments** - Reference projects

### Additional Files

- `LICENSE` - MIT License file (missing, pyproject.toml declares MIT)
- The `start.bat` references a hardcoded conda path; note in docs that users should adjust this

## Affected Files

| File | Type | Description |
|------|------|-------------|
| `README.md` | Rewrite | Complete bilingual README |
| `LICENSE` | Create | MIT License file |

## Implementation Details

### Badge Design
```
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![Ultralytics](https://img.shields.io/badge/Ultralytics-8.0+-FF6F00.svg)]()
```

### Architecture Diagram (ASCII)
```
┌─────────────────────────────────────────────┐
│                    UI Layer                  │
│  MainWindow │ Pages (5) │ Widgets (Canvas)  │
├─────────────────────────────────────────────┤
│               Services Layer                │
│  Project │ Dataset │ Annotation │ Training  │
│  Version │ Export  │ Inference  │ Assisted  │
├─────────────────────────────────────────────┤
│               Domain Layer                  │
│  Models (9) │ Enums (6) │ Schemas (13)     │
│  BBox (shared)                              │
├─────────────────────────────────────────────┤
│             Infrastructure Layer            │
│  SQLite+WAL │ Migrations │ FileRepo        │
│  YOLOParser │ Logger     │ StartupCheck    │
└─────────────────────────────────────────────┘
```

### Data Directory Structure
```
~/.labeltorch/
├── labeltorch.db          # Global database
├── logs/                  # Application logs
│   └── labeltorch.log     # Rotating (10MB × 5)
└── [project_root]/
    ├── datasets/          # Imported datasets
    ├── models/            # Trained model weights
    ├── exports/           # Exported models
    └── .cache/            # Temporary cache
```

### Workflow Description
The complete workflow from data to deployment:
1. Create Project → 2. Import Dataset (YOLO format) → 3. Validate & Split → 4. Annotate (manual/assisted) → 5. Train Model → 6. Version Management → 7. Export (PT/ONNX)

### Configuration Details
- Data directory: `~/.labeltorch/` (auto-created)
- Database: SQLite with WAL mode, auto-migration
- Logging: Rotating file handler, 10MB per file, 5 backups
- Startup self-check: 7 items (writable dir, SQLite, PySide6, Pillow, Ultralytics, CUDA, ONNX Runtime)

### Troubleshooting Items
- CUDA not available → Install PyTorch with CUDA support
- ONNX export fails → Install onnxruntime
- PySide6 import error → Check Qt platform plugin
- Slow training on CPU → Use GPU, or reduce batch size
- start.bat conda path → Edit the hardcoded path

## Boundary Conditions

- No screenshots available yet; include placeholder text suggesting users add them
- The project is MVP (v0.1.0); note this clearly
- start.bat has a hardcoded path; must warn users to modify it
- build_release.bat also has a hardcoded path; same warning needed
- No CONTRIBUTING.md yet; include basic contribution guidelines in README
- No CHANGELOG.md; not creating one unless requested
- The `reference/` directory contains third-party repos and should not be distributed

## Expected Outcomes

1. A professional, comprehensive bilingual README that would make the project immediately usable and understandable by new users
2. MIT LICENSE file properly created
3. All installation, configuration, and usage instructions are accurate and tested against the actual codebase
