"""
URL 清理工具

用于清理视频链接中的多余参数，提取视频 ID，检测平台类型。
"""

import re
from typing import Tuple, Optional


def detect_platform(url: str) -> Optional[str]:
    """
    检测视频平台类型

    参数:
        url: 视频链接

    返回:
        平台名称 ('bilibili', 'youtube') 或 None
    """
    if 'bilibili.com' in url or 'b23.tv' in url:
        return 'bilibili'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    return None


def clean_video_url(url: str) -> str:
    """
    清理视频 URL，移除多余的追踪参数

    参数:
        url: 原始视频链接

    返回:
        清理后的 URL
    """
    # Bilibili URL 清理
    # 匹配: https://www.bilibili.com/video/BVxxxxxxxxx
    # 或: https://www.bilibili.com/video/avxxxxxxx
    bilibili_pattern = r'(https?://(?:www\.)?bilibili\.com/video/(?:BV[\w]+|av\d+))'
    bilibili_match = re.search(bilibili_pattern, url)
    if bilibili_match:
        return bilibili_match.group(1)

    # YouTube URL 清理
    # 标准链接: https://www.youtube.com/watch?v=xxxxxxxxxxx
    # 短链接: https://youtu.be/xxxxxxxxxxx
    youtube_pattern = r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+))'
    youtube_match = re.search(youtube_pattern, url)
    if youtube_match:
        video_id = youtube_match.group(2)
        # 统一使用标准格式
        return f"https://www.youtube.com/watch?v={video_id}"

    # 如果不是支持的平台，返回原 URL
    return url


def extract_video_id(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    提取视频 ID

    参数:
        url: 视频链接

    返回:
        (平台名称, 视频ID) 或 (None, None)
    """
    # Bilibili BV 号
    bv_match = re.search(r'bilibili\.com/video/(BV[\w]+)', url)
    if bv_match:
        return ('bilibili', bv_match.group(1))

    # Bilibili AV 号
    av_match = re.search(r'bilibili\.com/video/(av\d+)', url)
    if av_match:
        return ('bilibili', av_match.group(1))

    # YouTube 视频 ID
    youtube_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]+)', url)
    if youtube_match:
        return ('youtube', youtube_match.group(1))

    return (None, None)


if __name__ == "__main__":
    # 测试用例
    test_urls = [
        "https://www.bilibili.com/video/BV1LTUvBLEnA/?spm_id_from=333.788",
        "https://www.bilibili.com/video/BV1Z6SEBrE1H",
        "https://www.bilibili.com/video/av12345678?from=search",
        "https://www.youtube.com/watch?v=n2to2wIKgDA&si=xQnapfIW6ezQk-HY",
        "https://youtu.be/n2to2wIKgDA?si=xQnapfIW6ezQk-HY",
        "https://example.com/video/123"
    ]

    print("URL 清理测试")
    print("=" * 70)

    for i, url in enumerate(test_urls, 1):
        print(f"\n测试 {i}:")
        print(f"  原始: {url}")

        platform = detect_platform(url)
        clean_url = clean_video_url(url)
        _, video_id = extract_video_id(url)

        print(f"  平台: {platform}")
        print(f"  清理: {clean_url}")
        print(f"  视频ID: {video_id}")
