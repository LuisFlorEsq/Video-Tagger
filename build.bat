@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ───────────────────────────────────────────────────────────────
REM build.bat — Video-Tagger Windows build script
REM Output: dist\VideoTagger\VideoTagger.exe
REM ───────────────────────────────────────────────────────────────

set VENV_DIR=.venv
set SPEC_FILE=app.spec
set BUILD_LOG=logs\build.log
set OUTPUT_EXE=dist\VideoTagger\VideoTagger.exe

echo.
echo --------------------------------------------------------
echo   Video-Tagger ^| PyInstaller build
echo --------------------------------------------------------
echo.

REM ── 1. Check virtual environment ─────────────────────────
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at: %VENV_DIR%
    echo         Create it with: python -m venv %VENV_DIR%
    echo         Install deps:    python -m pip install -r requirements.txt
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
echo [OK] Virtual environment activated.

REM ── 2. Check PyInstaller ─────────────────────────────────
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller not found. Installing...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        exit /b 1
    )
)
echo [OK] PyInstaller ready.

REM ── 3. Check assets ──────────────────────────────────────
if not exist "src\ui\resources\icons\app_icon.ico" (
    echo [WARN] app_icon.ico not found at src\ui\resources\icons\
    echo        The build will continue but the executable may have no icon.
    echo.
)

REM ── 4. Clean previous build ──────────────────────────────
echo [INFO] Cleaning previous build artifacts...

if exist "dist\VideoTagger" rmdir /s /q "dist\VideoTagger"
if exist "build" rmdir /s /q "build"
if exist "%BUILD_LOG%" del /q "%BUILD_LOG%"

echo [OK] Clean complete.

REM ── 5. Run PyInstaller ───────────────────────────────────
echo.
echo [INFO] Running PyInstaller...
echo [INFO] Logging output to: %BUILD_LOG%
echo.

pyinstaller "%SPEC_FILE%" --noconfirm > "%BUILD_LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller failed. See %BUILD_LOG%
    exit /b 1
)

REM ── 6. Verify output ─────────────────────────────────────
if not exist "%OUTPUT_EXE%" (
    echo [ERROR] Build completed but executable not found:
    echo         %OUTPUT_EXE%
    exit /b 1
)

REM ── 7. Summary ───────────────────────────────────────────
echo.
echo --------------------------------------------------------
echo   Build successful!
echo --------------------------------------------------------
echo.
echo   Executable : %OUTPUT_EXE%
echo   Distribute : copy the entire dist\VideoTagger\ folder
echo.

for /f "tokens=3" %%s in ('dir /s /-c "dist\VideoTagger" ^| find "File(s)"') do (
    echo   Bundle size: %%s bytes
)

echo.
exit /b 0