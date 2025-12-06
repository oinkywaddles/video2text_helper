"""
字幕管理器

核心功能：
- 解析 VTT/SRT 格式字幕
- 转换为纯文本或带时间戳格式
- 清理和规范化字幕内容
"""

import re
import os
from typing import Optional, List, Dict, Callable


class SubtitleManager:
    """
    字幕解析和处理类

    支持：
    - VTT 格式（WebVTT）
    - SRT 格式
    - 自动检测格式
    - 多种编码支持
    """

    # 支持的编码列表
    ENCODINGS = ['utf-8', 'utf-8-sig', 'gb2312', 'gbk', 'gb18030', 'latin-1']

    def __init__(self, file_path: Optional[str] = None):
        """
        初始化字幕管理器

        Args:
            file_path: 字幕文件路径（可选，也可以后续通过 load 方法加载）
        """
        self.file_path = file_path
        self._content: Optional[str] = None
        self._segments: List[Dict] = []
        self._format: Optional[str] = None

        if file_path:
            self.load(file_path)

    @property
    def is_loaded(self) -> bool:
        """是否已加载字幕"""
        return self._content is not None

    @property
    def segment_count(self) -> int:
        """字幕片段数量"""
        return len(self._segments)

    @property
    def format(self) -> Optional[str]:
        """字幕格式 ('vtt', 'srt', 'unknown')"""
        return self._format

    def load(
        self,
        file_path: str,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        加载字幕文件

        Args:
            file_path: 字幕文件路径
            log_callback: 日志回调

        Returns:
            是否成功加载
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        if not os.path.exists(file_path):
            log(f"[错误] 字幕文件不存在: {file_path}")
            return False

        self.file_path = file_path

        # 检测文件大小
        file_size = os.path.getsize(file_path)
        if file_size < 10:
            log(f"[警告] 字幕文件过小 ({file_size} bytes)")
            return False

        # 尝试多种编码读取
        self._content = self._read_with_encoding(file_path, log_callback)
        if not self._content:
            log("[错误] 无法读取字幕文件")
            return False

        # 检测格式并解析
        self._detect_and_parse(log_callback)

        if not self._segments:
            log("[警告] 未能解析出任何字幕内容")
            return False

        log(f"[字幕] 解析完成: {len(self._segments)} 个片段")
        return True

    def _read_with_encoding(
        self,
        file_path: str,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """尝试多种编码读取文件"""
        for encoding in self.ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        return None

    def _detect_and_parse(
        self,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """检测格式并解析"""
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        if not self._content:
            return

        content = self._content.strip()

        if content.startswith('WEBVTT'):
            self._format = 'vtt'
            log("[字幕] 检测到 VTT 格式")
            self._segments = self._parse_vtt(content)
        elif re.search(r'^\d+\s*$', content.split('\n')[0]):
            self._format = 'srt'
            log("[字幕] 检测到 SRT 格式")
            self._segments = self._parse_srt(content)
        else:
            self._format = 'unknown'
            log("[字幕] 未知格式，尝试通用解析")
            self._segments = self._parse_generic(content)

    def _parse_vtt(self, content: str) -> List[Dict]:
        """解析 VTT 格式"""
        segments = []
        lines = content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 跳过空行、头部、注释
            if not line or line.startswith('WEBVTT') or line.startswith('NOTE'):
                i += 1
                continue

            # 检测时间戳行
            if '-->' in line:
                timestamp_match = re.match(r'([\d:.]+)\s*-->\s*([\d:.]+)', line)

                if timestamp_match:
                    start_str = timestamp_match.group(1).strip()
                    end_str = timestamp_match.group(2).strip()

                    # 提取文本（可能多行）
                    i += 1
                    text_lines = []
                    while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                        text_lines.append(lines[i].strip())
                        i += 1

                    if text_lines:
                        text = ' '.join(text_lines)
                        segments.append({
                            'start': self._parse_timestamp(start_str),
                            'end': self._parse_timestamp(end_str),
                            'text': text
                        })
                else:
                    i += 1
            else:
                i += 1

        return segments

    def _parse_srt(self, content: str) -> List[Dict]:
        """解析 SRT 格式"""
        segments = []

        # 按空行分割字幕块
        blocks = re.split(r'\n\s*\n', content)

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue

            # 查找时间戳行
            timestamp_line = None
            text_lines = []

            for i, line in enumerate(lines):
                if '-->' in line:
                    timestamp_line = line
                    text_lines = lines[i+1:]
                    break

            if not timestamp_line or not text_lines:
                continue

            # 解析时间戳
            timestamp_match = re.match(r'([\d:,]+)\s*-->\s*([\d:,]+)', timestamp_line)

            if timestamp_match:
                start_str = timestamp_match.group(1).strip().replace(',', '.')
                end_str = timestamp_match.group(2).strip().replace(',', '.')

                text = ' '.join(line.strip() for line in text_lines if line.strip())
                if text:
                    segments.append({
                        'start': self._parse_timestamp(start_str),
                        'end': self._parse_timestamp(end_str),
                        'text': text
                    })

        return segments

    def _parse_generic(self, content: str) -> List[Dict]:
        """通用解析（后备方案）"""
        segments = []
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            # 跳过空行、时间戳、序号
            if (not line or
                '-->' in line or
                re.match(r'^\d+$', line) or
                line.startswith('WEBVTT') or
                line.startswith('NOTE')):
                continue

            if len(line) > 2:
                segments.append({
                    'start': 0.0,
                    'end': 0.0,
                    'text': line
                })

        return segments

    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> float:
        """将时间戳字符串转换为秒数"""
        timestamp_str = timestamp_str.strip()
        parts = timestamp_str.split(':')

        try:
            if len(parts) == 3:
                # HH:MM:SS.mmm
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                # MM:SS.mmm
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                # SS.mmm
                return float(parts[0])
        except (ValueError, IndexError):
            return 0.0

    def to_text(
        self,
        with_timestamps: bool = False,
        paragraph_gap: float = 5.0
    ) -> str:
        """
        转换为纯文本

        Args:
            with_timestamps: 是否包含时间戳
            paragraph_gap: 间隔超过此秒数时添加段落分隔

        Returns:
            纯文本字符串
        """
        if not self._segments:
            return ""

        # 清理 HTML 标签和说话人标签
        cleaned_segments = []
        for seg in self._segments:
            text = seg['text']

            # 移除 HTML 标签
            text = re.sub(r'<[^>]+>', '', text)

            # 移除说话人标签
            text = re.sub(r'^\[.*?\]:\s*', '', text)
            text = re.sub(r'^【.*?】：\s*', '', text)

            # 移除 HTML 实体
            text = text.replace('&nbsp;', ' ')
            text = text.replace('&amp;', '&')
            text = text.replace('&lt;', '<')
            text = text.replace('&gt;', '>')
            text = text.replace('&quot;', '"')

            text = text.strip()
            if text:
                cleaned_segments.append({
                    'start': seg['start'],
                    'end': seg['end'],
                    'text': text
                })

        # 去重
        deduped_segments = []
        prev_text = None
        for seg in cleaned_segments:
            if seg['text'] != prev_text:
                deduped_segments.append(seg)
                prev_text = seg['text']

        # 构建结果
        result_lines = []
        prev_end = 0.0

        for seg in deduped_segments:
            gap = seg['start'] - prev_end

            # 段落分隔
            if gap > paragraph_gap and result_lines:
                result_lines.append('')

            if with_timestamps:
                start_str = self._format_timestamp_for_text(seg['start'])
                end_str = self._format_timestamp_for_text(seg['end'])
                result_lines.append(f"[{start_str} -> {end_str}] {seg['text']}")
            else:
                result_lines.append(seg['text'])

            prev_end = seg['end']

        # 合并并规范化
        text = '\n'.join(result_lines)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def to_srt(self) -> str:
        """转换为 SRT 格式"""
        if not self._segments:
            return ""

        lines = []
        for i, seg in enumerate(self._segments, 1):
            start_str = self._format_timestamp_srt(seg['start'])
            end_str = self._format_timestamp_srt(seg['end'])
            lines.append(f"{i}")
            lines.append(f"{start_str} --> {end_str}")
            lines.append(seg['text'])
            lines.append("")

        return '\n'.join(lines)

    def to_vtt(self) -> str:
        """转换为 VTT 格式"""
        if not self._segments:
            return "WEBVTT\n\n"

        lines = ["WEBVTT", ""]
        for seg in self._segments:
            start_str = self._format_timestamp_vtt(seg['start'])
            end_str = self._format_timestamp_vtt(seg['end'])
            lines.append(f"{start_str} --> {end_str}")
            lines.append(seg['text'])
            lines.append("")

        return '\n'.join(lines)

    @staticmethod
    def _format_timestamp_for_text(seconds: float) -> str:
        """格式化时间戳（用于文本输出）"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    @staticmethod
    def _format_timestamp_srt(seconds: float) -> str:
        """格式化时间戳（SRT 格式，使用逗号）"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_timestamp_vtt(seconds: float) -> str:
        """格式化时间戳（VTT 格式，使用点）"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

    def save(
        self,
        output_path: str,
        output_format: str = "text",
        with_timestamps: bool = False,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        保存字幕内容到文件

        Args:
            output_path: 输出文件路径
            output_format: 输出格式 ('text', 'srt', 'vtt')
            with_timestamps: 文本格式时是否包含时间戳
            log_callback: 日志回调

        Returns:
            是否成功保存
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        if output_format == "srt":
            content = self.to_srt()
        elif output_format == "vtt":
            content = self.to_vtt()
        else:
            content = self.to_text(with_timestamps=with_timestamps)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            log(f"[保存] 已保存: {output_path}")
            return True
        except Exception as e:
            log(f"[错误] 保存失败: {e}")
            return False
