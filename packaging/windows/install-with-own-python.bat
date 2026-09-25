@echo off
rem One-time setup for the "own-python" package: creates .venv from YOUR 64-bit
rem Python 3.12 and installs the included wheels into it, fully offline.
rem
rem   install-with-own-python.bat                        (finds Python 3.12 itself)
rem   install-with-own-python.bat C:\path\to\python.exe  (use this exact Python)
setlocal
cd /d "%~dp0"
title Crop Labeller - setup

if not exist "wheelhouse\" (
    echo.
    echo   Can't find the wheelhouse folder next to this file.
    echo   Please extract the WHOLE zip first ^(right-click it, then "Extract All..."^).
    goto :fail
)

rem The included wheels are built for 64-bit CPython 3.12 exactly.
set "CHECK=import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) and sys.maxsize > 2**32 else 1)"

if "%~1"=="" goto :find_python
set PY="%~1"
%PY% -c "%CHECK%" >nul 2>&1 && goto :have_python
echo.
echo   "%~1" is not a 64-bit Python 3.12.
goto :wrong_python

:find_python
set PY=py -3.12
%PY% -c "%CHECK%" >nul 2>&1 && goto :have_python
set PY=python
%PY% -c "%CHECK%" >nul 2>&1 && goto :have_python
set PY=python3
%PY% -c "%CHECK%" >nul 2>&1 && goto :have_python
echo.
echo   Couldn't find a 64-bit Python 3.12 on this computer.

:wrong_python
echo   The included packages only work with 64-bit Python 3.12. Either:
echo     - run this again with the full path to your python.exe, e.g.
echo         install-with-own-python.bat C:\Users\you\AppData\Local\Programs\Python\Python312\python.exe
echo     - or use the other download, crop-labeller-...-windows-offline.zip,
echo       which has Python built in and needs no setup.
goto :fail

:have_python
%PY% -c "import sys; print('  Using Python', sys.version.split()[0], 'at', sys.executable)"
echo.

if exist ".venv\" (
    echo   Removing the previous .venv folder ^(your data and results are not touched^)...
    rmdir /s /q ".venv" || goto :fail
)
echo   Creating .venv ...
%PY% -m venv .venv || goto :fail

echo   Installing packages from wheelhouse ^(offline, takes a minute^)...
".venv\Scripts\python.exe" -E -m pip install --no-index --find-links wheelhouse -r requirements.txt --disable-pip-version-check --quiet || goto :fail
".venv\Scripts\python.exe" -E -c "import streamlit, pandas, plotly" || goto :fail

echo.
echo   Setup finished. Double-click start-crop-labeller.bat to start the app.
echo.
call :maybe_pause
exit /b 0

:fail
echo.
echo   Setup did not finish - see the messages above.
echo.
call :maybe_pause
exit /b 1

:maybe_pause
if not defined CROP_LABELLER_NO_PAUSE pause
exit /b 0
