# main.spec — bundles all PNG, JSON, TXT files automatically
import os
from PyInstaller.utils.hooks import collect_data_files

project_root = os.path.dirname(os.path.abspath(__file__))

# Collect all .png, .json, .txt from root
datas = []
for file in os.listdir(project_root):
    if file.endswith((".png", ".json", ".txt")):
        datas.append((file, "."))

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,   # include data files
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[]
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HangmanGame',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='HangmanGame'
)
