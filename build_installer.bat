@echo off
chcp 65001 >nul
echo ========================================
echo    Suci串口助手 - 生成安装包
echo ========================================
echo.

echo [1/5] 安装依赖...
pip install openpyxl pyinstaller pillow -q
echo 完成！
echo.

echo [2/5] 生成 .ico 图标...
python -c "from PIL import Image; img = Image.open('src/resource/Assistant.png'); img.save('src/resource/Assistant.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
if %errorlevel% neq 0 (
    echo 警告：图标转换失败，将使用默认图标
)
echo 完成！
echo.

echo [3/5] 清理旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo 完成！
echo.

echo [4/5] PyInstaller 打包...
pyinstaller build.spec --clean
if %errorlevel% neq 0 (
    echo 打包失败！请检查错误信息。
    pause
    exit /b 1
)
echo 完成！
echo.

echo [5/5] 生成安装包...
set ISCC=""
if exist "D:\Environment\Inno Setup 6\ISCC.exe" set ISCC="D:\Environment\Inno Setup 6\ISCC.exe"
where iscc >nul 2>&1 && set ISCC=iscc

if not %ISCC%=="" (
    if not exist installer_output mkdir installer_output
    %ISCC% installer.iss
    if exist "installer_output\Suci串口助手_安装包_v1.0.0.exe" (
        echo.
        echo ========================================
        echo 安装包已生成：installer_output\
        echo ========================================
        explorer installer_output
    ) else (
        echo Inno Setup 编译失败！
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
