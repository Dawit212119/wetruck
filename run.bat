@echo off
REM Run script for FastAPI application
cd platform-backend
if exist src\main.py (
    echo Starting FastAPI server...
    echo Server will be available at: http://127.0.0.1:8000
    echo API Docs at: http://127.0.0.1:8000/docs
    echo.
    python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
) else (
    echo Error: src\main.py not found
    echo Please make sure you're running this from the platform-backend root directory
    pause
)




