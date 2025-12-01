# 阶段一验收测试：视频下载模块

## 已完成功能

1. ✅ 项目环境配置 (pyproject.toml)
2. ✅ uv 虚拟环境初始化
3. ✅ yt-dlp 依赖安装
4. ✅ 下载器模块实现 (downloader.py)
5. ✅ 测试脚本 (test_downloader.py)

## 验收前准备

### 1. 确认 FFmpeg 已安装

```bash
ffmpeg -version
```

如果未安装，运行：

```bash
brew install ffmpeg
```

### 2. 激活虚拟环境

```bash
source .venv/bin/activate
```

## 验收测试方法

### 方法一：快速测试（推荐）

使用命令行直接测试一个视频链接：

```bash
# 测试 Bilibili 视频
uv run downloader.py "https://www.bilibili.com/video/BV1xx411c7mu"

# 测试 YouTube 视频（需要代理）
uv run downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "http://127.0.0.1:7890"
```

### 方法二：使用测试脚本

1. 编辑 `test_downloader.py` 文件
2. 在 `test_urls` 列表中修改测试链接
3. 运行测试：

```bash
uv run test_downloader.py
```

### 方法三：在 Python 中导入测试

```bash
source .venv/bin/activate
python
```

然后在 Python 交互式环境中：

```python
from downloader import download_audio

# 测试 Bilibili
result = download_audio("https://www.bilibili.com/video/BV1xx411c7mu")
print(f"下载结果: {result}")

# 测试 YouTube（需要代理）
result = download_audio(
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    proxy="http://127.0.0.1:7890"
)
print(f"下载结果: {result}")
```

## 验收标准

### ✅ 必须通过的测试

1. **环境检查**
   - [ ] FFmpeg 已安装并可用
   - [ ] uv 虚拟环境已创建
   - [ ] yt-dlp 已成功安装

2. **功能测试**
   - [ ] 能够成功下载 Bilibili 视频音频
   - [ ] 音频文件保存在 `downloads/` 目录
   - [ ] 文件格式为 MP3
   - [ ] 文件可以正常播放

3. **输出验证**
   - [ ] 下载过程有清晰的进度提示
   - [ ] 成功时显示文件路径
   - [ ] 失败时显示错误信息

### 🔍 可选测试（如果有条件）

- [ ] YouTube 视频下载（需要代理）
- [ ] 其他平台视频（如果 yt-dlp 支持）
- [ ] 长视频下载（测试性能）
- [ ] 特殊字符标题处理

## 预期输出示例

成功下载时，你应该看到类似的输出：

```
📁 创建下载目录: downloads
⬇️ 正在下载: https://www.bilibili.com/video/BV1xx411c7mu ...
[download] Destination: downloads/视频标题.webm
[download] 100% of   5.20MiB in 00:03
[ExtractAudio] Destination: downloads/视频标题.mp3
Deleting original file downloads/视频标题.webm (pass -k to keep)
✅ 下载完成: /Users/mac/workspace/projects/video2text_helper/downloads/视频标题.mp3

🎉 成功！文件位置: /Users/mac/workspace/projects/video2text_helper/downloads/视频标题.mp3
```

## 文件结构检查

完成后，项目目录应该包含：

```
video2text_helper/
├── .venv/                  # 虚拟环境
├── downloads/              # 下载的音频文件
│   └── *.mp3
├── downloader.py           # 下载器模块
├── test_downloader.py      # 测试脚本
├── pyproject.toml          # 项目配置
├── CLAUDE.md               # 开发指南
├── PHASE1_TEST.md          # 本文件
└── gemini_prd.md           # 原始需求
```

## 常见问题排查

### Q1: 提示 "FFmpeg not found"

```bash
# 安装 FFmpeg
brew install ffmpeg

# 验证安装
ffmpeg -version
```

### Q2: 下载失败 "HTTP Error 403"

可能需要代理，尝试添加 `--proxy` 参数

### Q3: 提示 "No module named 'yt_dlp'"

```bash
# 激活虚拟环境
source .venv/bin/activate

# 重新安装
uv pip install yt-dlp
```

### Q4: YouTube 下载超时

确保代理设置正确，端口号匹配你的梯子软件

## 验收完成后

如果所有测试通过，我们可以进入下一阶段：

- 阶段二：语音转写模块 (transcriber.py)
- 阶段三：主程序集成 (main.py)
- 阶段四：完整流程测试

## 反馈建议

在验收过程中，请记录：

1. 哪些功能正常工作
2. 遇到的问题和错误信息
3. 性能表现（下载速度、文件大小等）
4. 改进建议

这将帮助我们优化后续开发！
