@echo off
cd /d "%~dp0apps\web"
echo === npm run build (igual ao da Vercel) === > "%~dp0build-check.log"
call npm run build >> "%~dp0build-check.log" 2>&1
echo BUILD_EXIT=%errorlevel% >> "%~dp0build-check.log"
echo DONE>> "%~dp0build-check.log"
