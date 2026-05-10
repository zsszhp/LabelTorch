# Open-Source README Documentation — Summary

## Completed Tasks

### Task 1: MIT LICENSE File
- Created `LICENSE` file with standard MIT license text
- Copyright holder: "LabelTorch Team" (consistent with `pyproject.toml`)
- Year: 2025

### Task 2: Bilingual README.md
Replaced the minimal 89-line README with a comprehensive bilingual document (~600 lines) covering:

**English Section:**
- Header with badges (Python, License, Ultralytics, PySide6)
- Feature list (9 key features with descriptions)
- ASCII architecture diagram (4-layer: UI → Services → Domain → Infrastructure)
- Tech stack table
- Getting Started (3 install methods: source, pip, conda + optional export dependency)
- Configuration (data directory structure, startup self-check table, CUDA setup)
- Usage workflow with step-by-step guide (7 steps: Project → Dataset → Validate → Annotate → Train → Assisted → Export)
- Development (test commands, detailed project structure, contribution guidelines)
- Building (PyInstaller packaging instructions)
- FAQ (6 common issues with solutions)
- Roadmap (6 planned features)
- Acknowledgments (5 reference projects)

**Chinese Section (中文):**
- Complete translation of all English sections
- Technical terms kept in English where conventional (YOLO, SQLite, ONNX, etc.)
- Section anchors adjusted for Chinese navigation

## Key Design Decisions
- English first, then Chinese — follows the convention for projects targeting both international and Chinese audiences
- Badges use shields.io — standard open-source practice
- `start.bat` and `build_release.bat` hardcoded paths flagged with warnings
- No screenshots section — project has none yet, omitted rather than using empty placeholder
- FAQ covers the most likely user pain points (CUDA, ONNX, Linux Qt, hardcoded paths)
- Architecture diagram uses ASCII art — no external image dependencies
