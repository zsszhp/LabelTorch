@echo off
chcp 65001 >nul 2>&1
title LabelTorch

echo ========================================
echo   LabelTorch - Industrial Defect Detection Tool
echo ========================================
echo.

REM --- Check conda env ---
where F:\A\anaconda\envs\labeltorch\python.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Cannot find Python in labeltorch env
    echo Please make sure the conda env exists: F:\A\anaconda\envs\labeltorch
    pause
    exit /b 1
)

set PYTHON=F:\A\anaconda\envs\labeltorch\python.exe
set PROJECT_ROOT=%~dp0

REM --- Check dependencies ---
echo [1/3] Checking dependencies...
%PYTHON% -c "import PySide6" 2>nul
if %errorlevel% neq 0 (
    echo [INSTALL] Installing PySide6...
    %PYTHON% -m pip install PySide6>=6.5 -q
)

%PYTHON% -c "import PIL" 2>nul
if %errorlevel% neq 0 (
    echo [INSTALL] Installing Pillow...
    %PYTHON% -m pip install Pillow -q
)

%PYTHON% -c "import ultralytics" 2>nul
if %errorlevel% neq 0 (
    echo [INSTALL] Installing Ultralytics...
    %PYTHON% -m pip install ultralytics>=8.0 -q
)

echo [2/3] Running startup check...
%PYTHON% -c "from labeltorch.app.infra.startup_check import StartupCheck; c=StartupCheck(); c.run_all(); print(c.get_summary_text())" 2>nul

echo [3/3] Starting LabelTorch...
echo.
%PYTHON% -m labeltorch

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] LabelTorch exited with error code %errorlevel%
    pause
)
