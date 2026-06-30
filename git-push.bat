@echo off
cd /d "%~dp0"
set "OUT=%~dp0git-push.log"
echo === remove render.yaml do repo (mantem local) === > "%OUT%"
git rm --cached render.yaml >> "%OUT%" 2>&1
git add -A >> "%OUT%" 2>&1
git commit -m "chore: remove render.yaml do repositorio (repo agora 100%% frontend)" >> "%OUT%" 2>&1
echo COMMIT_EXIT=%errorlevel% >> "%OUT%"
git push >> "%OUT%" 2>&1
echo PUSH_EXIT=%errorlevel% >> "%OUT%"
echo. >> "%OUT%"
echo === arquivos no topo do repo === >> "%OUT%"
git ls-files --directory >> "%OUT%" 2>&1
git log --oneline -2 >> "%OUT%" 2>&1
echo DONE>> "%OUT%"
