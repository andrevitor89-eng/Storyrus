@echo off
cd /d "%~dp0"
set "OUT=%~dp0git-push.log"
echo === remove backend e e2e do repo (mantem local) === > "%OUT%"
git rm -r --cached backend >> "%OUT%" 2>&1
git rm -r --cached apps/web/e2e >> "%OUT%" 2>&1
git add -A >> "%OUT%" 2>&1
git commit -m "chore: remove backend e testes e2e do repositorio (mantidos localmente)" >> "%OUT%" 2>&1
echo COMMIT_EXIT=%errorlevel% >> "%OUT%"
git push >> "%OUT%" 2>&1
echo PUSH_EXIT=%errorlevel% >> "%OUT%"
echo. >> "%OUT%"
echo === confirma que backend/ e e2e/ sairam (nao devem aparecer) === >> "%OUT%"
git ls-files backend apps/web/e2e >> "%OUT%" 2>&1
echo (vazio acima = removidos) >> "%OUT%"
git log --oneline -2 >> "%OUT%" 2>&1
echo DONE>> "%OUT%"
