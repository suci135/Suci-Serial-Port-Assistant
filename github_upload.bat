@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    GitHub Upload Script
echo ========================================
echo.

:: Configure Git user info
echo [Config] Setting Git user information...
git config --global user.name "Su Ci"
git config --global user.email "3314881686@qq.com"
echo [Done] Git user info configured

echo.
echo [Verify] Current Git config:
git config --global user.name
git config --global user.email

echo.
:: Check if in Git repository
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Not a Git repository!
    echo Please run: git init
    pause
    exit /b 1
)

:: Show current status
echo [Info] Checking Git status...
git status --short

echo.
echo [Info] Adding all changed files...
git add .

:: Check if there are files to commit
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo [Info] No new changes to commit
    echo.
    set /p choice="Continue to push to remote? (y/n): "
    if /i not "!choice!"=="y" (
        echo Operation cancelled
        pause
        exit /b 0
    )
) else (
    echo.
    echo [Info] Files to be committed:
    git diff --cached --name-only
    echo.
    
    :: Get commit message
    set /p commit_msg="Enter commit message (press Enter for default): "
    if "!commit_msg!"=="" (
        for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set current_date=%%c-%%a-%%b
        for /f "tokens=1-2 delims=: " %%a in ('time /t') do set current_time=%%a:%%b
        set commit_msg=Auto update - !current_date! !current_time!
    )
    
    echo [Info] Committing changes...
    git commit -m "!commit_msg!"
    
    if !errorlevel! neq 0 (
        echo [Error] Commit failed!
        pause
        exit /b 1
    )
)

echo.
echo [Info] Pushing to remote repository...
git push

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    Successfully uploaded to GitHub!
    echo ========================================
) else (
    echo.
    echo [Error] Push failed! Possible reasons:
    echo 1. Network connection issues
    echo 2. Remote repository not configured
    echo 3. Authentication failed
    echo.
    echo For first-time push, set up remote repository:
    echo git remote add origin https://github.com/username/repository.git
    echo git branch -M main
    echo git push -u origin main
)

echo.
pause