@echo off
cd /d "%~dp0"
set "LOG=%~dp0apply.log"
echo Aplicando mudancas - rebuild docker (web + api + worker)... > "%LOG%"
echo. >> "%LOG%"
docker compose up -d --build web api worker >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo EXIT_CODE=%errorlevel% >> "%LOG%"
docker compose ps >> "%LOG%" 2>&1
