"""文件系统操作工具"""

import os
import shutil
import tempfile
from typing import Optional


class FileRepo:
    """文件系统操作封装"""

    @staticmethod
    def ensure_dir(path: str) -> str:
        """确保目录存在"""
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def atomic_write(target_path: str, content: str):
        """
        原子写入文件：先写临时文件再rename替换
        避免写入中途崩溃导致文件损坏
        """
        dir_path = os.path.dirname(target_path)
        os.makedirs(dir_path, exist_ok=True)

        # 在同目录创建临时文件，确保同文件系统，rename是原子操作
        fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            # Windows下需要先删除目标文件
            if os.path.exists(target_path):
                os.replace(tmp_path, target_path)
            else:
                os.rename(tmp_path, target_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    @staticmethod
    def copy_file(src: str, dst: str):
        """复制文件，确保目标目录存在"""
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    @staticmethod
    def list_files(directory: str, extensions: Optional[list] = None) -> list:
        """列出目录下的文件，可按扩展名过滤"""
        if not os.path.isdir(directory):
            return []
        files = []
        for f in os.listdir(directory):
            full_path = os.path.join(directory, f)
            if os.path.isfile(full_path):
                if extensions is None or os.path.splitext(f)[1].lower() in extensions:
                    files.append(full_path)
        return sorted(files)

    @staticmethod
    def delete_path(path: str):
        """删除文件或目录"""
        if os.path.isfile(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
