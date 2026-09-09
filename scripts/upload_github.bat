@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

git rev-parse --is-inside-work-tree >nul 2>&1 || (echo Not a Git repository.& pause & exit /b 1)
git remote get-url origin >nul 2>&1 || (echo Missing Git remote: origin.& pause & exit /b 1)

git add -A
git diff --cached --quiet || git commit -m "chore: update project"
git push --force origin main
if errorlevel 1 (
  echo.
  echo Upload failed. Check your network and GitHub sign-in, then retry.
  pause
  exit /b 1
)

echo.
echo GitHub has been replaced with the current main branch.
pause
