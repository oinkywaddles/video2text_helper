#!/usr/bin/env python3
"""
字幕下载模块

使用 yt-dlp 检查和下载视频字幕（不下载视频本身）
"""

import yt_dlp
import os
from typing import Optional, Dict, List
from url_cleaner import clean_video_url


# 平台语言优先级配置
PLATFORM_LANGUAGE_PRIORITY = {
    'bilibili': ['zh-Hans', 'zh-Hant', 'zh', 'en'],
    'youtube': ['en', 'zh-Hans', 'zh'],
    'default': ['zh-Hans', 'en']
}


def detect_platform(url: str) -> str:
    """
    检测视频平台

    Args:
        url: 视频链接

    Returns:
        'bilibili' | 'youtube' | 'unknown'
    """
    url_lower = url.lower()

    if 'bilibili.com' in url_lower:
        return 'bilibili'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    else:
        return 'unknown'


def check_subtitle_availability(url: str, proxy: Optional[str] = None,
                                use_cookies: bool = True) -> Optional[Dict]:
    """
    快速检查字幕可用性（不下载视频）

    Args:
        url: 视频链接
        proxy: 代理地址
        use_cookies: 是否使用浏览器 cookies

    Returns:
        {
            'has_subtitles': bool,
            'manual_subs': ['zh-Hans', 'en'],  # 手动字幕语言列表
            'auto_subs': ['en'],               # 自动字幕语言列表
            'platform': 'bilibili' | 'youtube'
        }
        失败返回 None
    """
    # 清理 URL
    url = clean_video_url(url)
    platform = detect_platform(url)

    # 配置 yt-dlp（仅获取信息，不下载）
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,  # 关键！不下载视频
    }

    # 添加 cookies（Bilibili 需要）
    if use_cookies:
        ydl_opts['cookiesfrombrowser'] = ('chrome',)

    # 添加代理（YouTube 可能需要）
    if proxy:
        ydl_opts['proxy'] = proxy

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # 提取字幕信息
            manual_subs = list(info.get('subtitles', {}).keys())
            auto_subs = list(info.get('automatic_captions', {}).keys())

            has_subtitles = bool(manual_subs or auto_subs)

            return {
                'has_subtitles': has_subtitles,
                'manual_subs': manual_subs,
                'auto_subs': auto_subs,
                'platform': platform
            }

    except Exception as e:
        print(f"⚠️ 检查字幕时出错: {e}")
        return None


def select_best_subtitle(subtitle_info: Dict,
                        language_priority: Optional[List[str]] = None) -> Optional[tuple]:
    """
    根据优先级选择最佳字幕

    优先级规则:
        1. 手动字幕 > 自动字幕（始终）
        2. 在同类型中，按 language_priority 顺序选择
        3. 如果 language_priority 为 None，使用平台默认优先级

    Args:
        subtitle_info: check_subtitle_availability() 返回的字幕信息
        language_priority: 语言优先级列表，例如 ['zh-Hans', 'en']

    Returns:
        (language_code, is_auto) 或 None
        例如: ('zh-Hans', False) 表示手动中文字幕
    """
    if not subtitle_info or not subtitle_info['has_subtitles']:
        return None

    manual_subs = subtitle_info['manual_subs']
    auto_subs = subtitle_info['auto_subs']
    platform = subtitle_info['platform']

    # 如果没有指定语言优先级，使用平台默认
    if language_priority is None:
        language_priority = PLATFORM_LANGUAGE_PRIORITY.get(
            platform,
            PLATFORM_LANGUAGE_PRIORITY['default']
        )

    # 优先尝试手动字幕
    if manual_subs:
        # 按优先级查找
        for lang in language_priority:
            if lang in manual_subs:
                return (lang, False)  # 找到手动字幕

        # 如果没有匹配，返回第一个手动字幕
        return (manual_subs[0], False)

    # 其次尝试自动字幕
    if auto_subs:
        # 按优先级查找
        for lang in language_priority:
            if lang in auto_subs:
                return (lang, True)  # 找到自动字幕

        # 如果没有匹配，返回第一个自动字幕
        return (auto_subs[0], True)

    return None


def download_subtitle(url: str, output_dir: str = "downloads",
                     language_priority: Optional[List[str]] = None,
                     proxy: Optional[str] = None,
                     use_cookies: bool = True) -> Optional[Dict]:
    """
    下载字幕文件（仅字幕，不下载视频）

    Args:
        url: 视频链接
        output_dir: 输出目录
        language_priority: 语言优先级列表
        proxy: 代理地址
        use_cookies: 是否使用浏览器 cookies

    Returns:
        {
            'success': bool,
            'file_path': str,      # 字幕文件绝对路径
            'language': str,       # 语言代码
            'is_auto': bool,       # 是否自动生成
            'format': str          # 'vtt' 或 'srt'
        }
        失败返回 None
    """
    # 清理 URL
    url = clean_video_url(url)

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 步骤 1: 检查字幕可用性
    subtitle_info = check_subtitle_availability(url, proxy, use_cookies)

    if not subtitle_info or not subtitle_info['has_subtitles']:
        print("ℹ️ 该视频没有可用字幕")
        return None

    # 步骤 2: 选择最佳字幕
    selection = select_best_subtitle(subtitle_info, language_priority)

    if not selection:
        print("ℹ️ 未能选择合适的字幕语言")
        return None

    selected_lang, is_auto = selection
    subtitle_type = "自动" if is_auto else "手动"
    print(f"📌 选择字幕: {subtitle_type} ({selected_lang})")

    # 步骤 3: 配置 yt-dlp 下载字幕
    ydl_opts = {
        'skip_download': True,          # 不下载视频！
        'writesubtitles': not is_auto,  # 下载手动字幕
        'writeautomaticsub': is_auto,   # 下载自动字幕
        'subtitleslangs': [selected_lang],  # 指定语言
        'subtitlesformat': 'vtt/srt',   # 优先 VTT，回退 SRT
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
    }

    # 添加 cookies
    if use_cookies:
        ydl_opts['cookiesfrombrowser'] = ('chrome',)

    # 添加代理
    if proxy:
        ydl_opts['proxy'] = proxy

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 下载字幕
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'video')

            # 查找下载的字幕文件
            # yt-dlp 会保存为: <video_title>.<lang>.vtt 或 .srt
            possible_extensions = ['vtt', 'srt']
            possible_names = [
                f"{video_title}.{selected_lang}",
                f"{video_title}.{selected_lang.replace('-', '_')}",
                video_title
            ]

            subtitle_file = None
            subtitle_format = None

            for name in possible_names:
                for ext in possible_extensions:
                    test_path = os.path.join(output_dir, f"{name}.{ext}")
                    if os.path.exists(test_path):
                        subtitle_file = test_path
                        subtitle_format = ext
                        break
                if subtitle_file:
                    break

            if not subtitle_file:
                # 尝试通配符查找
                import glob
                pattern = os.path.join(output_dir, f"*{selected_lang}*.vtt")
                matches = glob.glob(pattern)
                if not matches:
                    pattern = os.path.join(output_dir, f"*{selected_lang}*.srt")
                    matches = glob.glob(pattern)

                if matches:
                    subtitle_file = matches[0]
                    subtitle_format = 'vtt' if subtitle_file.endswith('.vtt') else 'srt'

            if subtitle_file and os.path.exists(subtitle_file):
                abs_path = os.path.abspath(subtitle_file)
                file_size = os.path.getsize(abs_path)

                print(f"✅ 字幕文件: {os.path.basename(abs_path)} ({file_size} bytes)")

                return {
                    'success': True,
                    'file_path': abs_path,
                    'language': selected_lang,
                    'is_auto': is_auto,
                    'format': subtitle_format
                }
            else:
                print(f"⚠️ 字幕下载完成但未找到文件")
                return None

    except Exception as e:
        print(f"❌ 下载字幕失败: {e}")
        return None


if __name__ == "__main__":
    # 简单测试
    import argparse

    parser = argparse.ArgumentParser(description="字幕下载工具")
    parser.add_argument("url", help="视频链接")
    parser.add_argument("--proxy", default=None, help="代理地址")
    parser.add_argument("--no-cookies", action="store_true", help="禁用 cookies")
    parser.add_argument("--output-dir", default="downloads", help="输出目录")
    parser.add_argument("--lang", default=None, help="语言优先级（逗号分隔）")

    args = parser.parse_args()

    print("=" * 70)
    print("字幕下载测试")
    print("=" * 70)
    print()

    # 检查字幕可用性
    print("步骤 1: 检查字幕...")
    subtitle_info = check_subtitle_availability(
        url=args.url,
        proxy=args.proxy,
        use_cookies=not args.no_cookies
    )

    if subtitle_info:
        print(f"✅ 平台: {subtitle_info['platform']}")
        print(f"   手动字幕: {', '.join(subtitle_info['manual_subs']) or '无'}")
        print(f"   自动字幕: {', '.join(subtitle_info['auto_subs']) or '无'}")
        print()

        if subtitle_info['has_subtitles']:
            # 下载字幕
            print("步骤 2: 下载字幕...")
            language_priority = args.lang.split(',') if args.lang else None

            result = download_subtitle(
                url=args.url,
                output_dir=args.output_dir,
                language_priority=language_priority,
                proxy=args.proxy,
                use_cookies=not args.no_cookies
            )

            if result and result['success']:
                print()
                print("=" * 70)
                print("✅ 下载成功！")
                print("=" * 70)
                print(f"文件路径: {result['file_path']}")
                print(f"语言: {result['language']}")
                print(f"类型: {'自动' if result['is_auto'] else '手动'}")
                print(f"格式: {result['format']}")
            else:
                print("\n❌ 下载失败")
        else:
            print("ℹ️ 该视频没有字幕")
    else:
        print("❌ 检查失败")
