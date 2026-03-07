# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['C:\\Users\\leemi\\Desktop\\Github Repositories\\ProgramasParaLG\\bi_hourly_reviewer'],
    binaries=[],
    datas=[],
    hiddenimports=['core', 'core.csv_parser', 'core.defect_filter', 'core.defect_analyzer', 'core.image_locator', 'core.image_selector', 'core.image_fetcher', 'core.fetch_pipeline', 'core.crop_locator', 'core.crop_selector', 'core.crop_fetcher', 'core.crop_cache', 'ui', 'ui.main_window', 'ui.fetch_tab', 'ui.review_tab', 'ui.styles', 'ui.widgets', 'ui.widgets.cell_list', 'ui.widgets.image_viewer', 'utils', 'utils.time_utils', 'utils.file_utils', 'config'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BiHourlyReviewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
