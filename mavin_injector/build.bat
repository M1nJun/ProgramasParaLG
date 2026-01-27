@echo off
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --noconsole --name "MavinModelInjector" --onedir app.py
