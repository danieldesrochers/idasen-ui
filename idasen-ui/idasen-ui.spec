# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['idasen-ui.py'],
             pathex=['C:\\code\\git\\idasen-ui'],             
             binaries=[],
             datas=[('*.png','.'),('*.ico','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='idasen-ui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False, 
          version='file_version_info.txt', 
          icon='appicon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='idasen-ui')
