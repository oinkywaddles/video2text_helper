# Video2Text Helper - Claude Code 开发指南

## 项目概述

这是一个全自动视频转文字工具，支持 YouTube 和 Bilibili 视频下载并转换为带时间戳的文本稿。

### 核心功能

1. **通用下载**：输入 YouTube 或 Bilibili 视频链接，自动下载音频文件
2. **语音转写**：使用 Whisper 模型将音频转换为带时间戳的文本
3. **本地运行**：利用本地算力（CPU/GPU），无需云端 API

## 技术栈

| 模块 | 工具/库 | 说明 |
|------|---------|------|
| **包管理器** | `uv` | 现代化的 Python 包管理器，速度快、依赖解析准确 |
| **编程语言** | Python 3.10+ | AI 生态完善，库丰富 |
| **下载引擎** | `yt-dlp` | 最强的视频下载库，支持 B站/YouTube |
| **音频处理** | `ffmpeg` | 视频流转码工具 |
| **ASR 模型** | `faster-whisper` | Whisper 优化版，速度快 4-5 倍，省显存 |

## 环境准备

### 1. 安装 FFmpeg (macOS)

```bash
brew install ffmpeg
```

### 2. 初始化项目

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖包
uv pip install yt-dlp faster-whisper torch
```

## 项目结构

```
video2text_helper/
├── downloader.py      # 视频下载模块
├── transcriber.py     # 音频转写模块
├── main.py           # 主程序入口
├── downloads/        # 下载文件存放目录（自动创建）
└── pyproject.toml    # 项目配置（推荐）
```

## 代码实现

### 模块 1: 下载器 (downloader.py)

负责调用 yt-dlp 下载音频，处理文件名，支持代理（针对 YouTube）。

```python
import yt_dlp
import os

def download_audio(url, output_dir="downloads", proxy=None):
    """
    下载视频音频并转换为 mp3
    返回: 下载文件的绝对路径
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

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
    }

    # 如果是 YouTube 且在中国，通常需要代理
    if proxy:
        ydl_opts['proxy'] = proxy

    print(f"⬇️ 正在下载: {url} ...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # 修正扩展名，因为 postprocessor 会把 ext 改成 mp3
            final_filename = os.path.splitext(filename)[0] + ".mp3"

            print(f"✅ 下载完成: {final_filename}")
            return final_filename
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None
```

### 模块 2: 转写器 (transcriber.py)

负责加载 faster-whisper 模型并进行识别。

```python
from faster_whisper import WhisperModel
import os

def transcribe_audio(audio_path, model_size="medium", device="auto"):
    """
    使用 faster-whisper 转录音频
    device: 'cuda' (N卡) 或 'cpu'
    model_size: 'tiny', 'base', 'small', 'medium', 'large-v3'
    """
    print(f"🧠 正在加载模型 ({model_size})...")

    # 自动判断设备
    if device == "auto":
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"

    compute_type = "float16" if device == "cuda" else "int8"

    print(f"🚀 运行在: {device} (精度: {compute_type})")

    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    print("🎙️ 开始转录，请稍候...")
    segments, info = model.transcribe(audio_path, beam_size=5)

    print(f"检测到语言: {info.language} (置信度: {info.language_probability})")

    results = []
    # 实时打印转录结果
    for segment in segments:
        line = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}"
        print(line)
        results.append(line)

    return "\n".join(results)
```

### 模块 3: 主程序 (main.py)

将两者串联起来。

```python
import argparse
import os
from downloader import download_audio
from transcriber import transcribe_audio

def main():
    parser = argparse.ArgumentParser(description="B站/YouTube 视频转文字工具")
    parser.add_argument("url", help="视频链接")
    parser.add_argument("--model", default="medium", help="Whisper模型大小 (tiny/small/medium/large-v3)")
    parser.add_argument("--proxy", default=None, help="代理地址 (例如 http://127.0.0.1:7890)")

    args = parser.parse_args()

    # 1. 下载
    audio_file = download_audio(args.url, proxy=args.proxy)

    if not audio_file:
        return

    # 2. 转写
    transcript = transcribe_audio(audio_file, model_size=args.model)

    # 3. 保存结果
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    output_txt = f"{base_name}_transcript.txt"

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(transcript)

    print(f"\n🎉 全部完成！结果已保存至: {output_txt}")

if __name__ == "__main__":
    main()
```

## 使用方法

### 1. 安装依赖

确保已安装 FFmpeg，然后：

```bash
# 创建并激活虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv pip install yt-dlp faster-whisper torch
```

### 2. 运行 Bilibili 视频

B站通常不需要代理：

```bash
uv run main.py "https://www.bilibili.com/video/BV1xxxxxx"
```

### 3. 运行 YouTube 视频 (需要代理)

假设梯子端口是 7890：

```bash
uv run main.py "https://www.youtube.com/watch?v=xxxxxx" --proxy "http://127.0.0.1:7890"
```

### 4. 指定模型大小

```bash
# 使用小模型（速度快）
uv run main.py "视频链接" --model small

# 使用大模型（精度高）
uv run main.py "视频链接" --model large-v3
```

## 优化建议

### 模型选择

- **tiny/small**: 速度快，精度一般，适合快速浏览
- **medium**: 速度和精度的最佳平衡点（推荐）
- **large-v3**: 精度最高，但 CPU 运行会很慢，建议有 GPU 时使用

### Mac M1/M2/M3 优化

- Mac 芯片的 CPU 性能已经足够强大，faster-whisper 可高效运行
- 推荐使用 medium 模型，在性能和精度间取得良好平衡
- 首次运行会下载模型，请耐心等待

### B站高清视频

如需下载大会员专享或 1080P+ 高码率视频音频，可在 `downloader.py` 的 `ydl_opts` 中添加：

```python
ydl_opts['cookiesfrombrowser'] = ('chrome',)  # 或 'firefox', 'safari'
```

## 依赖管理最佳实践

### 创建 pyproject.toml (推荐)

```toml
[project]
name = "video2text-helper"
version = "0.1.0"
description = "自动化视频转文字工具"
requires-python = ">=3.10"
dependencies = [
    "yt-dlp>=2024.0.0",
    "faster-whisper>=1.0.0",
    "torch>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

然后使用：

```bash
# 同步安装所有依赖
uv pip sync

# 或者直接安装当前项目
uv pip install -e .
```

## 常见问题

### Q: FFmpeg 未找到
A: 运行 `brew install ffmpeg` 安装

### Q: YouTube 下载超时
A: 检查代理设置，确保 `--proxy` 参数正确

### Q: 转录速度慢
A: 尝试使用更小的模型（如 small）

### Q: 导入错误
A: 确保已激活虚拟环境：`source .venv/bin/activate`

## 开发命令速查

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv pip install yt-dlp faster-whisper torch

# 运行程序
uv run main.py "视频链接"

# 查看已安装包
uv pip list

# 更新依赖
uv pip install --upgrade yt-dlp faster-whisper torch

# 冻结依赖（生成 requirements.txt）
uv pip freeze > requirements.txt
```

## Claude Code 开发提示

当使用 Claude Code 进行开发时，可以：

1. 直接要求实现某个功能模块
2. 要求优化现有代码性能
3. 要求添加错误处理和日志
4. 要求编写测试用例
5. 要求重构代码结构

示例 Prompt：
- "帮我实现 downloader.py 模块"
- "为 transcriber.py 添加进度条显示"
- "优化主程序的错误处理逻辑"
- "添加对本地音频文件的支持"
