@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM build.bat  —  Video-Tagger Windows build script
REM Run from the project root:  build.bat
REM Output:  dist\VideoTagger\VideoTagger.exe
REM ─────────────────────────────────────────────────────────────────────────────

setlocal EnableDelayedExpansion

echo.
echo ══════════════════════════════════════════
echo   Video-Tagger  ^|  PyInstaller build
echo ══════════════════════════════════════════
echo.

REM ── 1. Check virtual environment ─────────────────────────────────────────────
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo         Create it with:  python -m venv venv
    echo         Then install:    pip install -r requirements.txt
    exit /b 1
)

call .venv\Scripts\activate.bat
echo [OK] Virtual environment activated.

REM ── 2. Check PyInstaller ──────────────────────────────────────────────────────
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller not found. Installing...
    pip install pyinstaller
)
echo [OK] PyInstaller ready.

REM ── 3. Check assets folder ───────────────────────────────────────────────────
if not exist "src\ui\resources\icons\icon_cic.png" (
    echo [WARN] src\ui\resources\icons\icon_cic.png not found.
    echo        The build will continue but the executable will have no icon.
    echo        Place a valid .ico file at ui\resources\icons\icon_cic.png to fix this.
    echo.
)

REM ── 4. Clean previous build ──────────────────────────────────────────────────
if exist "dist\VideoTagger" (
    echo [INFO] Removing previous dist\VideoTagger...
    rmdir /s /q "dist\VideoTagger"
)
if exist "build" (
    rmdir /s /q "build"
)
echo [OK] Clean complete.

REM ── 5. Run PyInstaller ───────────────────────────────────────────────────────
echo.
echo [INFO] Running PyInstaller...
echo.
pyinstaller app.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller failed. Check the output above.
    exit /b 1
)

REM ── 6. Verify output ─────────────────────────────────────────────────────────
if not exist "dist\VideoTagger\VideoTagger.exe" (
    echo [ERROR] Build completed but VideoTagger.exe was not found in dist\.
    exit /b 1
)

REM ── 7. Print summary ─────────────────────────────────────────────────────────
echo.
echo ══════════════════════════════════════════
echo   Build successful!
echo ══════════════════════════════════════════
echo.
echo   Executable : dist\VideoTagger\VideoTagger.exe
echo   Distribute : copy the entire dist\VideoTagger\ folder
echo.
for /f "tokens=3" %%s in ('dir /s /-c "dist\VideoTagger" ^| find "File(s)"') do (
    echo   Bundle size: %%s bytes
)
echo.
