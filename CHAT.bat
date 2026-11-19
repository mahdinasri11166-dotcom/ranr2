@echo off
chcp 65001 >nul
title GGUF Desktop Chat v2.5
cd /d "%~dp0"
echo GGUF Desktop Chat v2.5
echo Mehdi Tariri / Mohsen Tarifii
echo.

if not exist "models" mkdir models 2>nul
if not exist "sessions" mkdir sessions 2>nul
if not exist "workspace" mkdir workspace 2>nul
if not exist "memory" mkdir memory 2>nul

set "PY="
if exist "python\python.exe" set "PY=%~dp0python\python.exe"
if not defined PY (
  where python >nul 2>&1 && for /f "delims=" %%P in ('where python') do (
    if not defined PY set "PY=%%P"
  )
)
if not defined PY (
  echo [ERROR] Python پیدا نشد. ابتدا SETUP.bat را اجرا کنید.
  pause
  exit /b 1
)

echo Using: %PY%
"%PY%" -c "import customtkinter" 2>nul
if errorlevel 1 (
  echo [WARN] customtkinter نیست — در حال نصب...
  "%PY%" -m pip install customtkinter --quiet
  if errorlevel 1 (
    echo [ERROR] نصب customtkinter ناموفق. اینترنت را بررسی کنید یا SETUP.bat را بزنید.
    pause
    exit /b 1
  )
)
"%PY%" -c "import llama_cpp" 2>nul
if errorlevel 1 (
  echo [WARN] llama-cpp-python نیست — در حال نصب (ممکن است چند دقیقه طول بکشد)...
  "%PY%" -m pip install llama-cpp-python --quiet
  if errorlevel 1 (
    echo [ERROR] نصب llama-cpp-python ناموفق بود.
    echo بدون آن مدل GGUF لود نمی‌شود. SETUP.bat را با اینترنت اجرا کنید.
    pause
    exit /b 1
  )
)

if not exist "scripts\python\desktop_chat.py" (
  echo [ERROR] scripts\python\desktop_chat.py پیدا نشد. فایل‌های پروژه ناقص است.
  pause
  exit /b 1
)

echo Starting UI...
"%PY%" "%~dp0scripts\python\desktop_chat.py"
set ERR=%ERRORLEVEL%
if not "%ERR%"=="0" (
  echo.
  echo Chat با کد %ERR% بسته شد.
  echo راهنما:
  echo   1^) SETUP.bat
  echo   2^) scripts\doctor.bat
  echo   3^) مدل .gguf را در models\ بگذارید
  pause
)
exit /b %ERR%
