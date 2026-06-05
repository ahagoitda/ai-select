@echo off
REM Quick launcher for MyAISelect (double-click this)
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe ai_select.py
) else (
    echo Virtual environment not found.
    echo Please run: python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
)