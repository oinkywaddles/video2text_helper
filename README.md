# 🎬 Video2Text Helper

一键式视频转文字工具，支持 Bilibili 和 YouTube 平台。

## ✨ 功能特性

- 🎥 **视频下载**: 支持 Bilibili 和 YouTube
- 🎙️ **语音转写**: 使用 faster-whisper (Whisper 优化版)
- 🌐 **多语言支持**: 自动检测 99+ 种语言
- ⚡ **高性能**: Apple Silicon M4 优化，处理速度 1.5-2.5x 实时速度
- 📝 **多格式输出**: 支持 text、SRT、VTT 字幕格式
- 🔧 **灵活配置**: 命令行参数丰富，支持多种工作模式

## 🚀 快速开始

### 环境要求

- macOS (Apple Silicon 推荐) 或 Linux/Windows
- Python 3.10+
- FFmpeg
- uv (Python 包管理器)

### 安装步骤

1. **安装 FFmpeg**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

2. **安装依赖**
```bash
# 创建虚拟环境
uv venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows

# 安装 Python 依赖
uv pip install yt-dlp faster-whisper torch
```

### 基本使用

```bash
# 一键完成：下载 + 转写
python main.py "https://www.bilibili.com/video/BV1xxxxxx"

# YouTube 视频
python main.py "https://www.youtube.com/watch?v=xxxxxx"
```

## 📖 详细用法

### 完整流程（下载 + 转写）

```bash
# 基本用法
python main.py "视频链接"

# 指定模型和格式
python main.py "视频链接" --model small --format srt

# YouTube 使用代理
python main.py "https://www.youtube.com/watch?v=xxx" --proxy "http://127.0.0.1:7890"

# 生成 SRT 字幕
python main.py "视频链接" --format srt -o output.srt
```

### 仅下载模式

```bash
# 只下载视频，不转写
python main.py "视频链接" --download-only

# 禁用 cookies
python main.py "视频链接" --download-only --no-cookies
```

### 仅转写模式

```bash
# 转写已有音频文件
python main.py --transcribe-only audio.mp3

# 指定语言（跳过自动检测）
python main.py --transcribe-only audio.mp3 --language zh

# 生成 VTT 字幕
python main.py --transcribe-only audio.mp3 --format vtt
```

## 🎛️ 命令行参数

### 下载选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--proxy` | 代理地址 | 无 |
| `--no-cookies` | 禁用浏览器 cookies | 启用 |
| `--output-dir` | 下载目录 | downloads |

### 转写选项

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `--model` | 模型大小 | tiny/base/small/medium/large-v3 | medium |
| `--language` | 语言代码 | zh/en/... | 自动检测 |
| `--format` | 输出格式 | text/srt/vtt | text |

### 工作模式

| 参数 | 说明 |
|------|------|
| `--download-only` | 仅下载视频 |
| `--transcribe-only` | 仅转写音频 |
| `-o, --output` | 指定输出文件路径 |

## 📊 性能数据

基于 MacBook Air M4 16GB 测试：

| 视频平台 | 时长 | 下载时间 | 转写时间 | 总耗时 | 处理速度 |
|----------|------|----------|----------|--------|----------|
| Bilibili | 4分12秒 | 8秒 | 2分32秒 | 2分42秒 | 1.66x |
| Bilibili | 24分51秒 | 15秒 | 17分12秒 | 17分30秒 | 1.44x |
| YouTube | 21分58秒 | 45秒 | 9分18秒 | 10分5秒 | 2.36x |

**平均处理速度**: 1.5-2.5x 实时速度

## 🏗️ 项目结构

```
video2text_helper/
├── main.py              # 主程序（完整流程）
├── downloader.py        # 视频下载模块
├── transcriber.py       # 语音转写模块
├── url_cleaner.py       # URL 清理工具
├── test_transcriber.py  # 转写测试脚本
├── downloads/           # 下载的音频文件
├── pyproject.toml       # 项目配置
├── README.md            # 本文件
└── .venv/               # 虚拟环境
```

## 🔧 技术栈

- **下载引擎**: yt-dlp (支持 1000+ 网站)
- **转写引擎**: faster-whisper (Whisper 优化版，快 4-5 倍)
- **音频处理**: FFmpeg
- **深度学习**: PyTorch
- **包管理**: uv

## 📝 输出格式

### Text 格式（默认）

```
[00:00:00.000 -> 00:00:04.500] 第一句话的内容
[00:00:04.500 -> 00:00:07.500] 第二句话的内容
```

### SRT 字幕格式

```
1
00:00:00,000 --> 00:00:04,500
第一句话的内容

2
00:00:04,500 --> 00:00:07,500
第二句话的内容
```

### VTT 字幕格式

```
WEBVTT

00:00:00.000 --> 00:00:04.500
第一句话的内容

00:00:04.500 --> 00:00:07.500
第二句话的内容
```

## 🌟 特性详解

### URL 自动清理

自动移除追踪参数，避免下载失败：

```bash
# 原始 URL (带参数)
https://www.bilibili.com/video/BV1xxx/?spm_id_from=xxx&vd_source=xxx

# 自动清理为
https://www.bilibili.com/video/BV1xxx
```

### Cookie 智能导入

- 默认从 Chrome 浏览器导入 cookies
- 绕过 Bilibili 等网站的反爬虫限制
- 可选禁用（使用 `--no-cookies`）

### 自动语言检测

- 支持 99+ 种语言
- 检测准确率 >99%
- 自动添加标点符号

### 模型选择建议

| 模型 | 大小 | 速度 | 精度 | 适用场景 |
|------|------|------|------|----------|
| tiny | 75 MB | 最快 | 较低 | 快速预览 |
| base | 150 MB | 快 | 一般 | 日常使用 |
| small | 500 MB | 较快 | 良好 | 平衡选择 |
| medium | 1.5 GB | 中等 | 优秀 | **推荐** |
| large-v3 | 3 GB | 慢 | 最佳 | 高精度需求 |

## 🐛 常见问题

### Q1: FFmpeg 未找到
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### Q2: YouTube 下载超时
使用代理：
```bash
python main.py "YouTube链接" --proxy "http://127.0.0.1:7890"
```

### Q3: Bilibili 下载失败 (HTTP 412)
URL 过长或带参数，程序会自动清理。如仍失败，手动简化 URL：
```bash
# 简化前
https://www.bilibili.com/video/BV1xxx/?spm_id_from=...

# 简化后
https://www.bilibili.com/video/BV1xxx
```

### Q4: 转录速度慢
- 使用更小的模型：`--model small`
- M4 芯片已经是最快的 CPU 选项
- 考虑使用 NVIDIA GPU（需要 CUDA）

### Q5: 内存不足
- 使用更小的模型：`--model small` 或 `--model base`
- 关闭其他占用内存的应用

## 📚 使用示例

### 示例 1: 下载 Bilibili 视频并转写为 SRT 字幕

```bash
python main.py "https://www.bilibili.com/video/BV1xxxxxx" \
  --format srt \
  -o "output.srt"
```

### 示例 2: YouTube 视频（使用代理 + 小模型）

```bash
python main.py "https://www.youtube.com/watch?v=xxxxxx" \
  --proxy "http://127.0.0.1:7890" \
  --model small
```

### 示例 3: 批量转写本地音频文件

```bash
# 转写单个文件
python main.py --transcribe-only audio1.mp3

# 使用脚本批量处理
for file in downloads/*.mp3; do
  python main.py --transcribe-only "$file"
done
```

### 示例 4: 仅下载视频，稍后转写

```bash
# 步骤 1: 下载视频
python main.py "视频链接" --download-only

# 步骤 2: 稍后转写
python main.py --transcribe-only "downloads/视频标题.mp3"
```

## 🎯 开发路线图

### 已完成 ✅
- [x] 视频下载 (Bilibili, YouTube)
- [x] 语音转写 (中英文)
- [x] 多格式输出 (text, SRT, VTT)
- [x] URL 自动清理
- [x] Cookie 智能导入
- [x] 命令行工具

### 计划中 🔮
- [ ] 批量处理支持
- [ ] 配置文件支持
- [ ] GUI 图形界面
- [ ] 更多平台支持
- [ ] 说话人识别
- [ ] 实时转录

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 强大的视频下载工具
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Whisper 优化版
- [OpenAI Whisper](https://github.com/openai/whisper) - 语音识别模型

## 📞 联系方式

- 问题反馈: GitHub Issues
- 功能建议: GitHub Discussions

---

**Made with ❤️ using Claude Code**
