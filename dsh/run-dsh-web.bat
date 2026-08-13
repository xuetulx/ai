@echo off
setlocal EnableExtensions
title DSH Web Server

rem ============================================================
rem  One-click launcher for the DeepSeek DSH web server.
rem  Runs: npx @deepseek-ai/dsh web
rem  Then automatically opens Edge in app mode (application window):
rem      msedge.exe --app=http://127.0.0.1:3080/ --app-launch-source=4
rem ============================================================

set "PORT=3080"
set "URL=http://127.0.0.1:3080/"
set "EDGE=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
set "WAIT_SEC=120"

rem Run from the folder this script lives in
cd /d "%~dp0"

rem --- If the server is already running, skip npx and just open the browser ---
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $c = New-Object System.Net.Sockets.TcpClient; $c.Connect('127.0.0.1',%PORT%); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo Server already running on port %PORT% - opening the Edge app window...
    goto open
)

rem --- Make sure npx is available ---
where npx >nul 2>&1
if errorlevel 1 (
    echo npx was not found. Please install Node.js first.
    pause
    exit /b 1
)

rem --- Hidden helper: opens the Edge app window as soon as the server is ready ---
start "" /b powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "$d=(Get-Date).AddSeconds(%WAIT_SEC%); do { try { $c=New-Object System.Net.Sockets.TcpClient; $c.Connect('127.0.0.1',%PORT%); $c.Close(); if (Test-Path '%EDGE%') { Start-Process -FilePath '%EDGE%' -ArgumentList '--app=%URL%','--app-launch-source=4' } else { Start-Process '%URL%' }; exit 0 } catch { Start-Sleep -Milliseconds 500 } } while ((Get-Date) -lt $d)"

echo Starting DSH web server...
npx --yes @deepseek-ai/dsh web
pause
exit /b 0

:open
rem --- Open the Edge app window ---
if exist "%EDGE%" (
    start "" "%EDGE%" --app="%URL%" --app-launch-source=4
) else (
    echo Edge not found at %EDGE% - opening with the default browser instead.
    start "" "%URL%"
)
timeout /t 2 >nul
exit /b 0
