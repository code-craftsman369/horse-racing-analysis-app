@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo Starting Horse Racing Analysis App...
echo Please wait, browser will open automatically.
echo.
echo To stop: press Ctrl+C in this window
echo.

streamlit run app.py --server.port 8501 --server.headless false

pause
