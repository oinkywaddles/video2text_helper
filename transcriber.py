from faster_whisper import WhisperModel
import os
import time


def transcribe_audio(audio_path, model_size="medium", device="auto", language=None, output_format="text"):
    """
    使用 faster-whisper 转录音频

    参数:
        audio_path: 音频文件路径
        model_size: 模型大小 ('tiny', 'base', 'small', 'medium', 'large-v3')
        device: 设备选择 ('auto', 'cpu', 'cuda')
        language: 语言代码（None 表示自动检测，'zh' 中文，'en' 英文）
        output_format: 输出格式 ('text', 'srt', 'vtt')

    返回:
        转录文本字符串，失败返回 None
    """
    if not os.path.exists(audio_path):
        print(f"❌ 错误: 音频文件不存在: {audio_path}")
        return None

    # 获取文件大小
    file_size = os.path.getsize(audio_path) / 1024 / 1024  # MB
    print(f"📁 音频文件: {os.path.basename(audio_path)}")
    print(f"📊 文件大小: {file_size:.2f} MB")

    # 自动判断设备
    if device == "auto":
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"

    # 根据设备选择计算精度
    compute_type = "float16" if device == "cuda" else "int8"

    print(f"🧠 正在加载模型: {model_size}")
    print(f"🚀 运行设备: {device} (精度: {compute_type})")

    # 加载模型（首次运行会自动下载）
    start_load = time.time()
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        load_time = time.time() - start_load
        print(f"✅ 模型加载完成 (耗时: {load_time:.2f}s)")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return None

    print("🎙️ 开始转录，请稍候...")
    start_time = time.time()

    try:
        # 转录音频
        # beam_size: 束搜索大小，越大越准确但越慢
        segments, info = model.transcribe(
            audio_path,
            beam_size=5,
            language=language,
            task="transcribe"  # 'transcribe' 或 'translate'
        )

        # 显示检测到的语言
        print(f"🌐 检测到语言: {info.language} (置信度: {info.language_probability:.2%})")

        results = []
        segment_count = 0

        # 处理每个片段
        for segment in segments:
            segment_count += 1

            # 格式化时间戳
            start_str = format_timestamp(segment.start)
            end_str = format_timestamp(segment.end)

            # 根据输出格式生成文本
            if output_format == "srt":
                # SRT 字幕格式
                line = f"{segment_count}\n{start_str} --> {end_str}\n{segment.text.strip()}\n"
            elif output_format == "vtt":
                # WebVTT 字幕格式
                line = f"{start_str} --> {end_str}\n{segment.text.strip()}\n"
            else:
                # 默认文本格式（带时间戳）
                line = f"[{start_str} -> {end_str}] {segment.text.strip()}"

            # 实时打印（每 10 个片段显示一次进度）
            if segment_count % 10 == 0:
                print(f"📝 已处理 {segment_count} 个片段...")

            results.append(line)

        # 计算统计信息
        elapsed_time = time.time() - start_time
        audio_duration = segment.end if segment_count > 0 else 0
        speed_ratio = audio_duration / elapsed_time if elapsed_time > 0 else 0

        print(f"\n✅ 转录完成!")
        print(f"📊 统计信息:")
        print(f"   - 总片段数: {segment_count}")
        print(f"   - 音频时长: {format_duration(audio_duration)}")
        print(f"   - 转录耗时: {format_duration(elapsed_time)}")
        print(f"   - 处理速度: {speed_ratio:.2f}x 实时速度")

        # 组合结果
        if output_format == "srt":
            return "\n".join(results)
        elif output_format == "vtt":
            return "WEBVTT\n\n" + "\n".join(results)
        else:
            return "\n".join(results)

    except Exception as e:
        print(f"❌ 转录失败: {e}")
        return None


def format_timestamp(seconds):
    """
    将秒数格式化为时间戳字符串

    参数:
        seconds: 秒数（浮点数）

    返回:
        格式化的时间戳 (HH:MM:SS.mmm 或 HH:MM:SS,mmm for SRT)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def format_duration(seconds):
    """
    将秒数格式化为可读的时长字符串

    参数:
        seconds: 秒数（浮点数）

    返回:
        格式化的时长字符串
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
    # 简单的命令行测试
    import argparse

    parser = argparse.ArgumentParser(
        description="音频转文字工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python transcriber.py audio.mp3

  # 指定模型大小
  python transcriber.py audio.mp3 --model small

  # 指定语言（跳过自动检测）
  python transcriber.py audio.mp3 --language zh

  # 生成 SRT 字幕文件
  python transcriber.py audio.mp3 --format srt -o output.srt
        """
    )

    parser.add_argument("audio_file", help="音频文件路径")
    parser.add_argument("--model", default="medium",
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="模型大小（默认: medium）")
    parser.add_argument("--language", default=None,
                        help="语言代码（zh=中文, en=英文, None=自动检测）")
    parser.add_argument("--format", default="text",
                        choices=["text", "srt", "vtt"],
                        help="输出格式（默认: text）")
    parser.add_argument("-o", "--output", default=None,
                        help="输出文件路径（默认: 音频文件名_transcript.txt）")

    args = parser.parse_args()

    # 转录
    result = transcribe_audio(
        audio_path=args.audio_file,
        model_size=args.model,
        language=args.language,
        output_format=args.format
    )

    if result:
        # 生成输出文件名
        if args.output:
            output_file = args.output
        else:
            base_name = os.path.splitext(os.path.basename(args.audio_file))[0]
            ext = "srt" if args.format == "srt" else "vtt" if args.format == "vtt" else "txt"
            output_file = f"{base_name}_transcript.{ext}"

        # 保存结果
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"\n💾 结果已保存: {output_file}")
        except Exception as e:
            print(f"\n❌ 保存失败: {e}")
            exit(1)
    else:
        print("\n💔 转录失败")
        exit(1)
