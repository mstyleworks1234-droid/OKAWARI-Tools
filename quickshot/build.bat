@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "VER=1.1.16"
set "NAME=QuickShot-%VER%-win64"
set "OUT=%~dp0..\releases\%NAME%.exe"
if exist "%OUT%" (
  echo Release already exists. Refusing to overwrite:
  echo %OUT%
  exit /b 1
)
py -3 -m pip install --disable-pip-version-check -r "%~dp0requirements.txt"
if errorlevel 1 exit /b 1
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name %NAME% --add-data "extension;extension" main.py
if errorlevel 1 exit /b 1
if not exist "dist\%NAME%.exe" (
  echo EXE was not produced.
  exit /b 1
)
copy /B /Y "dist\%NAME%.exe" "%OUT%" >nul
if errorlevel 1 exit /b 1
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q "%NAME%.spec" 2>nul
echo Built: %OUT%
exit /b 0
