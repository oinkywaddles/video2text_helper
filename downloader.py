import yt_dlp
import os
from url_cleaner import clean_video_url

def download_audio(url, output_dir="downloads", proxy=None, use_cookies=True):
    """
    下载视频音频并转换为 mp3

    参数:
        url: 视频链接 (支持 YouTube, Bilibili 等)
        output_dir: 下载目录，默认为 'downloads'
        proxy: 代理地址，例如 'http://127.0.0.1:7890'
        use_cookies: 是否从浏览器导入 cookies，默认为 True
                     启用此选项可以绕过某些网站的反爬虫限制

    返回:
        下载文件的绝对路径，失败返回 None
    """
    # 清理 URL，移除多余参数
    url = clean_video_url(url)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📁 创建下载目录: {output_dir}")

    # yt-dlp 配置
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'nocheckcertificate': True,
        'quiet': False,
        # 添加请求头以绕过反爬虫
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        },
    }

    # 如果启用 cookies，从浏览器导入
    if use_cookies:
        ydl_opts['cookiesfrombrowser'] = ('chrome',)
        print(f"🍪 已启用 Cookie 导入 (从 Chrome 浏览器)")

    # 如果是 YouTube 且在中国，通常需要代理
    if proxy:
        ydl_opts['proxy'] = proxy
        print(f"🌐 使用代理: {proxy}")

    print(f"⬇️ 正在下载: {url} ...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # 修正扩展名，因为 postprocessor 会把 ext 改成 mp3
            final_filename = os.path.splitext(filename)[0] + ".mp3"

            # 获取绝对路径
            abs_path = os.path.abspath(final_filename)

            print(f"✅ 下载完成: {abs_path}")
            return abs_path
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None


if __name__ == "__main__":
    # 简单的命令行测试
    import argparse

    parser = argparse.ArgumentParser(
        description="视频音频下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法（默认使用 cookies）
  python downloader.py "https://www.bilibili.com/video/BV1xxxxxx"

  # 使用代理 (YouTube)
  python downloader.py "https://www.youtube.com/watch?v=xxxxxx" --proxy "http://127.0.0.1:7890"

  # 禁用 Cookie 导入
  python downloader.py "https://www.bilibili.com/video/BV1xxxxxx" --no-cookies
        """
    )

    parser.add_argument("url", help="视频链接")
    parser.add_argument("--proxy", default=None, help="代理地址，例如 http://127.0.0.1:7890")
    parser.add_argument("--no-cookies", action="store_true",
                        help="禁用从 Chrome 浏览器导入 cookies（默认启用）")
    parser.add_argument("--output-dir", default="downloads", help="输出目录，默认为 downloads")

    args = parser.parse_args()

    result = download_audio(
        url=args.url,
        output_dir=args.output_dir,
        proxy=args.proxy,
        use_cookies=not args.no_cookies  # 反转逻辑
    )

    if result:
        print(f"\n🎉 成功！文件位置: {result}")
    else:
        print("\n💔 下载失败，请检查链接或网络连接")
        exit(1)
