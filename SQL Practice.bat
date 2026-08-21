@echo off
rem Launch the practice GUI with no console window behind it.
rem pythonw.exe is the windowed build of the interpreter; falls back to py -w.
setlocal
set "PYW=%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"
if exist "%PYW%" (
    start "" "%PYW%" "%~dp0gui.py"
) else (
    start "" pyw "%~dp0gui.py"
)
