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
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all submodules for packages with dynamic imports
hiddenimports = [
    # Flet GUI framework
    'flet',
    'flet.core',
    'flet_runtime',
    'flet_core',

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

# Collect data files
datas = []
datas += collect_data_files('flet')
datas += collect_data_files('flet_runtime', include_py_files=True)
datas += collect_data_files('certifi')

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
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

# macOS App Bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Video2Transcript.app',
        icon=None,  # Add icon path if available: 'assets/icon.icns'
        bundle_identifier='com.video2transcript.app',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '0.1.0',
        },
    )
