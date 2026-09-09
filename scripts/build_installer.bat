@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
chcp 65001 >nul
set "APP_VERSION=1.0.0"
title Drift的综合调试助手 - 生成安装包

if /i "%~1"=="--check" goto check_environment

echo ========================================
echo    Drift的综合调试助手 v%APP_VERSION% - 生成安装包
echo ========================================
echo.

echo [1/6] 检查构建环境...
where python >nul 2>&1
if errorlevel 1 (
    echo 未找到 Python，请安装 Python 3.11 或更高版本并加入 PATH。
    pause
    exit /b 1
)
python -c "import PyInstaller, PIL, openpyxl, serial, PyQt6" >nul 2>&1
if errorlevel 1 (
    echo 检测到缺少依赖，正在安装 requirements.txt...
    python -m pip install -r requirements.txt --disable-pip-version-check
    if errorlevel 1 (
        echo 依赖安装失败，请检查 Python 和网络环境。
        pause
        exit /b 1
    )
)
echo 完成！
echo.

echo [2/6] 生成应用图标和安装向导视觉资源...
python -c "from PIL import Image; img = Image.open('src/resource/Assistant.png'); img.save('src/resource/Assistant.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
if errorlevel 1 (
    echo 图标转换失败。
    pause
    exit /b 1
)
python scripts\generate_installer_assets.py
if errorlevel 1 (
    echo 安装向导视觉资源生成失败。
    pause
    exit /b 1
)
echo 完成！
echo.

echo [3/6] 清理旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo 完成！
echo.

echo [4/6] PyInstaller 打包...
python -m PyInstaller scripts\build.spec --clean
if errorlevel 1 (
    echo 打包失败！请检查错误信息。
    pause
    exit /b 1
)
echo 完成！
echo.

echo [5/6] 查找 Inno Setup...
set "ISCC="
if exist "D:\Environment\Inno Setup 6\ISCC.exe" set "ISCC=D:\Environment\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC for /f "delims=" %%I in ('where iscc 2^>nul') do if not defined ISCC set "ISCC=%%I"

if defined ISCC (
    echo [6/6] 生成安装包...
    if not exist installer_output mkdir installer_output
    "%ISCC%" "/DMyAppVersion=%APP_VERSION%" scripts\installer.iss
    if errorlevel 1 (
        echo Inno Setup 编译失败！
        pause
        exit /b 1
    )
    if exist "installer_output\Drift的综合调试助手_安装包_v%APP_VERSION%.exe" (
        echo.
        echo ========================================
        echo 安装包已生成：installer_output\Drift的综合调试助手_安装包_v%APP_VERSION%.exe
        echo ========================================
        explorer installer_output
    ) else (
        echo 未找到预期的安装包输出文件。
        pause
        exit /b 1
    )
) else (
    echo.
    echo ========================================
    echo PyInstaller 打包完成！
    echo 程序目录：dist\Drift的综合调试助手\
    echo.
    echo 若要生成安装包，请先安装 Inno Setup：
    echo https://jrsoftware.org/isdl.php
    echo 安装后重新运行本脚本即可。
    echo ========================================
    explorer dist
)
echo.
pause
endlocal
exit /b 0

:check_environment
echo Checking build environment...
where python >nul 2>&1
if errorlevel 1 goto missing_python
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 goto missing_pyinstaller
if not exist "scripts\installer.iss" goto missing_installer
if not exist "scripts\build.spec" goto missing_spec
if not exist "scripts\generate_installer_assets.py" goto missing_assets
echo [OK] Build environment is ready.
exit /b 0

:missing_python
echo [ERROR] Python was not found.
exit /b 1

:missing_pyinstaller
echo [ERROR] PyInstaller was not found in this Python environment.
exit /b 1

:missing_installer
echo [ERROR] scripts\installer.iss is missing.
exit /b 1

:missing_spec
echo [ERROR] scripts\build.spec is missing.
exit /b 1

:missing_assets
echo [ERROR] scripts\generate_installer_assets.py is missing.
exit /b 1
