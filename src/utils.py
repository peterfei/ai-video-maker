"""
工具函数模块
提供通用的工具函数
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import colorlog


def setup_logger(name: str = "video_factory", level: str = "INFO") -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        Logger对象
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    if not logger.handlers:
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        ))
        logger.addHandler(handler)

    return logger


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 替换空格为下划线
    filename = filename.replace(' ', '_')
    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def generate_filename(title: str, pattern: str = "{title}_{timestamp}", ext: str = "mp4") -> str:
    """
    生成文件名

    Args:
        title: 标题
        pattern: 文件名模式
        ext: 文件扩展名

    Returns:
        生成的文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = pattern.format(
        title=sanitize_filename(title),
        timestamp=timestamp
    )
    return f"{filename}.{ext}"


def ensure_dir(path: Path) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        目录路径
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_files_by_extension(directory: Path, extensions: List[str]) -> List[Path]:
    """
    获取目录下指定扩展名的所有文件

    Args:
        directory: 目录路径
        extensions: 扩展名列表，如 ['.jpg', '.png']

    Returns:
        文件路径列表
    """
    directory = Path(directory)
    files = []

    if not directory.exists():
        return files

    for ext in extensions:
        files.extend(directory.glob(f"*{ext}"))
        files.extend(directory.glob(f"*{ext.upper()}"))

    return sorted(files)


def format_duration(seconds: float) -> str:
    """
    格式化时长为可读字符串

    Args:
        seconds: 秒数

    Returns:
        格式化的时长字符串，如 "1:23:45"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def split_text_by_length(text: str, max_chars: int) -> List[str]:
    """
    按长度分割文本为多行

    Args:
        text: 原始文本
        max_chars: 每行最大字符数

    Returns:
        分割后的文本列表
    """
    lines = []
    words = text.split()
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line += word + " "
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "

    if current_line:
        lines.append(current_line.strip())

    return lines


def parse_time_string(time_str: str) -> float:
    """
    解析时间字符串为秒数

    Args:
        time_str: 时间字符串，支持 "1:23:45" 或 "83.5"

    Returns:
        秒数
    """
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    else:
        return float(time_str)


def get_file_size(file_path: Path) -> str:
    """
    获取文件大小的可读字符串

    Args:
        file_path: 文件路径

    Returns:
        文件大小字符串，如 "1.23 MB"
    """
    size = file_path.stat().st_size
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, total: int, desc: str = "Processing"):
        """
        初始化进度跟踪器

        Args:
            total: 总数
            desc: 描述
        """
        from tqdm import tqdm
        self.pbar = tqdm(total=total, desc=desc)

    def update(self, n: int = 1):
        """更新进度"""
        self.pbar.update(n)

    def close(self):
        """关闭进度条"""
        self.pbar.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
