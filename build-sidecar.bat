@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo [1/5] Building sidecar with PyInstaller...
python -m PyInstaller scraper-sidecar.spec --noconfirm --clean
if errorlevel 1 exit /b 1

echo [2/5] Installing Chromium into build/sidecar/ms-playwright...
if not exist "build\sidecar" mkdir "build\sidecar"
set "PLAYWRIGHT_BROWSERS_PATH=%CD%\build\sidecar\ms-playwright"
python -m playwright install chromium
if errorlevel 1 exit /b 1

echo [3/5] Copying sidecar to Tauri binaries...
copy /Y "dist\scraper-sidecar.exe" "src-tauri\binaries\scraper-sidecar-x86_64-pc-windows-msvc.exe" >nul
if errorlevel 1 exit /b 1

echo [4/5] Copying Playwright browsers to Tauri binaries...
if exist "src-tauri\binaries\ms-playwright" rmdir /S /Q "src-tauri\binaries\ms-playwright"
xcopy /E /I /Y "build\sidecar\ms-playwright" "src-tauri\binaries\ms-playwright" >nul
if errorlevel 1 exit /b 1

echo [5/5] Copying browsers next to dist exe for standalone test...
if exist "dist\ms-playwright" rmdir /S /Q "dist\ms-playwright"
xcopy /E /I /Y "build\sidecar\ms-playwright" "dist\ms-playwright" >nul

echo.
echo Done. Sidecar: src-tauri\binaries\scraper-sidecar-x86_64-pc-windows-msvc.exe
echo Test: set PLAYWRIGHT_BROWSERS_PATH=dist\ms-playwright ^& dist\scraper-sidecar.exe
echo Build app: npm run tauri build
