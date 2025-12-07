# -*- mode: python ; coding: utf-8 -*-
"""
Video2Transcript - PyInstaller Build Specification

Usage:
    pyinstaller build.spec

Output:
    dist/Video2Transcript.exe (Windows)
    dist/Video2Transcript.app (macOS)
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# Collect all submodules for packages with dynamic imports
hiddenimports = [
    # Flet GUI framework
    'flet',
    'flet.core',
    'flet_runtime',
    'flet_core',
    'flet_desktop',  # 关键：解决 ModuleNotFoundError: flet_desktop

    # faster-whisper ASR
    'faster_whisper',
    'ctranslate2',

    # ONNX Runtime (used by faster-whisper)
    'onnxruntime',

    # Hugging Face (model download)
    'huggingface_hub',
    'huggingface_hub.utils',
    'huggingface_hub.file_download',

    # Tokenizers
    'tokenizers',

    # yt-dlp video download
    'yt_dlp',
    'yt_dlp.extractor',
    'yt_dlp.downloader',
    'yt_dlp.postprocessor',

    # PyTorch
    'torch',
    'torch._C',
    'torch.utils',

    # NumPy
    'numpy',
    'numpy.core',

    # Audio/Video processing
    'av',

    # Progress bars and logging
    'tqdm',
    'coloredlogs',
    'humanfriendly',
    'humanfriendly.terminal',

    # HTTP clients
    'httpx',
    'httpcore',

    # Other utilities
    'packaging',
    'filelock',
    'yaml',
    'certifi',
]

# Collect all yt-dlp extractors (there are hundreds)
hiddenimports += collect_submodules('yt_dlp.extractor')

# 初始化收集列表
datas = []
binaries = []

# 使用 collect_all 收集完整的 flet 依赖（包括 flet_desktop）
tmp_ret = collect_all('flet')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# 使用 collect_all 收集完整的 faster_whisper 依赖
tmp_ret = collect_all('faster_whisper')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# 额外收集其他数据文件
datas += collect_data_files('flet_runtime', include_py_files=True)
datas += collect_data_files('certifi')

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused packages to reduce size
        'matplotlib',
        'PIL',
        'cv2',
        'scipy',
        'pandas',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# onedir 模式：EXE 只包含脚本，文件分离到文件夹中
exe = EXE(
    pyz,
    a.scripts,
    [],  # onedir 模式：binaries, zipfiles, datas 移到 COLLECT
    exclude_binaries=True,  # 关键：启用 onedir 模式
    name='Video2Transcript',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide terminal window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# onedir 模式：收集所有文件到文件夹
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Video2Transcript',
)

# macOS App Bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,  # 注意：onedir 模式下使用 coll 而不是 exe
        name='Video2Transcript.app',
        icon=None,  # Add icon path if available: 'assets/icon.icns'
        bundle_identifier='com.video2transcript.app',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '0.1.0',
        },
    )
