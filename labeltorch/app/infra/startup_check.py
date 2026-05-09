"""Startup self-check: verify environment, database, CUDA availability"""

import os
import logging
import platform
import sqlite3
from typing import Optional

logger = logging.getLogger(__name__)


class StartupCheck:
    """Perform startup self-checks and report issues"""

    def __init__(self):
        self.results: list = []
        self.warnings: list = []
        self.errors: list = []

    def run_all(self) -> dict:
        """Run all checks, return summary dict"""
        self.results = []
        self.warnings = []
        self.errors = []

        self._check_writable_dir()
        self._check_sqlite()
        self._check_pyside6()
        self._check_pillow()
        self._check_ultralytics()
        self._check_cuda()
        self._check_onnxruntime()

        return {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r["status"] == "pass"),
            "warnings": len(self.warnings),
            "errors": len(self.errors),
            "results": self.results,
        }

    def _add_result(self, name: str, status: str, message: str = ""):
        self.results.append({"name": name, "status": status, "message": message})
        if status == "warning":
            self.warnings.append(f"{name}: {message}")
        elif status == "error":
            self.errors.append(f"{name}: {message}")

    def _check_writable_dir(self):
        """Check if data directory is writable"""
        data_dir = os.path.join(os.path.expanduser("~"), ".labeltorch")
        try:
            os.makedirs(data_dir, exist_ok=True)
            test_file = os.path.join(data_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            self._add_result("Writable Directory", "pass")
        except Exception as e:
            self._add_result("Writable Directory", "error", str(e))

    def _check_sqlite(self):
        """Check SQLite version and WAL support"""
        try:
            version = sqlite3.sqlite_version
            conn = sqlite3.connect(":memory:")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.close()
            self._add_result("SQLite", "pass", f"v{version}")
        except Exception as e:
            self._add_result("SQLite", "error", str(e))

    def _check_pyside6(self):
        """Check PySide6 availability"""
        try:
            import PySide6
            self._add_result("PySide6", "pass", f"v{PySide6.__version__}")
        except ImportError:
            self._add_result("PySide6", "error", "Not installed")

    def _check_pillow(self):
        """Check Pillow availability"""
        try:
            from PIL import Image
            self._add_result("Pillow", "pass")
        except ImportError:
            self._add_result("Pillow", "error", "Not installed")

    def _check_ultralytics(self):
        """Check Ultralytics availability"""
        try:
            import ultralytics
            self._add_result("Ultralytics", "pass", f"v{ultralytics.__version__}")
        except ImportError:
            self._add_result("Ultralytics", "error", "Not installed")

    def _check_cuda(self):
        """Check CUDA availability"""
        try:
            import torch
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                self._add_result("CUDA", "pass", device_name)
            else:
                self._add_result("CUDA", "warning",
                    "CUDA not available - training will use CPU (slower)")
        except ImportError:
            self._add_result("CUDA", "warning", "PyTorch not installed - CPU training only")
        except Exception as e:
            self._add_result("CUDA", "warning", f"Check failed: {e}")

    def _check_onnxruntime(self):
        """Check ONNX Runtime availability"""
        try:
            import onnxruntime
            providers = onnxruntime.get_available_providers()
            self._add_result("ONNX Runtime", "pass", f"providers: {', '.join(providers)}")
        except ImportError:
            self._add_result("ONNX Runtime", "warning", "Not installed - ONNX export verification disabled")

    def get_summary_text(self) -> str:
        """Get human-readable summary"""
        lines = [f"LabelTorch Startup Check ({platform.system()} {platform.release()})", ""]
        for r in self.results:
            icon = {"pass": "[OK]", "warning": "[!!]", "error": "[XX]"}.get(r["status"], "[??]")
            msg = f"  {r['message']}" if r["message"] else ""
            lines.append(f"  {icon} {r['name']}{msg}")

        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")

        if self.errors:
            lines.append("")
            lines.append("Errors:")
            for e in self.errors:
                lines.append(f"  - {e}")

        lines.append("")
        lines.append(f"Total: {len(self.results)} checks, "
                     f"{len(self.errors)} errors, {len(self.warnings)} warnings")
        return "\n".join(lines)
