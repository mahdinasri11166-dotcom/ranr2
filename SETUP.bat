@echo off
chcp 65001 >nul
title GGUF Runner Setup
cd /d "%~dp0"
echo ========================================================
echo  GGUF Runner Setup (offline-first)
echo  Mehdi Tariri / Mohsen Tarifii
echo ========================================================
echo.

if exist "python\python.exe" (
  "python\python.exe" -c "import llama_cpp, customtkinter" 2>nul
  if not errorlevel 1 (
    echo [OK] Offline Python + libraries already present.
    echo No internet needed. Add models to models\ and run CHAT.bat
    if /i not "%1"=="/silent" pause
    exit /b 0
  )
)

echo Bundled stack incomplete — running detect_and_setup (may need internet^)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\detect_and_setup.ps1"
set ERR=%ERRORLEVEL%
if /i not "%1"=="/silent" pause
exit /b %ERR%
