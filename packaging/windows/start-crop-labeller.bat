@echo off
rem Double-click launcher for the offline Windows packages (USAGE-GUIDELINES, section 8).
rem Uses the bundled python\ if present, else the .venv made by install-with-own-python.bat.
setlocal
cd /d "%~dp0"
title Crop Labeller

set "PY="
if exist "python\python.exe" set "PY=python\python.exe"
if not defined PY if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY goto :no_python

echo Starting Crop Labeller - your browser will open in a few seconds.
echo Keep this window open while you work; close it to stop the app.
echo.

rem -E -s: ignore PYTHON* environment variables and per-user site-packages, so
rem other Python setups on this machine can't interfere.
"%PY%" -E -s run.py %*
if errorlevel 1 (
    echo.
    echo   Crop Labeller stopped with an error - see the messages above.
    call :maybe_pause
    exit /b 1
)
exit /b 0

:no_python
echo.
if exist "install-with-own-python.bat" (
    echo   Setup hasn't been run yet. Double-click install-with-own-python.bat first,
    echo   then double-click start-crop-labeller.bat again.
) else (
    echo   Can't find python\python.exe next to this file.
    echo   Please extract the WHOLE zip first ^(right-click it, then "Extract All..."^),
    echo   and double-click start-crop-labeller.bat inside the extracted folder.
)
echo.
call :maybe_pause
exit /b 1

:maybe_pause
if not defined CROP_LABELLER_NO_PAUSE pause
exit /b 0
