这是一个非常经典且实用的自动化项目。既然你希望使用 **Claude Code**（或者任何 AI 编程助手）来协助开发，我为你准备了一份**详细的技术方案文档**。

你可以直接将这份文档作为 Prompt 发给 AI，或者参考这份结构自己编写代码。

-----

# 项目方案：全自动视频转文字工具 (Video-to-Text Pipeline)

## 1\. 项目目标

构建一个 Python 命令行工具，实现以下功能：

1.  **通用下载**：输入 YouTube 或 Bilibili 视频链接，自动下载音频文件。
2.  **语音转写**：使用 Whisper 模型将下载的音频转换为带时间戳的文本稿。
3.  **本地运行**：无需调用昂贵的云端 API，利用本地算力（CPU/GPU）。

## 2\. 技术栈选型 (Tech Stack)

| 模块 | 推荐库/工具 | 选择理由 |
| :--- | :--- | :--- |
| **编程语言** | Python 3.10+ | AI 生态最完善，库最丰富。 |
| **下载引擎** | **`yt-dlp`** | 目前最强的视频下载库，完美支持 B站/YT，更新频率高。 |
| **音频处理** | **`ffmpeg`** | `yt-dlp` 的依赖项，用于将视频流转码为 MP3/WAV。 |
| **ASR 模型** | **`faster-whisper`** | OpenAI Whisper 的优化版。**速度比原版快 4-5 倍**，且更省显存，非常适合个人电脑。 |

-----

## 3\. 环境准备 (Prerequisites)

在开始写代码前，必须确保系统安装了以下依赖：

1.  **Python 库**：
    ```bash
    pip install yt-dlp faster-whisper torch
    ```
2.  **系统工具 FFmpeg (必须安装，否则无法提取音频)**：
      * **Windows**: 下载 FFmpeg release版，解压并将 `bin` 目录添加到系统环境变量 `Path` 中。
      * **Mac**: `brew install ffmpeg`

-----

## 4\. 代码实现方案 (Implementation)

我们将项目分为三个部分：`downloader.py` (下载), `transcriber.py` (转写), `main.py` (主控)。

### 模块 1: 下载器 (`downloader.py`)

负责调用 `yt-dlp` 下载音频，处理文件名，并支持代理（针对 YouTube）。

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
        # 禁用一些可能会导致报错的选项
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

### 模块 2: 转写器 (`transcriber.py`)

负责加载 `faster-whisper` 模型并进行识别。

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

### 模块 3: 主程序 (`main.py`)

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
    # 注意：如果你需要下载 YouTube，请在这里填入你的代理地址，例如 'http://127.0.0.1:7890'
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

-----

## 5\. 如何运行 (Usage)

### 步骤 1：安装依赖

确保你已经安装了 Python 和 FFmpeg。

```bash
pip install yt-dlp faster-whisper torch
```

### 步骤 2：运行 B站链接

B站通常不需要代理，直接运行：

```bash
python main.py "https://www.bilibili.com/video/BV1xxxxxx"
```

### 步骤 3：运行 YouTube 链接 (需要代理)

如果不挂代理，`yt-dlp` 连接 YouTube 会超时。假设你的梯子端口是 7890：

```bash
python main.py "https://www.youtube.com/watch?v=xxxxxx" --proxy "http://127.0.0.1:7890"
```

-----

## 6\. 给开发者的优化建议 (Pro Tips)

1.  **模型选择 (Model Size)**:
      * `small`: 速度快，精度一般。适合快速浏览。
      * `medium`: 速度和精度的最佳平衡点（推荐）。
      * `large-v3`: 精度最高，但如果你没有 GPU，CPU 跑起来会非常慢。
2.  **GPU 加速 (CUDA)**:
      * 如果你有 NVIDIA 显卡，请务必安装 `CUDA` 和 `cuDNN`，`faster-whisper` 会自动调用 GPU，速度能提升 10 倍以上。
      * 如果是 Mac (M1/M2/M3)，`faster-whisper` 也可以利用 CPU 高效运行，虽然不如 N 卡快，但也完全可用。
3.  **B站 Cookie**:
      * 如果你需要下载 B站 **大会员专享** 或 **1080P+ 高码率** 视频的音频，可能需要在 `ydl_opts` 中添加 `cookies-from-browser` 参数，或者使用 `cookiefile`。但对于普通的音频提取，通常不需要登录。

你可以将上述代码直接复制并保存为三个文件，即可在本地直接跑通流程。
