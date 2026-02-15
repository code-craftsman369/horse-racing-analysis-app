@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo Installing required packages...
echo This may take a few minutes. Please wait.
echo.

pip install pandas matplotlib numpy openpyxl selenium webdriver-manager streamlit

if errorlevel 1 (
    echo.
    echo ERROR: Installation failed.
    echo Please contact your developer.
) else (
    echo.
    echo Installation complete!
    echo Please run run_app.bat to start the app.
)

echo.
pause
