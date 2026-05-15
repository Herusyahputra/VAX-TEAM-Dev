@echo off
setlocal
echo ============================================
echo      [ VAX STUDIO - GITHUB PUSH TOOL ]
echo ============================================
echo.

:: Set current directory
cd /d "%~dp0"

:: Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not in PATH.
    echo Please install Git from https://git-scm.com/
    pause
    exit /b
)

:: Initialize git if not already
if not exist .git (
    echo [1/4] Initializing git repository...
    git init
    git checkout -b main
)

:: Set remote URL
echo [2/4] Configuring remote origin...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/RamadanMufian/vax-sd-.git

:: Add and commit
echo [3/4] Staging and committing files...
git add .
git commit -m "Update VAX Studio: Generative Pipeline and Scientific Validation"

:: Push
echo [4/4] Pushing to GitHub (main branch)...
echo.
echo NOTE: You may be asked to log in to GitHub in a popup window.
echo.
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo [!] Push failed. Trying to push to 'master' branch instead...
    git push -u origin master
)

echo.
echo ============================================
echo             PROCESS FINISHED
echo ============================================
echo.
pause
