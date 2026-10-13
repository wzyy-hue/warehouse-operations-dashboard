@echo off
chcp 65001 >nul
cd /d "%~dp0"
call D:\Miniconda3\Scripts\activate.bat warehouse
if errorlevel 1 (
  echo Failed to activate warehouse Conda environment.
  pause
  exit /b 1
)
python -m streamlit run app.py
pause
