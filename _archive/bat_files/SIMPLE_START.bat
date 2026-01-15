@echo off
echo Starting app with venv...
cd /d C:\Users\sydne\OneDrive\myprojectx
call .venv\Scripts\activate.bat
streamlit run app_trading_hub.py --server.port 8501
