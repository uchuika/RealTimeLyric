# -*- mode: python ; coding: utf-8 -*-
# ビルド方法:
#   venv\Scripts\pip install pyinstaller
#   venv\Scripts\pyinstaller RealTimeLyric.spec
# 生成物は dist\RealTimeLyric\ 配下(onedir形式)。Windows専用アプリのためWindows上でビルドすること。

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("web", "web"),
    ],
    hiddenimports=[
        "shazamio_core",
        "pythonnet",
        "clr_loader",
        "pyaudiowpatch",
        "webview.platforms.winforms",
        "webview.platforms.edgechromium",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RealTimeLyric",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RealTimeLyric",
)
