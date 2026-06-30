@echo off
cd /d "%~dp0"
set "OUT=%~dp0git-push.log"
echo === commit/push === > "%OUT%"
git rm --cached apps/web/tsconfig.tsbuildinfo >> "%OUT%" 2>&1
git add . >> "%OUT%" 2>&1
git commit -m "chore: ignora tsconfig.tsbuildinfo (artefato de build)" >> "%OUT%" 2>&1
echo COMMIT_EXIT=%errorlevel% >> "%OUT%"
git push >> "%OUT%" 2>&1
echo PUSH_EXIT=%errorlevel% >> "%OUT%"
echo. >> "%OUT%"
git log --oneline -3 >> "%OUT%" 2>&1
echo DONE>> "%OUT%"
