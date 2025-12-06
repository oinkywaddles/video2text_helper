"""
下载管理器

核心特性：
- 进度回调：实时报告下载进度
- 支持字幕优先下载
- 支持 Cookie 导入
"""

import os
import yt_dlp
from typing import Optional, Callable, Dict, List, Any
from .url_cleaner import clean_video_url, detect_platform
from .config import get_default_use_cookies, get_cookie_browser


class DownloadTask:
    """
    下载任务类

    支持：
    - 音频下载（转 MP3）
    - 字幕下载（VTT/SRT）
    - 实时进度回调
    """

    def __init__(
        self,
        url: str,
        output_dir: str = "downloads",
        use_cookies: Optional[bool] = None,
        proxy: Optional[str] = None
    ):
        """
        初始化下载任务

        Args:
            url: 视频链接
            output_dir: 输出目录
            use_cookies: 是否使用浏览器 cookies (None=根据平台自动决定)
            proxy: 代理地址（如 http://127.0.0.1:7890）
        """
        self.original_url = url
        self.url = clean_video_url(url)
        self.platform = detect_platform(url)
        self.output_dir = output_dir
        self.proxy = proxy

        # 根据平台配置决定是否使用 cookies
        if use_cookies is None:
            self.use_cookies = get_default_use_cookies(self.platform)
        else:
            self.use_cookies = use_cookies

        self.cookie_browser = get_cookie_browser(self.platform)

        # 状态
        self._cancelled = False
        self._video_info: Optional[Dict] = None

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def cancel(self):
        """取消下载"""
        self._cancelled = True

    def get_video_info(
        self,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[Dict]:
        """
        获取视频信息（不下载）

        Returns:
            {
                'title': str,
                'duration': float,  # 秒
                'platform': str,
                'subtitles': {
                    'manual': ['zh-Hans', 'en', ...],
                    'auto': ['en', ...]
                }
            }
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        log(f"[信息] 获取视频信息...")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }

        if self.use_cookies:
            ydl_opts['cookiesfrombrowser'] = (self.cookie_browser,)

        if self.proxy:
            ydl_opts['proxy'] = self.proxy

        try:
            info = None
            # 尝试获取信息，不指定格式
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            if info is None:
                log("[错误] 无法获取视频信息")
                return None

            self._video_info = {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'platform': self.platform,
                'subtitles': {
                    'manual': list(info.get('subtitles', {}).keys()),
                    'auto': list(info.get('automatic_captions', {}).keys()),
                }
            }

            log(f"[信息] 标题: {self._video_info['title']}")
            log(f"[信息] 时长: {self._format_duration(self._video_info['duration'])}")

            manual_subs = self._video_info['subtitles']['manual']
            auto_subs = self._video_info['subtitles']['auto']
            if manual_subs:
                log(f"[字幕] 手动字幕: {', '.join(manual_subs)}")
            if auto_subs:
                log(f"[字幕] 自动字幕: {', '.join(auto_subs[:5])}{'...' if len(auto_subs) > 5 else ''}")

            return self._video_info

        except Exception as e:
            log(f"[错误] 获取信息失败: {e}")
            return None

    def download_audio(
        self,
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Optional[str]:
        """
        下载音频并转换为 MP3

        Args:
            log_callback: 日志回调 fn(msg: str)
            progress_callback: 进度回调 fn(percent: float)  # 0.0 ~ 100.0

        Returns:
            下载文件的绝对路径，失败返回 None
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        def progress(percent: float):
            if progress_callback:
                progress_callback(percent)

        if self._cancelled:
            log("[取消] 下载已取消")
            return None

        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        log(f"[下载] 开始下载音频...")
        log(f"[下载] URL: {self.url}")

        # 进度钩子
        def progress_hook(d):
            if self._cancelled:
                raise Exception("下载已取消")

            if d['status'] == 'downloading':
                # 计算进度
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    progress(percent)

            elif d['status'] == 'finished':
                log(f"[下载] 下载完成，正在转换...")
                progress(100.0)

        # yt-dlp 配置
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.output_dir}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [progress_hook],
        }

        if self.use_cookies:
            ydl_opts['cookiesfrombrowser'] = (self.cookie_browser,)
            log(f"[下载] 使用 Cookie (Chrome)")

        if self.proxy:
            ydl_opts['proxy'] = self.proxy
            log(f"[下载] 使用代理: {self.proxy}")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                filename = ydl.prepare_filename(info)
                final_filename = os.path.splitext(filename)[0] + ".mp3"
                abs_path = os.path.abspath(final_filename)

                log(f"[下载] 完成: {os.path.basename(abs_path)}")
                return abs_path

        except Exception as e:
            if "取消" in str(e):
                log("[取消] 下载已取消")
            else:
                log(f"[错误] 下载失败: {e}")
            return None

    def download_subtitle(
        self,
        language: Optional[str] = None,
        prefer_auto: bool = False,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[Dict]:
        """
        下载字幕文件

        Args:
            language: 指定语言 (None=自动选择最佳)
            prefer_auto: 是否优先自动字幕（默认优先手动字幕）
            log_callback: 日志回调

        Returns:
            {
                'file_path': str,
                'language': str,
                'is_auto': bool,
                'format': 'vtt' | 'srt'
            }
            失败返回 None
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        if self._cancelled:
            log("[取消] 下载已取消")
            return None

        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # 获取视频信息（如果还没有）
        if self._video_info is None:
            self.get_video_info(log_callback)

        if self._video_info is None:
            log("[错误] 无法获取视频信息")
            return None

        # 选择字幕
        manual_subs = self._video_info['subtitles']['manual']
        auto_subs = self._video_info['subtitles']['auto']

        if not manual_subs and not auto_subs:
            log("[信息] 该视频没有可用字幕")
            return None

        # 确定下载哪种字幕
        selected_lang = None
        is_auto = False

        # 语言优先级
        lang_priority = self._get_language_priority()

        if language:
            # 用户指定了语言
            if language in manual_subs:
                selected_lang = language
                is_auto = False
            elif language in auto_subs:
                selected_lang = language
                is_auto = True
            else:
                log(f"[警告] 找不到语言 {language} 的字幕")
        else:
            # 自动选择
            if not prefer_auto and manual_subs:
                # 优先手动字幕
                for lang in lang_priority:
                    if lang in manual_subs:
                        selected_lang = lang
                        is_auto = False
                        break
                if not selected_lang:
                    selected_lang = manual_subs[0]
                    is_auto = False

            if not selected_lang and auto_subs:
                # 使用自动字幕
                for lang in lang_priority:
                    if lang in auto_subs:
                        selected_lang = lang
                        is_auto = True
                        break
                if not selected_lang:
                    selected_lang = auto_subs[0]
                    is_auto = True

        if not selected_lang:
            log("[信息] 没有找到合适的字幕")
            return None

        subtitle_type = "自动" if is_auto else "手动"
        log(f"[字幕] 选择: {subtitle_type} ({selected_lang})")

        # 配置 yt-dlp
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': not is_auto,
            'writeautomaticsub': is_auto,
            'subtitleslangs': [selected_lang],
            'subtitlesformat': 'vtt/srt',
            'outtmpl': f'{self.output_dir}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        if self.use_cookies:
            ydl_opts['cookiesfrombrowser'] = (self.cookie_browser,)

        if self.proxy:
            ydl_opts['proxy'] = self.proxy

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                video_title = info.get('title', 'video')

                # 查找下载的字幕文件
                subtitle_file = self._find_subtitle_file(video_title, selected_lang)

                if subtitle_file and os.path.exists(subtitle_file):
                    abs_path = os.path.abspath(subtitle_file)
                    fmt = 'vtt' if subtitle_file.endswith('.vtt') else 'srt'

                    log(f"[字幕] 下载完成: {os.path.basename(abs_path)}")

                    return {
                        'file_path': abs_path,
                        'language': selected_lang,
                        'is_auto': is_auto,
                        'format': fmt
                    }
                else:
                    log("[警告] 字幕下载完成但未找到文件")
                    return None

        except Exception as e:
            log(f"[错误] 字幕下载失败: {e}")
            return None

    def _get_language_priority(self) -> List[str]:
        """获取语言优先级列表"""
        if self.platform == 'bilibili':
            return ['zh-Hans', 'zh-Hant', 'zh', 'en']
        elif self.platform == 'youtube':
            return ['en', 'zh-Hans', 'zh', 'zh-Hant']
        else:
            return ['zh-Hans', 'en', 'zh']

    def _find_subtitle_file(self, video_title: str, language: str) -> Optional[str]:
        """查找下载的字幕文件"""
        import glob

        possible_names = [
            f"{video_title}.{language}",
            f"{video_title}.{language.replace('-', '_')}",
            video_title
        ]

        for name in possible_names:
            for ext in ['vtt', 'srt']:
                test_path = os.path.join(self.output_dir, f"{name}.{ext}")
                if os.path.exists(test_path):
                    return test_path

        # 通配符查找
        for ext in ['vtt', 'srt']:
            pattern = os.path.join(self.output_dir, f"*{language}*.{ext}")
            matches = glob.glob(pattern)
            if matches:
                return matches[0]

        return None

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}小时{minutes}分"
