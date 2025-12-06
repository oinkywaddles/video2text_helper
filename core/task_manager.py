"""
任务管理器

核心功能：
- 整合完整工作流
- 字幕优先策略（字幕不存在时使用 Whisper）
- 进度和日志回调
- 支持取消操作
"""

import os
import threading
import traceback
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from enum import Enum

from .url_cleaner import clean_video_url, detect_platform
from .download_manager import DownloadTask
from .subtitle_manager import SubtitleManager
from .transcribe_manager import WhisperModelManager, get_global_manager


class TaskStatus(Enum):
    """任务状态"""
    IDLE = "idle"
    FETCHING_INFO = "fetching_info"
    CHECKING_SUBTITLE = "checking_subtitle"
    DOWNLOADING_SUBTITLE = "downloading_subtitle"
    DOWNLOADING_AUDIO = "downloading_audio"
    TRANSCRIBING = "transcribing"
    PARSING_SUBTITLE = "parsing_subtitle"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class TaskManager:
    """
    任务管理器

    工作流程：
    1. 获取视频信息
    2. 检查字幕可用性
    3. 如果有字幕：下载并解析字幕
    4. 如果没有字幕：下载音频，使用 Whisper 转录
    5. 输出结果
    """

    def __init__(
        self,
        whisper_manager: Optional[WhisperModelManager] = None
    ):
        """
        初始化任务管理器

        Args:
            whisper_manager: Whisper 模型管理器（可选，不传则使用全局单例）
        """
        self._whisper_manager = whisper_manager or get_global_manager()
        self._current_task: Optional[DownloadTask] = None
        self._status = TaskStatus.IDLE
        self._cancelled = False
        self._thread: Optional[threading.Thread] = None

        # 回调函数
        self._log_callback: Optional[Callable[[str], None]] = None
        self._progress_callback: Optional[Callable[[float, str], None]] = None
        self._status_callback: Optional[Callable[[TaskStatus], None]] = None
        self._complete_callback: Optional[Callable[[bool, Optional[str], Optional[str]], None]] = None

    @property
    def status(self) -> TaskStatus:
        """当前任务状态"""
        return self._status

    @property
    def is_running(self) -> bool:
        """是否有任务正在运行"""
        return self._status not in [TaskStatus.IDLE, TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.ERROR]

    def set_callbacks(
        self,
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        status_callback: Optional[Callable[[TaskStatus], None]] = None,
        complete_callback: Optional[Callable[[bool, Optional[str], Optional[str]], None]] = None
    ):
        """
        设置回调函数

        Args:
            log_callback: 日志回调 fn(msg: str)
            progress_callback: 进度回调 fn(percent: float, stage: str)
            status_callback: 状态回调 fn(status: TaskStatus)
            complete_callback: 完成回调 fn(success: bool, output_path: Optional[str], error: Optional[str])
        """
        self._log_callback = log_callback
        self._progress_callback = progress_callback
        self._status_callback = status_callback
        self._complete_callback = complete_callback

    def _log(self, msg: str):
        """日志"""
        if self._log_callback:
            self._log_callback(msg)

    def _progress(self, percent: float, stage: str):
        """进度"""
        if self._progress_callback:
            self._progress_callback(percent, stage)

    def _set_status(self, status: TaskStatus):
        """设置状态"""
        old_status = self._status
        self._status = status
        if old_status != status:
            self._log(f"[状态] {old_status.value} → {status.value}")
        if self._status_callback:
            self._status_callback(status)

    def _complete(self, success: bool, output_path: Optional[str] = None, error: Optional[str] = None):
        """完成"""
        if self._complete_callback:
            self._complete_callback(success, output_path, error)

    def start(
        self,
        url: str,
        output_dir: str = "downloads",
        use_cookies: bool = True,
        proxy: Optional[str] = None,
        subtitle_language: Optional[str] = None,
        force_whisper: bool = False,
        model_size: str = "medium",
        output_format: str = "text",
        with_timestamps: bool = False
    ):
        """
        启动任务（异步）

        Args:
            url: 视频链接
            output_dir: 输出目录
            use_cookies: 是否使用浏览器 cookies
            proxy: 代理地址
            subtitle_language: 指定字幕语言（None=自动选择）
            force_whisper: 强制使用 Whisper（跳过字幕检查）
            model_size: Whisper 模型大小
            output_format: 输出格式 ('text', 'srt', 'vtt')
            with_timestamps: 文本格式时是否包含时间戳
        """
        if self.is_running:
            self._log("[错误] 已有任务正在运行")
            return

        self._cancelled = False
        self._set_status(TaskStatus.IDLE)

        # 在新线程中运行任务
        self._thread = threading.Thread(
            target=self._run_task,
            args=(url, output_dir, use_cookies, proxy, subtitle_language,
                  force_whisper, model_size, output_format, with_timestamps),
            daemon=True
        )
        self._thread.start()

    def _run_task(
        self,
        url: str,
        output_dir: str,
        use_cookies: bool,
        proxy: Optional[str],
        subtitle_language: Optional[str],
        force_whisper: bool,
        model_size: str,
        output_format: str,
        with_timestamps: bool
    ):
        """任务主逻辑（在线程中运行）"""
        try:
            # 清理 URL
            clean_url = clean_video_url(url)
            platform = detect_platform(url)
            self._log(f"[任务] 平台: {platform}")
            self._log(f"[任务] URL: {clean_url}")

            # 创建下载任务（临时目录，后续会更新）
            self._current_task = DownloadTask(
                url=clean_url,
                output_dir=output_dir,
                use_cookies=use_cookies,
                proxy=proxy
            )

            # Step 1: 获取视频信息
            self._set_status(TaskStatus.FETCHING_INFO)
            self._progress(5, "获取视频信息")

            video_info = self._current_task.get_video_info(log_callback=self._log)

            if self._cancelled:
                self._set_status(TaskStatus.CANCELLED)
                self._complete(False, error="任务已取消")
                return

            if not video_info:
                self._set_status(TaskStatus.ERROR)
                self._complete(False, error="无法获取视频信息")
                return

            video_title = video_info['title']
            # 清理文件名中的非法字符
            safe_title = self._sanitize_filename(video_title)
            if safe_title != video_title:
                self._log(f"[任务] 文件名清理: {video_title} → {safe_title}")

            # 创建输出文件夹: {title}_transcript_YYMMDD-HHMM
            task_folder = self._create_output_folder(output_dir, safe_title)
            intermediate_dir = os.path.join(task_folder, "intermediate")
            os.makedirs(intermediate_dir, exist_ok=True)

            # 更新下载任务的输出目录为 intermediate
            self._current_task.output_dir = intermediate_dir
            self._log(f"[任务] 输出目录: {task_folder}")
            self._log(f"[任务] 中间文件: {intermediate_dir}")

            # Step 2: 检查字幕并决定策略
            has_subtitle = False
            subtitle_result = None

            if not force_whisper:
                self._set_status(TaskStatus.CHECKING_SUBTITLE)
                self._progress(10, "检查字幕")

                manual_subs = video_info['subtitles']['manual']
                auto_subs = video_info['subtitles']['auto']
                has_subtitle = bool(manual_subs or auto_subs)

                if has_subtitle:
                    self._log("[策略] 检测到字幕，使用字幕优先策略")

                    # Step 3a: 下载字幕
                    self._set_status(TaskStatus.DOWNLOADING_SUBTITLE)
                    self._progress(20, "下载字幕")

                    subtitle_result = self._current_task.download_subtitle(
                        language=subtitle_language,
                        log_callback=self._log
                    )

                    if self._cancelled:
                        self._set_status(TaskStatus.CANCELLED)
                        self._complete(False, error="任务已取消")
                        return

                    if subtitle_result:
                        # Step 4a: 解析字幕
                        self._set_status(TaskStatus.PARSING_SUBTITLE)
                        self._progress(60, "解析字幕")

                        subtitle_manager = SubtitleManager()
                        if subtitle_manager.load(subtitle_result['file_path'], log_callback=self._log):
                            # 生成输出文件（放到 task_folder 根目录）
                            ext = 'srt' if output_format == 'srt' else 'vtt' if output_format == 'vtt' else 'txt'
                            output_path = os.path.join(task_folder, f"{safe_title}.{ext}")

                            self._progress(80, "保存结果")

                            if subtitle_manager.save(
                                output_path,
                                output_format=output_format,
                                with_timestamps=with_timestamps,
                                log_callback=self._log
                            ):
                                self._progress(100, "完成")
                                self._set_status(TaskStatus.COMPLETED)
                                self._log(f"[完成] 输出文件: {output_path}")
                                self._complete(True, output_path)
                                return
                    else:
                        self._log("[警告] 字幕下载失败，回退到 Whisper")
                else:
                    self._log("[策略] 没有可用字幕，使用 Whisper 转录")

            # Step 3b/4b: Whisper 转录流程
            # 下载音频
            self._set_status(TaskStatus.DOWNLOADING_AUDIO)
            self._progress(20, "下载音频")

            def download_progress(percent: float):
                # 下载进度映射到 20-50%
                mapped = 20 + (percent * 0.3)
                self._progress(mapped, "下载音频")

            audio_path = self._current_task.download_audio(
                log_callback=self._log,
                progress_callback=download_progress
            )

            if self._cancelled:
                self._set_status(TaskStatus.CANCELLED)
                self._complete(False, error="任务已取消")
                return

            if not audio_path:
                self._set_status(TaskStatus.ERROR)
                self._complete(False, error="音频下载失败")
                return

            # 转录
            self._set_status(TaskStatus.TRANSCRIBING)
            self._progress(55, "转录中")

            def transcribe_progress(current: int, total: int):
                # 转录进度映射到 55-95%
                if total > 0:
                    percent = (current / total)
                    mapped = 55 + (percent * 40)
                    self._progress(mapped, "转录中")

            result = self._whisper_manager.transcribe(
                audio_path=audio_path,
                model_size=model_size,
                language=None,  # 自动检测
                output_format=output_format,
                log_callback=self._log,
                progress_callback=transcribe_progress
            )

            if self._cancelled:
                self._set_status(TaskStatus.CANCELLED)
                self._complete(False, error="任务已取消")
                return

            if not result:
                self._set_status(TaskStatus.ERROR)
                self._complete(False, error="转录失败")
                return

            # 保存结果（放到 task_folder 根目录）
            self._progress(95, "保存结果")

            ext = 'srt' if output_format == 'srt' else 'vtt' if output_format == 'vtt' else 'txt'
            output_path = os.path.join(task_folder, f"{safe_title}.{ext}")

            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                self._log(f"[保存] 已保存: {output_path}")
            except Exception as e:
                self._set_status(TaskStatus.ERROR)
                self._complete(False, error=f"保存失败: {e}")
                return

            # 完成
            self._progress(100, "完成")
            self._set_status(TaskStatus.COMPLETED)
            self._log(f"[完成] 输出文件: {output_path}")
            self._complete(True, output_path)

        except Exception as e:
            self._set_status(TaskStatus.ERROR)
            self._log(f"[错误] 任务失败: {e}")
            self._log(f"[错误] 详细信息:\n{traceback.format_exc()}")
            self._complete(False, error=str(e))

    def cancel(self):
        """取消当前任务"""
        self._cancelled = True
        if self._current_task:
            self._current_task.cancel()
        self._log("[取消] 正在取消任务...")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """清理文件名中的非法字符"""
        # 替换非法字符
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in illegal_chars:
            filename = filename.replace(char, '_')

        # 移除前后空格
        filename = filename.strip()

        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]

        return filename or "video"

    @staticmethod
    def _create_output_folder(base_dir: str, title: str) -> str:
        """
        创建带时间戳的输出文件夹

        格式: {title}_transcript_YYMMDD-HHMM
        重复时添加 _1, _2 等后缀

        Args:
            base_dir: 基础目录 (如 downloads/)
            title: 视频标题（已清理）

        Returns:
            创建的文件夹绝对路径
        """
        # 生成时间戳
        timestamp = datetime.now().strftime("%y%m%d-%H%M")
        folder_name = f"{title}_transcript_{timestamp}"

        # 检查重复并添加后缀
        folder_path = os.path.join(base_dir, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            return os.path.abspath(folder_path)

        # 有重复，添加后缀
        suffix = 1
        while True:
            folder_path_with_suffix = os.path.join(base_dir, f"{folder_name}_{suffix}")
            if not os.path.exists(folder_path_with_suffix):
                os.makedirs(folder_path_with_suffix)
                return os.path.abspath(folder_path_with_suffix)
            suffix += 1
