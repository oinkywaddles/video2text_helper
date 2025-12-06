"""
Video2Text Helper Core Module

核心业务逻辑，与 UI 完全解耦，仅通过回调函数通信。
"""

from .url_cleaner import clean_video_url, extract_video_id, detect_platform
from .transcribe_manager import WhisperModelManager
from .download_manager import DownloadTask
from .subtitle_manager import SubtitleManager
from .task_manager import TaskManager, TaskStatus
from .config import PLATFORM_CONFIG, get_platform_config

__all__ = [
    'clean_video_url',
    'extract_video_id',
    'detect_platform',
    'WhisperModelManager',
    'DownloadTask',
    'SubtitleManager',
    'TaskManager',
    'TaskStatus',
    'PLATFORM_CONFIG',
    'get_platform_config',
]
