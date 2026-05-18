@echo off
cd /d "%~dp0"
pip install -r requirements.txt
pyinstaller --noconsole --onefile --name SerialSniffer --windowed main.py
echo Build complete. Find SerialSniffer.exe in the dist/ folder.
