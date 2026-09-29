@echo off
cd /d %~dp0
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pytest -q
uvicorn app.main:app --reload
