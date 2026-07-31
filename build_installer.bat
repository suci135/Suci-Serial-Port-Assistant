@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul
set "APP_VERSION=1.0.0"
title Suci串口助手 - 生成安装包

if /i "%~1"=="--check" goto check_environment

echo ========================================
echo    Suci串口助手 v%APP_VERSION% - 生成安装包
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
python tools\generate_installer_assets.py
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
pyinstaller build.spec --clean
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
    "%ISCC%" "/DMyAppVersion=%APP_VERSION%" installer.iss
    if errorlevel 1 (
        echo Inno Setup 编译失败！
        pause
        exit /b 1
    )
    if exist "installer_output\Suci串口助手_安装包_v%APP_VERSION%.exe" (
        echo.
        echo ========================================
        echo 安装包已生成：installer_output\Suci串口助手_安装包_v%APP_VERSION%.exe
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
    echo 程序目录：dist\Suci串口助手\
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
echo 正在检查打包环境...
where python >nul 2>&1 || (echo [失败] 未找到 Python & exit /b 1)
where pyinstaller >nul 2>&1 || (echo [失败] 未找到 PyInstaller & exit /b 1)
if not exist "installer.iss" (echo [失败] 缺少 installer.iss & exit /b 1)
if not exist "build.spec" (echo [失败] 缺少 build.spec & exit /b 1)
if not exist "tools\generate_installer_assets.py" (echo [失败] 缺少安装器资源生成脚本 & exit /b 1)
echo [通过] Python、PyInstaller 和打包脚本均可用。
exit /b 0
