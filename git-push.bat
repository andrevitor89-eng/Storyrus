@echo off
cd /d "%~dp0"
set "OUT=%~dp0git-push.log"
echo === commit/push === > "%OUT%"
git add . >> "%OUT%" 2>&1
git commit -m "docs: DEPLOY.md com passo a passo (Vercel + Render)" >> "%OUT%" 2>&1
echo COMMIT_EXIT=%errorlevel% >> "%OUT%"
git push >> "%OUT%" 2>&1
echo PUSH_EXIT=%errorlevel% >> "%OUT%"
echo. >> "%OUT%"
git log --oneline -3 >> "%OUT%" 2>&1
echo DONE>> "%OUT%"
