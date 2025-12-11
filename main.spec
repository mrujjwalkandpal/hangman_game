# main.spec — bundles all PNG, JSON, TXT files in project root
import os

project_root = os.path.dirname(os.path.abspath(__file__))

datas = []
for file in os.listdir(project_root):
    if file.lower().endswith((".png", ".json", ".txt")):
        datas.append((file, "."))

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    datas=datas,
    binaries=[],
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
    strip=False,
    upx=False,
    console=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='HangmanGame'
)
