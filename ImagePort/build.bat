@echo off
setlocal
cd /d "%~dp0"
set VER=1.0.1
set OUT=releases\ImagePort-%VER%-win64.exe
if exist "%OUT%" (
  echo %OUT% already exists. Choose a new version instead of overwriting it.
  exit /b 1
)
py -3 -m pip install -r requirements.txt
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --exclude-module numpy --name ImagePort-%VER%-win64 --distpath releases --workpath build --specpath build main.py
if errorlevel 1 exit /b 1
if exist build rmdir /s /q build
echo Built %OUT%
