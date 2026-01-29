@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:main
cls
echo ========================================
echo        GitHub 助手工具
echo ========================================
echo.
echo 请选择操作：
echo 1. 快速上传 (添加所有文件并推送)
echo 2. 查看状态
echo 3. 设置远程仓库
echo 4. 查看提交历史
echo 5. 强制推送 (谨慎使用)
echo 6. 配置 Git 用户信息
echo 0. 退出
echo.
set /p choice="请输入选项 (0-6): "

if "%choice%"=="1" goto quick_upload
if "%choice%"=="2" goto show_status
if "%choice%"=="3" goto setup_remote
if "%choice%"=="4" goto show_history
if "%choice%"=="5" goto force_push
if "%choice%"=="6" goto config_user
if "%choice%"=="0" goto exit
goto main

:quick_upload
echo.
echo ========================================
echo        快速上传到 GitHub
echo ========================================

:: 检查 Git 用户配置
call :check_git_config
if %errorlevel% neq 0 goto main

:: 检查 Git 仓库
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 当前目录不是 Git 仓库！
    echo.
    set /p init_choice="是否初始化 Git 仓库？(y/n): "
    if /i "!init_choice!"=="y" (
        git init
        echo Git 仓库已初始化
    ) else (
        goto main
    )
)

echo.
echo [信息] 当前状态：
git status --short

echo.
echo [信息] 添加所有文件...
git add .

:: 检查是否有更改
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo [信息] 没有新的更改需要提交
    pause
    goto main
)

echo.
echo [信息] 将要提交的文件：
git diff --cached --name-only

echo.
set /p commit_msg="请输入提交信息 (回车使用默认): "
if "%commit_msg%"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set current_date=%%a-%%b-%%c
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set current_time=%%a:%%b
    set commit_msg=Auto update - !current_date! !current_time!
)

echo [信息] 提交更改...
git commit -m "%commit_msg%"

if %errorlevel% neq 0 (
    echo [错误] 提交失败！
    pause
    goto main
)

echo [信息] 推送到远程仓库...
git push

if %errorlevel% equ 0 (
    echo.
    echo ✅ 成功上传到 GitHub！
) else (
    echo.
    echo ❌ 推送失败！
    echo.
    echo 可能需要设置远程仓库或检查网络连接
    set /p setup_choice="是否现在设置远程仓库？(y/n): "
    if /i "!setup_choice!"=="y" goto setup_remote
)

pause
goto main

:show_status
echo.
echo ========================================
echo           Git 状态信息
echo ========================================
echo.
echo [当前分支和状态]
git status
echo.
echo [远程仓库信息]
git remote -v
echo.
pause
goto main

:setup_remote
echo.
echo ========================================
echo         设置远程仓库
echo ========================================
echo.
echo 当前远程仓库：
git remote -v
echo.
set /p repo_url="请输入 GitHub 仓库 URL: "
if "%repo_url%"=="" (
    echo 未输入 URL，返回主菜单
    pause
    goto main
)

echo.
echo [信息] 设置远程仓库...
git remote remove origin 2>nul
git remote add origin %repo_url%

echo [信息] 设置主分支...
git branch -M main

echo [信息] 首次推送...
git push -u origin main

if %errorlevel% equ 0 (
    echo ✅ 远程仓库设置成功！
) else (
    echo ❌ 设置失败，请检查 URL 和网络连接
)

pause
goto main

:show_history
echo.
echo ========================================
echo          提交历史记录
echo ========================================
echo.
git log --oneline -10
echo.
pause
goto main

:force_push
echo.
echo ========================================
echo           强制推送
echo ========================================
echo.
echo ⚠️  警告：强制推送会覆盖远程仓库的历史记录！
echo    这可能会导致其他协作者的工作丢失！
echo.
set /p force_choice="确定要强制推送吗？(输入 YES 确认): "
if not "%force_choice%"=="YES" (
    echo 操作已取消
    pause
    goto main
)

echo [信息] 执行强制推送...
git push --force

if %errorlevel% equ 0 (
    echo ✅ 强制推送完成！
) else (
    echo ❌ 强制推送失败！
)

pause
goto main

:exit
echo.
echo 感谢使用 GitHub 助手工具！
echo.
pause
exit /b 0

:: 检查 Git 用户配置
:check_git_config
echo [信息] 检查 Git 用户配置...

:: 检查用户名
for /f "tokens=*" %%i in ('git config --global user.name 2^>nul') do set git_username=%%i
:: 检查邮箱
for /f "tokens=*" %%i in ('git config --global user.email 2^>nul') do set git_email=%%i

if "%git_username%"=="" (
    echo [警告] 未配置 Git 用户名
    set need_config=1
) else (
    echo [信息] Git 用户名: %git_username%
)

if "%git_email%"=="" (
    echo [警告] 未配置 Git 邮箱
    set need_config=1
) else (
    echo [信息] Git 邮箱: %git_email%
)

if defined need_config (
    echo.
    echo [提示] 需要配置 Git 用户信息才能提交代码
    set /p auto_config="是否现在配置？(y/n): "
    if /i "!auto_config!"=="y" (
        call :config_user
        exit /b 0
    ) else (
        echo [错误] 未配置用户信息，无法提交
        pause
        exit /b 1
    )
)

exit /b 0

:: 配置 Git 用户信息
:config_user
echo.
echo ========================================
echo        配置 Git 用户信息
echo ========================================
echo.

:: 显示当前配置
echo [当前配置]
echo 用户名: 
git config --global user.name 2>nul || echo (未设置)
echo 邮箱: 
git config --global user.email 2>nul || echo (未设置)
echo.

set /p new_username="Suci"
if not "%new_username%"=="" (
    git config --global user.name "%new_username%"
    echo ✅ 用户名已设置为: %new_username%
)

set /p new_email="3314881686@qq.com"
if not "%new_email%"=="" (
    git config --global user.email "%new_email%"
    echo ✅ 邮箱已设置为: %new_email%
)

echo.
echo [更新后的配置]
echo 用户名: 
git config --global user.name
echo 邮箱: 
git config --global user.email

echo.
echo ✅ Git 用户信息配置完成！
pause
goto main