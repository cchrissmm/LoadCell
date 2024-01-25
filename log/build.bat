@echo off

REM Change to your Python script's name
SET PYTHON_SCRIPT=logger.py

REM Building the executable
REM pyinstaller --onefile --windowed %PYTHON_SCRIPT%
REM pyinstaller --onefile %PYTHON_SCRIPT%
pyinstaller %PYTHON_SCRIPT%

echo Build and copy process completed.
pause