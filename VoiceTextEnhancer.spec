# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 收集所有需要的数据文件
added_files = [
    ('config.example.yaml', '.'),
    ('.env.example', '.'),
    ('src', 'src'),
    ('assets', 'assets'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'pyobjc-framework-Cocoa',
        'pyobjc-framework-Quartz',
        'pyobjc-framework-ApplicationServices',
        'pyobjc-framework-WebKit',
        'pyobjc-core',
        'webview',
        'webview.platforms.cocoa',
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
    [],
    exclude_binaries=True,
    name='VoiceTextEnhancer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示终端窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VoiceTextEnhancer',
)

app = BUNDLE(
    coll,
    name='VoiceTextEnhancer.app',
    icon='icon.icns',
    bundle_identifier='com.voicetextenhancer.app',
    info_plist={
        'CFBundleName': 'Voice Text Enhancer',
        'CFBundleDisplayName': 'Voice Text Enhancer',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'LSUIElement': '1',  # 不显示 Dock 图标，作为后台服务运行
        'NSAppleEventsUsageDescription': 'Voice Text Enhancer needs to control system events for text processing.',
        'NSSystemAdministrationUsageDescription': 'Voice Text Enhancer needs accessibility permissions to simulate keyboard input.',
    },
)
