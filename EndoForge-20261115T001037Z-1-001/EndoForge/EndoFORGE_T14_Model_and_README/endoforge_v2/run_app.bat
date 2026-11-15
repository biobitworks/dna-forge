@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8503
) else (
  "..\endoforge\.venv\Scripts\python.exe" -m streamlit run app.py --server.port 8503
)
pause
