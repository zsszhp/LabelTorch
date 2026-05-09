"""
标炬（LabelTorch）- 工业缺陷检测桌面工具
入口文件
"""

import sys
import os

# 确保项目根目录在 sys.path 中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from labeltorch.app.ui.main_window import MainWindow
from labeltorch.app.infra.logging.logger import setup_logging


def main():
    """应用主入口"""
    # 初始化日志系统
    setup_logging()

    # 创建 Qt 应用
    app = QApplication(sys.argv)
    app.setApplicationName("标炬 LabelTorch")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("LabelTorch")

    # 高 DPI 支持
    app.setStyle("Fusion")

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
