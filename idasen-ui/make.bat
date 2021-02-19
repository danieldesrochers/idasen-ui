@echo off
type file_version_info.txt
echo ===================================
echo.
echo Is the file version info updated ?
echo.
pause
echo ===================================
echo.
echo Is idasen-ui.nsi config updated ?
echo.
pause
echo =======
rmdir /s /q __pycache__
rmdir /s /q build
rmdir /s /q dist
rmdir /q dist
pyinstaller idasen-ui.spec
pause
echo =========
"C:\Program Files (x86)\NSIS\makensis.exe" idasen-ui.nsi