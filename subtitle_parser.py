#!/usr/bin/env python3
"""
字幕解析模块

支持解析 VTT 和 SRT 格式的字幕文件，转换为纯文本。
"""

import re
import os
from typing import List, Dict, Optional


def parse_subtitle_file(file_path: str) -> Optional[str]:
    """
    解析字幕文件（自动检测格式）

    Args:
        file_path: 字幕文件路径（.vtt 或 .srt）

    Returns:
        纯文本内容，失败返回 None
    """
    if not os.path.exists(file_path):
        print(f"❌ 字幕文件不存在: {file_path}")
        return None

    # 检测文件编码并读取
    content = read_with_encoding(file_path)
    if not content:
        print(f"❌ 无法读取字幕文件: {file_path}")
        return None

    # 检测文件大小
    file_size = os.path.getsize(file_path)
    if file_size < 10:
        print(f"⚠️ 字幕文件过小 ({file_size} bytes)，可能为空")
        return None

    # 根据内容判断格式
    if content.strip().startswith('WEBVTT'):
        print("📝 检测到 VTT 格式")
        segments = parse_vtt(content)
    elif re.search(r'^\d+\s*$', content.strip().split('\n')[0]):
        print("📝 检测到 SRT 格式")
        segments = parse_srt(content)
    else:
        print("⚠️ 未知字幕格式，尝试通用解析")
        segments = parse_generic(content)

    if not segments:
        print("⚠️ 未能解析出任何字幕内容")
        return None

    # 清理并合并文本
    text = clean_subtitle_text(segments)

    print(f"✅ 解析完成: {len(segments)} 个片段，{len(text)} 字符")
    return text


def read_with_encoding(file_path: str) -> Optional[str]:
    """
    尝试多种编码读取文件

    Args:
        file_path: 文件路径

    Returns:
        文件内容，失败返回 None
    """
    encodings = ['utf-8', 'utf-8-sig', 'gb2312', 'gbk', 'gb18030']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue

    # 最后尝试 latin-1（几乎总能成功，但可能乱码）
    try:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return None


def parse_vtt(content: str) -> List[Dict]:
    """
    解析 VTT 格式字幕

    VTT 格式:
        WEBVTT

        00:00:00.000 --> 00:00:02.500
        字幕文本

    Args:
        content: VTT 文件内容

    Returns:
        [{'start': 0.0, 'end': 2.5, 'text': '字幕文本'}, ...]
    """
    segments = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 跳过空行、WEBVTT 头、NOTE 等
        if not line or line.startswith('WEBVTT') or line.startswith('NOTE'):
            i += 1
            continue

        # 检测时间戳行：00:00:00.000 --> 00:00:02.500
        if '-->' in line:
            # 解析时间戳
            timestamp_match = re.match(
                r'([\d:.]+ +)--> +([\d:.]+)',
                line
            )

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
                        'start': parse_timestamp(start_str),
                        'end': parse_timestamp(end_str),
                        'text': text
                    })
            else:
                i += 1
        else:
            i += 1

    return segments


def parse_srt(content: str) -> List[Dict]:
    """
    解析 SRT 格式字幕

    SRT 格式:
        1
        00:00:00,000 --> 00:00:02,500
        字幕文本

    Args:
        content: SRT 文件内容

    Returns:
        [{'start': 0.0, 'end': 2.5, 'text': '字幕文本'}, ...]
    """
    segments = []

    # 按空行分割字幕块
    blocks = re.split(r'\n\s*\n', content)

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue

        # 第一行应该是序号（跳过）
        # 第二行应该是时间戳
        timestamp_line = None
        text_lines = []

        for i, line in enumerate(lines):
            if '-->' in line:
                timestamp_line = line
                # 时间戳后面的都是文本
                text_lines = lines[i+1:]
                break

        if not timestamp_line or not text_lines:
            continue

        # 解析时间戳 (SRT 使用逗号)
        timestamp_match = re.match(
            r'([\d:,]+)\s+-->\s+([\d:,]+)',
            timestamp_line
        )

        if timestamp_match:
            start_str = timestamp_match.group(1).strip().replace(',', '.')
            end_str = timestamp_match.group(2).strip().replace(',', '.')

            text = ' '.join(line.strip() for line in text_lines if line.strip())
            if text:
                segments.append({
                    'start': parse_timestamp(start_str),
                    'end': parse_timestamp(end_str),
                    'text': text
                })

    return segments


def parse_generic(content: str) -> List[Dict]:
    """
    通用字幕解析（作为后备）

    Args:
        content: 字幕内容

    Returns:
        [{'start': 0.0, 'end': 0.0, 'text': '...'}, ...]
    """
    segments = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        # 跳过空行、时间戳行、序号行
        if (not line or
            '-->' in line or
            re.match(r'^\d+$', line) or
            line.startswith('WEBVTT') or
            line.startswith('NOTE')):
            continue

        # 保留看起来像文本的行
        if len(line) > 2:
            segments.append({
                'start': 0.0,
                'end': 0.0,
                'text': line
            })

    return segments


def parse_timestamp(timestamp_str: str) -> float:
    """
    将时间戳字符串转换为秒数

    支持格式:
        00:00:02.500
        00:02.500
        02.500

    Args:
        timestamp_str: 时间戳字符串

    Returns:
        秒数（浮点数）
    """
    timestamp_str = timestamp_str.strip()

    # 分离时分秒
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


def clean_subtitle_text(segments: List[Dict]) -> str:
    """
    清理字幕文本

    操作:
        1. 移除 HTML 标签
        2. 移除说话人标签 [Speaker:]
        3. 去除连续重复行
        4. 时间间隔 >5 秒时添加段落分隔
        5. 规范化空白字符

    Args:
        segments: 字幕片段列表

    Returns:
        清理后的纯文本
    """
    if not segments:
        return ""

    # 1. 移除 HTML 标签和说话人标签
    cleaned_segments = []
    for seg in segments:
        text = seg['text']

        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)

        # 移除说话人标签 [Speaker:] 或 【说话人：】
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

    # 2. 去除连续重复行
    deduped_segments = []
    prev_text = None
    for seg in cleaned_segments:
        if seg['text'] != prev_text:
            deduped_segments.append(seg)
            prev_text = seg['text']

    # 3. 按时间间隔合并文本，间隔 >5 秒添加段落分隔
    result_lines = []
    prev_end = 0.0

    for seg in deduped_segments:
        gap = seg['start'] - prev_end

        # 如果间隔超过 5 秒，添加段落分隔
        if gap > 5.0 and result_lines:
            result_lines.append('')  # 空行

        result_lines.append(seg['text'])
        prev_end = seg['end']

    # 4. 合并为最终文本
    text = '\n'.join(result_lines)

    # 5. 规范化空白字符
    text = re.sub(r' +', ' ', text)  # 多个空格 → 单个空格
    text = re.sub(r'\n{3,}', '\n\n', text)  # 多个空行 → 最多两个

    return text.strip()


if __name__ == "__main__":
    # 简单测试
    import sys

    if len(sys.argv) < 2:
        print("用法: python subtitle_parser.py <字幕文件路径>")
        sys.exit(1)

    file_path = sys.argv[1]
    text = parse_subtitle_file(file_path)

    if text:
        print("\n" + "="*70)
        print("解析结果:")
        print("="*70)
        print(text)
        print("\n" + "="*70)
        print(f"总字符数: {len(text)}")
    else:
        print("\n❌ 解析失败")
        sys.exit(1)
