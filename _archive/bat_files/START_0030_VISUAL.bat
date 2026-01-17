@echo off
echo Starting 0030 ORB Visual Dashboard...
cd /d "%~dp0"
streamlit run orb_0030_visual.py --server.port 8502
