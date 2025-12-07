#!/usr/bin/env python3
"""
Video2Text Helper - GUI Application

Flet-based desktop app supporting:
- YouTube/Bilibili video to text conversion
- Subtitle-first strategy (auto-detect subtitles, fallback to Whisper)
- Real-time progress display
- Multiple output formats
"""

import os
import subprocess
import sys

import flet as ft
from core import TaskManager, TaskStatus, WhisperModelManager


# Model options
MODEL_OPTIONS = [
    ("tiny", "Tiny (最快，约75MB)"),
    ("base", "Base (较快，约145MB)"),
    ("small", "Small (平衡，约466MB)"),
    ("medium", "Medium (推荐，约1.5GB)"),
    ("large-v3", "Large-v3 (最精确，约3GB)"),
]

# Output format options
FORMAT_OPTIONS = [
    ("text", "纯文本 (.txt)"),
    ("srt", "SRT 字幕 (.srt)"),
    ("vtt", "VTT 字幕 (.vtt)"),
]


class Video2TextApp:
    """Video2Text Helper main application"""

    def __init__(self, page):
        self.page = page
        self.task_manager = TaskManager()
        self.whisper_manager = WhisperModelManager()

        # Set task callbacks
        self.task_manager.set_callbacks(
            log_callback=self._on_log,
            progress_callback=self._on_progress,
            status_callback=self._on_status,
            complete_callback=self._on_complete
        )

        # State
        self._output_path = ""
        self._is_running = False

        # Initialize UI
        self._setup_page()
        self._build_ui()

    def _setup_page(self):
        """Set up page properties"""
        self.page.title = "Video2Text Helper"
        self.page.window.width = 700
        self.page.window.height = 750
        self.page.window.min_width = 600
        self.page.window.min_height = 600
        self.page.padding = 24
        self.page.bgcolor = ft.Colors.GREY_50
        self.page.theme_mode = ft.ThemeMode.LIGHT

    def _create_card(self, content, padding=25, expand=False):
        """Create a card container with shadow and rounded corners"""
        return ft.Container(
            content=content,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=padding,
            expand=expand,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

    def _build_ui(self):
        """Build UI components"""
        # URL input
        self.url_input = ft.TextField(
            hint_text="粘贴 YouTube 或 Bilibili 视频链接",
            expand=True,
            filled=True,
            border_color=ft.Colors.TRANSPARENT,
            bgcolor=ft.Colors.GREY_100,
            prefix_icon=ft.Icons.LINK,
            on_change=self._on_url_change,
        )

        # Cookie option
        self.cookie_checkbox = ft.Checkbox(
            label="使用浏览器 Cookie（推荐，可绕过某些限制）",
            value=True
        )

        # Model selection
        self.model_dropdown = ft.Dropdown(
            label="Whisper 模型",
            value="medium",
            options=[ft.dropdown.Option(key=k, text=v) for k, v in MODEL_OPTIONS],
            width=250,
            text_size=14,
            color=ft.Colors.GREY_700,
            label_style=ft.TextStyle(size=16, color=ft.Colors.GREY_900),
        )

        # Output format
        self.format_dropdown = ft.Dropdown(
            label="输出格式",
            value="text",
            options=[ft.dropdown.Option(key=k, text=v) for k, v in FORMAT_OPTIONS],
            width=200,
            text_size=14,
            color=ft.Colors.GREY_700,
            label_style=ft.TextStyle(size=16, color=ft.Colors.GREY_900),
        )

        # Timestamp option
        self.timestamp_checkbox = ft.Checkbox(
            label="包含时间戳",
            value=False
        )

        # Force Whisper option
        self.force_whisper_checkbox = ft.Checkbox(
            label="强制使用 Whisper（跳过字幕检查）",
            value=False
        )

        # Subtitle language selection (dynamically shown)
        self.subtitle_lang_dropdown = ft.Dropdown(
            label="字幕语言",
            hint_text="自动选择",
            options=[],
            width=200,
            visible=False,
            text_size=14,
            color=ft.Colors.GREY_700,
            label_style=ft.TextStyle(size=16, color=ft.Colors.GREY_900),
        )

        # Progress bar
        self.progress_bar = ft.ProgressBar(
            value=0,
            bar_height=3,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.GREY_200,
        )

        self.progress_text = ft.Text(
            "等待开始...",
            size=12,
            color=ft.Colors.GREY_600
        )

        # Log area
        self.log_text = ft.TextField(
            multiline=True,
            read_only=True,
            min_lines=15,
            max_lines=None,
            expand=True,
            text_size=12,
            text_style=ft.TextStyle(font_family="monospace"),
            color=ft.Colors.BLACK54,
            border_color=ft.Colors.TRANSPARENT,
            bgcolor=ft.Colors.GREY_100,
        )

        # Buttons
        self.start_button = ft.ElevatedButton(
            text="开始转换",
            icon=ft.Icons.PLAY_ARROW,
            width=160,
            height=42,
            on_click=self._on_start,
            disabled=True,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600,
            )
        )

        self.open_folder_button = ft.OutlinedButton(
            text="打开输出文件夹",
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            width=160,
            height=42,
            on_click=self._on_open_folder,
            disabled=True,
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
                side={
                    ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREY_400),
                },
            )
        )

        # Layout
        self.page.add(
            # Title area
            ft.Column([
                ft.Text(
                    "Video2Text Helper",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_800
                ),
                ft.Text(
                    "支持 YouTube / Bilibili 视频转文字",
                    size=14,
                    color=ft.Colors.GREY_600
                ),
            ]),

            # Spacing
            ft.Container(height=16),

            # Input card
            self._create_card(
                content=ft.Column([
                    ft.Text("视频链接", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                    ft.Container(height=8),
                    self.url_input,
                    ft.Container(height=12),
                    self.cookie_checkbox,
                    ft.Container(height=16),
                    ft.Row([
                        self.model_dropdown,
                        self.format_dropdown,
                        self.timestamp_checkbox
                    ], alignment=ft.MainAxisAlignment.START, spacing=16),
                    ft.Container(height=8),
                    ft.Row([
                        self.force_whisper_checkbox,
                        self.subtitle_lang_dropdown
                    ], alignment=ft.MainAxisAlignment.START, spacing=16),
                ]),
                padding=25,
            ),

            # Spacing
            ft.Container(height=16),

            # Log card
            self._create_card(
                content=ft.Column([
                    ft.Row([
                        ft.Text("日志", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800),
                        ft.Container(expand=True),
                        self.progress_text,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    self.progress_bar,
                    ft.Container(height=12),
                    self.log_text,
                ], expand=True),
                padding=20,
                expand=True,
            ),

            # Spacing
            ft.Container(height=16),

            # Button card
            self._create_card(
                content=ft.Row([
                    ft.Container(width=160),  # Left spacer
                    self.start_button,
                    self.open_folder_button,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=15,
            ),
        )

    def _on_url_change(self, e):
        """URL input changed"""
        url = self.url_input.value.strip()
        self.start_button.disabled = not bool(url)
        self.page.update()

    def _on_start(self, e):
        """Start/Cancel button clicked"""
        if self._is_running:
            # Cancel task
            self.task_manager.cancel()
            return

        url = self.url_input.value.strip()
        if not url:
            return

        # Clear log
        self.log_text.value = ""
        self._output_path = ""

        # Update button state to "Cancel"
        self._is_running = True
        self.start_button.text = "取消"
        self.start_button.icon = ft.Icons.CLOSE
        self.start_button.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_400,
        )
        self.open_folder_button.disabled = True

        # Reset progress
        self.progress_bar.value = 0
        self.progress_text.value = "正在启动..."

        self.page.update()

        # Start task
        output_dir = os.path.join(os.getcwd(), "downloads")
        self.task_manager.start(
            url=url,
            output_dir=output_dir,
            use_cookies=self.cookie_checkbox.value,
            proxy=None,
            subtitle_language=self.subtitle_lang_dropdown.value if self.subtitle_lang_dropdown.visible else None,
            force_whisper=self.force_whisper_checkbox.value,
            model_size=self.model_dropdown.value,
            output_format=self.format_dropdown.value,
            with_timestamps=self.timestamp_checkbox.value
        )

    def _on_open_folder(self, e):
        """Open output folder"""
        if self._output_path:
            folder = os.path.dirname(self._output_path)
        else:
            folder = os.path.join(os.getcwd(), "downloads")

        # Ensure directory exists
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Cross-platform open folder
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", folder])
        elif sys.platform == "win32":  # Windows
            subprocess.run(["explorer", folder])
        else:  # Linux
            subprocess.run(["xdg-open", folder])

    def _on_log(self, msg):
        """Log callback"""
        # Also output to terminal
        print(msg)
        # Update UI
        current = self.log_text.value or ""
        self.log_text.value = current + msg + "\n"
        self.page.update()

    def _on_progress(self, percent, stage):
        """Progress callback"""
        self.progress_bar.value = percent / 100.0
        self.progress_text.value = f"{stage} ({percent:.1f}%)"
        self.page.update()

    def _on_status(self, status):
        """Status callback"""
        status_text = {
            TaskStatus.IDLE: "等待开始",
            TaskStatus.FETCHING_INFO: "获取视频信息...",
            TaskStatus.CHECKING_SUBTITLE: "检查字幕...",
            TaskStatus.DOWNLOADING_SUBTITLE: "下载字幕...",
            TaskStatus.DOWNLOADING_AUDIO: "下载音频...",
            TaskStatus.TRANSCRIBING: "转录中...",
            TaskStatus.PARSING_SUBTITLE: "解析字幕...",
            TaskStatus.COMPLETED: "完成",
            TaskStatus.CANCELLED: "已取消",
            TaskStatus.ERROR: "出错"
        }.get(status, str(status))

        self.progress_text.value = status_text
        self.page.update()

    def _on_complete(self, success, output_path=None, error=None):
        """Completion callback"""
        # Reset button state to "Start"
        self._is_running = False
        self.start_button.text = "开始转换"
        self.start_button.icon = ft.Icons.PLAY_ARROW
        self.start_button.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_600,
        )
        self.start_button.disabled = False

        if success and output_path:
            self._output_path = output_path
            self.open_folder_button.disabled = False
            self.progress_bar.value = 1.0
            self.progress_text.value = "完成!"

            # Show success notification
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"转换完成: {os.path.basename(output_path)}"),
                action="打开",
                on_action=self._on_open_folder
            )
            self.page.snack_bar.open = True
        else:
            self.progress_text.value = f"失败: {error}" if error else "任务失败"

            # Show error notification
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"转换失败: {error}" if error else "未知错误"),
                bgcolor=ft.Colors.RED_400
            )
            self.page.snack_bar.open = True

        self.page.update()


def main(page):
    """Application entry point"""
    Video2TextApp(page)


if __name__ == "__main__":
    ft.app(target=main)
