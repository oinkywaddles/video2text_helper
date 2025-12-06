"""
Whisper 模型管理器

核心特性：
- 热启动：避免重复加载相同模型
- 进度回调：实时报告转录进度
- 支持多种输出格式
"""

import os
import time
from typing import Optional, Callable, Generator, Any
from faster_whisper import WhisperModel


# 模型大小映射（用于显示）
MODEL_SIZES = {
    'tiny': {'name': 'Tiny', 'desc': '最快，精度一般', 'size_mb': 75},
    'base': {'name': 'Base', 'desc': '速度快，精度一般', 'size_mb': 145},
    'small': {'name': 'Small', 'desc': '平衡速度与精度', 'size_mb': 466},
    'medium': {'name': 'Medium', 'desc': '推荐，精度较高', 'size_mb': 1500},
    'large-v3': {'name': 'Large-v3', 'desc': '最高精度，较慢', 'size_mb': 3000},
}


class WhisperModelManager:
    """
    Whisper 模型管理器（单例模式思路，但不强制）

    支持热启动：如果请求的模型与当前加载的模型相同，直接复用。
    """

    def __init__(self):
        self._model: Optional[WhisperModel] = None
        self._current_model_size: Optional[str] = None
        self._current_device: Optional[str] = None
        self._current_compute_type: Optional[str] = None

    @property
    def is_loaded(self) -> bool:
        """模型是否已加载"""
        return self._model is not None

    @property
    def current_model_info(self) -> dict:
        """当前加载的模型信息"""
        if not self.is_loaded:
            return {'loaded': False}
        return {
            'loaded': True,
            'model_size': self._current_model_size,
            'device': self._current_device,
            'compute_type': self._current_compute_type,
        }

    def load_model(
        self,
        model_size: str = "medium",
        device: str = "auto",
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        加载 Whisper 模型（支持热启动）

        Args:
            model_size: 模型大小 ('tiny', 'base', 'small', 'medium', 'large-v3')
            device: 设备 ('auto', 'cpu', 'cuda')
            log_callback: 日志回调函数

        Returns:
            是否成功加载
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        # 自动检测设备
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        # 根据设备选择计算精度
        compute_type = "float16" if device == "cuda" else "int8"

        # 热启动检查：如果模型已加载且参数相同，直接复用
        if (self._model is not None and
            self._current_model_size == model_size and
            self._current_device == device):
            log(f"[热启动] 复用已加载的模型: {model_size} ({device})")
            return True

        # 需要加载新模型
        log(f"[模型] 正在加载: {model_size}")
        log(f"[设备] {device} (精度: {compute_type})")

        # 如果有旧模型，先释放
        if self._model is not None:
            log(f"[模型] 释放旧模型: {self._current_model_size}")
            self._model = None

        start_time = time.time()

        try:
            self._model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )
            self._current_model_size = model_size
            self._current_device = device
            self._current_compute_type = compute_type

            load_time = time.time() - start_time
            log(f"[模型] 加载完成 (耗时: {load_time:.2f}s)")
            return True

        except Exception as e:
            log(f"[错误] 模型加载失败: {e}")
            self._model = None
            self._current_model_size = None
            return False

    def unload_model(self, log_callback: Optional[Callable[[str], None]] = None):
        """
        释放模型，释放内存

        Args:
            log_callback: 日志回调函数
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        if self._model is not None:
            log(f"[模型] 释放: {self._current_model_size}")
            self._model = None
            self._current_model_size = None
            self._current_device = None
            self._current_compute_type = None

    def transcribe(
        self,
        audio_path: str,
        model_size: str = "medium",
        device: str = "auto",
        language: Optional[str] = None,
        output_format: str = "text",
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Optional[str]:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            model_size: 模型大小
            device: 设备
            language: 语言代码 (None=自动检测, 'zh', 'en', etc.)
            output_format: 输出格式 ('text', 'srt', 'vtt')
            log_callback: 日志回调 fn(msg: str)
            progress_callback: 进度回调 fn(current: int, total: int)

        Returns:
            转录文本，失败返回 None
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        def progress(current: int, total: int):
            if progress_callback:
                progress_callback(current, total)

        # 检查文件
        if not os.path.exists(audio_path):
            log(f"[错误] 音频文件不存在: {audio_path}")
            return None

        file_size = os.path.getsize(audio_path) / 1024 / 1024
        log(f"[文件] {os.path.basename(audio_path)} ({file_size:.2f} MB)")

        # 加载模型（支持热启动）
        if not self.load_model(model_size, device, log_callback):
            return None

        log("[转录] 开始...")
        start_time = time.time()

        try:
            # 转录音频
            segments_generator, info = self._model.transcribe(
                audio_path,
                beam_size=5,
                language=language,
                task="transcribe"
            )

            log(f"[语言] 检测到: {info.language} (置信度: {info.language_probability:.2%})")

            results = []
            segment_count = 0
            last_end_time = 0.0

            # 处理每个片段
            for segment in segments_generator:
                segment_count += 1
                last_end_time = segment.end

                # 格式化时间戳
                start_str = self._format_timestamp(segment.start, output_format)
                end_str = self._format_timestamp(segment.end, output_format)

                # 根据输出格式生成文本
                if output_format == "srt":
                    line = f"{segment_count}\n{start_str} --> {end_str}\n{segment.text.strip()}\n"
                elif output_format == "vtt":
                    line = f"{start_str} --> {end_str}\n{segment.text.strip()}\n"
                else:
                    line = f"[{start_str} -> {end_str}] {segment.text.strip()}"

                results.append(line)

                # 进度回调（每 5 个片段更新一次）
                if segment_count % 5 == 0:
                    # 估算总片段数（基于音频时长）
                    estimated_total = max(segment_count, int(last_end_time / 3))
                    progress(segment_count, estimated_total)
                    log(f"[进度] 已处理 {segment_count} 个片段...")

            # 计算统计信息
            elapsed_time = time.time() - start_time
            speed_ratio = last_end_time / elapsed_time if elapsed_time > 0 else 0

            log(f"[完成] 总片段: {segment_count}")
            log(f"[完成] 音频时长: {self._format_duration(last_end_time)}")
            log(f"[完成] 转录耗时: {self._format_duration(elapsed_time)}")
            log(f"[完成] 处理速度: {speed_ratio:.2f}x")

            # 最终进度
            progress(segment_count, segment_count)

            # 组合结果
            if output_format == "srt":
                return "\n".join(results)
            elif output_format == "vtt":
                return "WEBVTT\n\n" + "\n".join(results)
            else:
                return "\n".join(results)

        except Exception as e:
            log(f"[错误] 转录失败: {e}")
            return None

    @staticmethod
    def _format_timestamp(seconds: float, output_format: str = "text") -> str:
        """格式化时间戳"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        if output_format == "srt":
            # SRT 使用逗号
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        else:
            # VTT 和普通文本使用点
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}小时{minutes}分"

    @staticmethod
    def get_available_models() -> dict:
        """获取可用模型列表"""
        return MODEL_SIZES.copy()


# 全局单例（可选使用）
_global_manager: Optional[WhisperModelManager] = None


def get_global_manager() -> WhisperModelManager:
    """获取全局模型管理器实例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = WhisperModelManager()
    return _global_manager
