@echo off
chcp 65001 >nul
where pythonw >nul 2>&1
if errorlevel 1 (
    echo 找不到 Python，請先安裝 Python 3。
    pause
    exit /b 1
)
start "" pythonw "%~dp0mouse_writer_ui.pyw"
