#!/usr/bin/env python3
"""
Video2Text Helper - 视频转文字工具

一键完成视频下载和语音转写
"""

import argparse
import os
import sys
import time
from downloader import download_audio
from transcriber import transcribe_audio


def main():
    parser = argparse.ArgumentParser(
        description="视频转文字一键工具 - 支持 Bilibili 和 YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 完整流程（下载 + 转写）
  python main.py "https://www.bilibili.com/video/BV1xxxxxx"

  # 指定模型和格式
  python main.py "https://www.bilibili.com/video/BV1xxxxxx" --model small --format srt

  # 使用代理（YouTube）
  python main.py "https://www.youtube.com/watch?v=xxxxxx" --proxy "http://127.0.0.1:7890"

  # 仅下载（不转写）
  python main.py "https://www.bilibili.com/video/BV1xxxxxx" --download-only

  # 仅转写（已有音频文件）
  python main.py --transcribe-only audio.mp3

  # 禁用 cookies
  python main.py "https://www.bilibili.com/video/BV1xxxxxx" --no-cookies

支持的平台:
  - Bilibili (bilibili.com)
  - YouTube (youtube.com, youtu.be)

输出格式:
  - text: 带时间戳的文本（默认）
  - srt: SRT 字幕格式
  - vtt: WebVTT 字幕格式
        """
    )

    # 主要参数
    parser.add_argument("url_or_file", nargs="?", help="视频链接或音频文件路径")

    # 下载选项
    download_group = parser.add_argument_group("下载选项")
    download_group.add_argument("--proxy", default=None,
                                help="代理地址，例如 http://127.0.0.1:7890")
    download_group.add_argument("--no-cookies", action="store_true",
                                help="禁用从浏览器导入 cookies")
    download_group.add_argument("--output-dir", default="downloads",
                                help="下载目录（默认: downloads）")

    # 转写选项
    transcribe_group = parser.add_argument_group("转写选项")
    transcribe_group.add_argument("--model", default="medium",
                                  choices=["tiny", "base", "small", "medium", "large-v3"],
                                  help="Whisper 模型大小（默认: medium）")
    transcribe_group.add_argument("--language", default=None,
                                  help="语言代码（zh=中文, en=英文, None=自动检测）")
    transcribe_group.add_argument("--format", default="text",
                                  choices=["text", "srt", "vtt"],
                                  help="输出格式（默认: text）")

    # 工作模式
    mode_group = parser.add_argument_group("工作模式")
    mode_group.add_argument("--download-only", action="store_true",
                           help="仅下载视频，不进行转写")
    mode_group.add_argument("--transcribe-only", action="store_true",
                           help="仅转写音频文件，不下载视频")

    # 输出选项
    output_group = parser.add_argument_group("输出选项")
    output_group.add_argument("-o", "--output", default=None,
                             help="输出文件路径（默认: 自动生成）")

    args = parser.parse_args()

    # 验证参数
    if not args.url_or_file:
        parser.print_help()
        print("\n❌ 错误: 请提供视频链接或音频文件路径")
        sys.exit(1)

    if args.download_only and args.transcribe_only:
        print("❌ 错误: --download-only 和 --transcribe-only 不能同时使用")
        sys.exit(1)

    # 显示欢迎信息
    print("=" * 70)
    print("🎬 Video2Text Helper - 视频转文字工具")
    print("=" * 70)
    print()

    # 记录总体开始时间
    total_start_time = time.time()

    # 工作流程
    audio_file = None
    transcript = None

    try:
        # 模式 1: 仅转写
        if args.transcribe_only:
            print("📝 模式: 仅转写")
            print(f"📁 音频文件: {args.url_or_file}")
            print()

            if not os.path.exists(args.url_or_file):
                print(f"❌ 错误: 音频文件不存在: {args.url_or_file}")
                sys.exit(1)

            audio_file = args.url_or_file

            # 转写音频
            print("🎙️ 步骤: 转写音频")
            print("-" * 70)
            transcript = transcribe_audio(
                audio_path=audio_file,
                model_size=args.model,
                language=args.language,
                output_format=args.format
            )

        # 模式 2: 仅下载
        elif args.download_only:
            print("⬇️ 模式: 仅下载")
            print(f"🔗 视频链接: {args.url_or_file}")
            print()

            # 下载视频
            print("📥 步骤: 下载视频")
            print("-" * 70)
            audio_file = download_audio(
                url=args.url_or_file,
                output_dir=args.output_dir,
                proxy=args.proxy,
                use_cookies=not args.no_cookies
            )

            if not audio_file:
                print("\n❌ 下载失败")
                sys.exit(1)

            print(f"\n✅ 下载完成: {audio_file}")

        # 模式 3: 完整流程（默认）
        else:
            print("🚀 模式: 完整流程（下载 + 转写）")
            print(f"🔗 视频链接: {args.url_or_file}")
            print()

            # 步骤 1: 下载视频
            print("📥 步骤 1/2: 下载视频")
            print("-" * 70)
            audio_file = download_audio(
                url=args.url_or_file,
                output_dir=args.output_dir,
                proxy=args.proxy,
                use_cookies=not args.no_cookies
            )

            if not audio_file:
                print("\n❌ 下载失败")
                sys.exit(1)

            print(f"\n✅ 下载完成: {audio_file}")
            print()

            # 步骤 2: 转写音频
            print("🎙️ 步骤 2/2: 转写音频")
            print("-" * 70)
            transcript = transcribe_audio(
                audio_path=audio_file,
                model_size=args.model,
                language=args.language,
                output_format=args.format
            )

        # 保存转写结果
        if transcript:
            # 生成输出文件名
            if args.output:
                output_file = args.output
            else:
                base_name = os.path.splitext(os.path.basename(audio_file))[0]
                ext = {"text": "txt", "srt": "srt", "vtt": "vtt"}[args.format]
                output_file = f"{base_name}_transcript.{ext}"

            # 保存文件
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(transcript)

                print(f"\n💾 转写结果已保存: {output_file}")

                # 显示文件信息
                file_size = os.path.getsize(output_file) / 1024
                line_count = len(transcript.split("\n"))
                char_count = len(transcript)

                print(f"📊 文件信息:")
                print(f"   - 大小: {file_size:.2f} KB")
                print(f"   - 行数: {line_count}")
                print(f"   - 字符数: {char_count}")

            except Exception as e:
                print(f"\n❌ 保存失败: {e}")
                sys.exit(1)

        # 显示总体统计
        total_elapsed = time.time() - total_start_time
        print()
        print("=" * 70)
        print("✅ 任务完成!")
        print("=" * 70)
        print(f"⏱️  总耗时: {format_duration(total_elapsed)}")

        if audio_file and not args.download_only:
            print(f"🎵 音频文件: {audio_file}")
        if transcript:
            print(f"📄 文本文件: {output_file}")

        print()
        print("🎉 感谢使用 Video2Text Helper!")
        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def format_duration(seconds):
    """
    将秒数格式化为可读的时长字符串
    """
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


if __name__ == "__main__":
    main()
