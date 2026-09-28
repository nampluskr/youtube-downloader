# PyInstaller spec for the pywebview host (D-27: package.json's
# `package:pywebview` script runs this). Builds a one-folder distribution,
# not one-file — onefile's runtime self-extraction adds startup lag and is
# a second place native DLLs can go missing.
#
# Build with (from the project root, WinPython or any Python with the
# project's requirements.txt + local youtube-kit editable install):
#   npm run build          # dist/ must exist — this bundles it, doesn't build it
#   pyinstaller youtube-downloader.spec --noconfirm --distpath dist-py --workpath build-py
# Output: dist-py/youtube-downloader/youtube-downloader.exe
#
# youtube-kit and yt-dlp are bundled into the executable (D-27); ffmpeg is
# not bundled and is looked up on PATH at runtime instead.
#
# youtube-kit is installed editable (`pip install -e`), which registers a
# PEP 660 MetaPathFinder (__editable___youtube_kit_..._finder.py) instead of
# a plain sys.path entry. PyInstaller's modulegraph cannot follow that
# finder, so collect_all('youtube_kit') resolves the package's *names* from
# its dist-info metadata but then fails to locate the actual files ("Hidden
# import 'youtube_kit.core' not found") and silently ships none of its
# source. Tree() below copies the real source tree in as a normal on-disk
# 'youtube_kit' package instead, which the frozen app can import the usual
# way at runtime — no modulegraph analysis of its (stdlib + yt_dlp-only)
# imports is needed since both are already covered elsewhere in this spec.
from PyInstaller.utils.hooks import collect_all
from PyInstaller.building.datastruct import Tree

block_cipher = None

datas = [('dist', 'dist')]
binaries = []
hiddenimports = ['clr_loader', 'clr']

for pkg in ('webview', 'clr_loader', 'yt_dlp'):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

# Assumes youtube-kit's package-dir remap (pyproject.toml
# [tool.setuptools.package-dir] youtube_kit = "src") stays a flat mapping —
# i.e. '../youtube-kit/src' holds core.py/errors.py/url.py/... directly,
# not a nested 'youtube_kit/' subfolder. If youtube-kit ever switches to a
# conventional src/youtube_kit/ layout, this prefix would double it into
# youtube_kit/youtube_kit/ (A6 adversarial review, Codex, 2026-09-28) —
# check `../youtube-kit/src/__init__.py` still exists at that path when
# youtube-kit's layout changes.
youtube_kit_tree = Tree('../youtube-kit/src', prefix='youtube_kit', excludes=['__pycache__', '*.pyc'])

a = Analysis(
    ['src/hosts/pywebview/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='youtube-downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    youtube_kit_tree,
    strip=False,
    upx=False,
    name='youtube-downloader',
)
