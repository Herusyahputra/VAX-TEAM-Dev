@echo off
echo [VAX PROJECT PUSH SCRIPT]
echo.

:: Set current directory
cd /d "%~dp0"

:: Initialize git if not already
if not exist .git (
    echo Initializing git...
    git init
)

:: Add remote
echo Adding remote vax-sd...
git remote add vax-sd https://github.com/RamadanMufian/vax-sd-.git 2>nul
git remote set-url vax-sd https://github.com/RamadanMufian/vax-sd-.git

:: Add and commit
echo Staging files...
git add .
echo Committing changes...
git commit -m "Direct push from VAX Studio"

:: Push
echo Pushing to GitHub...
git push -u vax-sd main

echo.
echo Process finished.
pause
