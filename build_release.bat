@echo off
chcp 65001 >nul 2>&1
title LabelTorch - Build Release

echo ========================================
echo   LabelTorch - Build Release Package
echo ========================================
echo.

set PYTHON=F:\A\anaconda\envs\labeltorch\python.exe
set PROJECT_ROOT=%~dp0

REM --- Install PyInstaller ---
echo [1/4] Installing PyInstaller...
%PYTHON% -m pip install pyinstaller -q

REM --- Clean old build ---
echo [2/4] Cleaning old build...
if exist "%PROJECT_ROOT%dist" rmdir /s /q "%PROJECT_ROOT%dist"
if exist "%PROJECT_ROOT%build" rmdir /s /q "%PROJECT_ROOT%build"
if exist "%PROJECT_ROOT%LabelTorch.spec" del /q "%PROJECT_ROOT%LabelTorch.spec"

REM --- Build ---
echo [3/4] Building release package...
cd /d "%PROJECT_ROOT%"

%PYTHON% -m PyInstaller ^
    --name LabelTorch ^
    --onedir ^
    --windowed ^
    --icon NONE ^
    --add-data "labeltorch\app\infra\db\migrations;labeltorch\app\infra\db\migrations" ^
    --hidden-import=labeltorch.app.infra.db.migrations.v001_initial ^
    --hidden-import=labeltorch.app.domain.enums ^
    --hidden-import=ultralytics ^
    --hidden-import=ultralytics.nn ^
    --hidden-import=ultralytics.models ^
    --hidden-import=ultralytics.engine ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --noconfirm ^
    labeltorch\main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

REM --- Copy launcher ---
echo [4/5] Copying launcher.bat...
copy /y "%PROJECT_ROOT%dist\launcher.bat" "%PROJECT_ROOT%dist\LabelTorch\launcher.bat" >nul 2>&1
if not exist "%PROJECT_ROOT%dist\LabelTorch\launcher.bat" (
    echo @echo off> "%PROJECT_ROOT%dist\LabelTorch\launcher.bat"
    echo cd /d "%%~dp0">> "%PROJECT_ROOT%dist\LabelTorch\launcher.bat"
    echo start "" "LabelTorch.exe">> "%PROJECT_ROOT%dist\LabelTorch\launcher.bat"
)

echo [5/5] Build complete!
echo.
echo Output directory: %PROJECT_ROOT%dist\LabelTorch\
echo.
echo Double-click: dist\LabelTorch\launcher.bat
echo Or run:        dist\LabelTorch\LabelTorch.exe
echo.
pause
