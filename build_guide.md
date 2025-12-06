# Video2Text Helper 打包指南

本文档介绍如何将 Video2Text Helper 打包为独立的桌面应用。

## 前置要求

- Python 3.10+
- FFmpeg（已安装并添加到 PATH）
- macOS / Windows / Linux

## 开发环境设置

```bash
# 1. 创建虚拟环境
uv venv

# 2. 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 3. 安装依赖
uv pip install -r requirements.txt
```

## 运行应用

```bash
# 激活虚拟环境后
python app.py
```

或使用 Flet 命令：

```bash
flet run app.py
```

## 打包为独立应用

### 方式 1: 使用 Flet 内置打包（推荐）

Flet 提供了跨平台打包功能：

```bash
# macOS
flet pack app.py --name "Video2Text Helper" --icon icon.png

# Windows
flet pack app.py --name "Video2Text Helper" --icon icon.ico

# Linux
flet pack app.py --name "Video2Text Helper"
```

### 方式 2: 使用 PyInstaller

1. 安装 PyInstaller：

```bash
uv pip install pyinstaller
```

2. 创建 spec 文件（`video2text.spec`）：

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('core', 'core'),
    ],
    hiddenimports=[
        'flet',
        'faster_whisper',
        'yt_dlp',
        'torch',
        'ctranslate2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Video2Text Helper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设为 True 可显示控制台调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS 专用: 创建 .app 包
app = BUNDLE(
    exe,
    name='Video2Text Helper.app',
    icon='icon.icns',
    bundle_identifier='com.video2text.helper',
)
```

3. 打包：

```bash
pyinstaller video2text.spec
```

## 项目结构

```
video2text_helper/
├── app.py                  # GUI 主程序
├── core/                   # 核心业务逻辑
│   ├── __init__.py
│   ├── url_cleaner.py      # URL 清理工具
│   ├── transcribe_manager.py  # Whisper 模型管理
│   ├── download_manager.py # 下载管理
│   ├── subtitle_manager.py # 字幕解析
│   └── task_manager.py     # 任务流程管理
├── downloads/              # 下载文件目录（运行时创建）
├── requirements.txt        # 依赖清单
├── build_guide.md          # 本文档
└── CLAUDE.md               # 开发指南
```

## 核心模块说明

### WhisperModelManager

- **热启动**: 避免重复加载相同模型
- **进度回调**: 实时报告转录进度
- 支持模型: tiny, base, small, medium, large-v3

### DownloadTask

- 支持 YouTube 和 Bilibili
- 进度回调
- Cookie 支持（绕过限制）

### SubtitleManager

- 支持 VTT/SRT 格式
- 自动编码检测
- 文本清理和去重

### TaskManager

- **字幕优先策略**: 自动检测字幕，无字幕时使用 Whisper
- 异步执行（不阻塞 UI）
- 支持取消操作

## 注意事项

### Whisper 模型

模型会在首次使用时自动下载，不需要打包进应用：

| 模型 | 大小 | 说明 |
|------|------|------|
| tiny | ~75MB | 最快，精度一般 |
| base | ~145MB | 较快，精度一般 |
| small | ~466MB | 平衡 |
| medium | ~1.5GB | 推荐 |
| large-v3 | ~3GB | 最精确 |

### FFmpeg 依赖

用户需要单独安装 FFmpeg：

- **macOS**: `brew install ffmpeg`
- **Windows**: 从 https://ffmpeg.org/download.html 下载并添加到 PATH
- **Linux**: `sudo apt install ffmpeg`

### Cookie 支持

应用会从 Chrome 浏览器读取 Cookie 以绕过某些网站限制。如果遇到问题：

1. 确保 Chrome 浏览器已登录目标网站
2. 关闭 Chrome 后再运行应用（Cookie 数据库可能被锁定）

## 故障排除

### 模型下载失败

模型从 Hugging Face 下载，如果网络问题：

```bash
# 设置 HF 镜像（中国用户）
export HF_ENDPOINT=https://hf-mirror.com
```

### Bilibili 下载失败

1. 确保启用了 Cookie 选项
2. 在 Chrome 中登录 Bilibili
3. 尝试关闭 Chrome 后再运行

### YouTube 下载失败（中国用户）

需要配置系统代理，应用会自动使用系统代理设置。
