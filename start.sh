#!/bin/bash
# LabelTorch startup script (Linux/macOS)

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"

echo "========================================"
echo "  LabelTorch - Industrial Defect Detection Tool"
echo "========================================"
echo ""

# Check dependencies
echo "[1/3] Checking dependencies..."
$PYTHON -c "import PySide6" 2>/dev/null || pip install "PySide6>=6.5" -q
$PYTHON -c "import PIL" 2>/dev/null || pip install Pillow -q
$PYTHON -c "import ultralytics" 2>/dev/null || pip install "ultralytics>=8.0" -q

echo "[2/3] Running startup check..."
cd "$SCRIPT_DIR"
$PYTHON -c "from labeltorch.app.infra.startup_check import StartupCheck; c=StartupCheck(); c.run_all(); print(c.get_summary_text())" 2>/dev/null || true

echo "[3/3] Starting LabelTorch..."
echo ""
$PYTHON -m labeltorch
