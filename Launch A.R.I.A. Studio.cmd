@echo off
setlocal
title A.R.I.A. Studio Launcher
set "SCRIPT_DIR=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%start-site.ps1" -SkipModelWarmup
endlocal
