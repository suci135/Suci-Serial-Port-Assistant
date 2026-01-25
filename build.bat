@echo off
chcp 65001 >nul
echo ========================================
echo    Suci串口助手 - 打包工具
echo ========================================
echo.

echo [1/3] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo 完成！
echo.

echo [2/3] 开始打包...
pyinstaller build.spec --clean
echo.

if %errorlevel% equ 0 (
    echo [3/3] 打包成功！
    echo.
    echo ========================================
    echo 可执行文件位置: dist\Suci串口助手.exe
    echo ========================================
    echo.
    echo 按任意键打开 dist 文件夹...
    pause >nul
    explorer dist
) else (
    echo [3/3] 打包失败！
    echo 请检查错误信息。
    echo.
    pause
)
