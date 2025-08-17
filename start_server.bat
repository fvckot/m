@echo off
echo Starting Aurevtech AI Coder Server...
echo.

cd /d "C:\Users\aams5\Workspace\medical_coding_engine"

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing dependencies...
uv pip install -r requirements.txt

echo Starting server...
echo Server will be available at: http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
echo.

python main.py

pause