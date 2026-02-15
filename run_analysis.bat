@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo Starting analysis...
echo This may take about 30 minutes. Please wait.
echo.

python main_analysis.py

if errorlevel 1 (
    echo.
    echo ERROR: Please check settings.txt
) else (
    echo.
    echo DONE. Please check the output folder.
    echo Next: run run_app.bat to view the graphs.
)

echo.
pause
