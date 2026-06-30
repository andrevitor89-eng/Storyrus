@echo off
cd /d "%~dp0"
set "OUT=%~dp0git-commit.log"
echo === git commit/push === > "%OUT%"
git --version >> "%OUT%" 2>&1
git init >> "%OUT%" 2>&1
git config user.name "andrevitor89-eng" >> "%OUT%" 2>&1
git config user.email "andrevitor89-eng@users.noreply.github.com" >> "%OUT%" 2>&1
git remote remove origin 2>nul
git remote add origin https://github.com/andrevitor89-eng/Storyrus.git >> "%OUT%" 2>&1
git add . >> "%OUT%" 2>&1
git commit -m "feat: Story R Us - landing infantil, estudio sem login, ebook PDF, imagem realistica e storage MinIO" >> "%OUT%" 2>&1
echo COMMIT_EXIT=%errorlevel% >> "%OUT%"
git branch -M main >> "%OUT%" 2>&1
git push -u origin main >> "%OUT%" 2>&1
echo PUSH_EXIT=%errorlevel% >> "%OUT%"
echo. >> "%OUT%"
echo === ultimo commit === >> "%OUT%"
git log --oneline -2 >> "%OUT%" 2>&1
echo === checagem: .env esta fora do commit? === >> "%OUT%"
git ls-files >> "%OUT%" 2>&1
echo DONE>> "%OUT%"
