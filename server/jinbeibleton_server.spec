# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for JINBEIBLETON Python AI Server.
Bundles the FastAPI/Uvicorn backend into a single-folder executable.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect data files for key packages
datas = []
datas += collect_data_files('librosa')
datas += collect_data_files('soundfile')
datas += collect_data_files('google.genai')

# Include orchestration module as data
datas += [
    ('orchestration', 'orchestration'),
    ('user_style_profile.json', '.'),
    ('.env', '.'),
]

# Collect all submodules for packages that use dynamic imports
hiddenimports = []
hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('fastapi')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('httpx')
hiddenimports += collect_submodules('google.genai')
hiddenimports += collect_submodules('starlette')
hiddenimports += collect_submodules('anyio')
hiddenimports += collect_submodules('librosa')
hiddenimports += collect_submodules('soundfile')
hiddenimports += collect_submodules('scipy')
hiddenimports += collect_submodules('numpy')
hiddenimports += collect_submodules('pretty_midi')
hiddenimports += collect_submodules('mido')
hiddenimports += collect_submodules('ollama')
hiddenimports += collect_submodules('tenacity')
hiddenimports += collect_submodules('websockets')

# Explicit hidden imports for dynamic loading
hiddenimports += [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'email.mime.multipart',
    'email.mime.text',
    'encodings',
    'json',
    'multiprocessing',
    'concurrent.futures',
    'orchestration.advisor_engine',
    'orchestration.audio_engine',
    'orchestration.expert_engine',
    'orchestration.gemini_analysis_engine',
    'orchestration.local_analysis_engine',
    'orchestration.midi_engine',
    'orchestration.midi_analyzer',
    'orchestration.mixing_engine',
    'orchestration.ableton_control',
    'orchestration.ableton_shortcuts',
]

# MLX / Whisper - include only if available (optional heavy deps)
try:
    import mlx
    hiddenimports += collect_submodules('mlx')
    hiddenimports += collect_submodules('mlx_whisper')
    hiddenimports += collect_submodules('mlx_lm')
    datas += collect_data_files('mlx_whisper')
except ImportError:
    pass

# Torch - include only if available (optional heavy deps)
try:
    import torch
    hiddenimports += collect_submodules('torch')
    hiddenimports += collect_submodules('torchaudio')
    datas += collect_data_files('torch')
    datas += collect_data_files('torchaudio')
except ImportError:
    pass

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'cv2',
        'torchvision',
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='jinbeibleton-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    target_arch='arm64',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='jinbeibleton-server',
)
