@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    一键上传到 GitHub 脚本
echo ========================================
echo.

:: 直接配置 Git 用户信息（避免复杂的检查逻辑）
echo [配置] 设置 Git 用户信息...
git config --global user.name "Su Ci"
git config --global user.email "3314881686@qq.com"
echo [完成] Git 用户信息已配置

echo.
echo [验证] 当前 Git 配置:
git config --global user.name
git config --global user.email

echo.
:: 检查是否在 Git 仓库中
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 当前目录不是 Git 仓库！
    echo 请先运行: git init
    pause
    exit /b 1
)

:: 显示当前状态
echo [信息] 检查当前 Git 状态...
git status --short

echo.
echo [信息] 添加所有更改的文件...
git add .

:: 检查是否有文件需要提交
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo [信息] 没有新的更改需要提交
    echo.
    set /p choice="是否继续推送到远程仓库？(y/n): "
    if /i not "!choice!"=="y" (
        echo 操作已取消
        pause
        exit /b 0
    )
) else (
    echo.
    echo [信息] 准备提交的文件:
    git diff --cached --name-only
    echo.
    
    :: 获取提交信息
    set /p commit_msg="请输入提交信息 (直接回车使用默认信息): "
    if "!commit_msg!"=="" (
        for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set current_date=%%c-%%a-%%b
        for /f "tokens=1-2 delims=: " %%a in ('time /t') do set current_time=%%a:%%b
        set commit_msg=Update files - !current_date! !current_time!
    )
    
    echo [信息] 提交更改...
    git commit -m "!commit_msg!"
    
    if !errorlevel! neq 0 (
        echo [错误] 提交失败！
        pause
        exit /b 1
    )
)

echo.
echo [信息] 推送到远程仓库...
git push

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    成功上传到 GitHub！
    echo ========================================
) else (
    echo.
    echo [错误] 推送失败！可能的原因：
    echo 1. 网络连接问题
    echo 2. 没有配置远程仓库
    echo 3. 认证失败
    echo.
    echo 如果是第一次推送，请先设置远程仓库：
    echo git remote add origin https://github.com/你的用户名/你的仓库名.git
    echo git branch -M main
    echo git push -u origin main
)

echo.
pause