@echo off
rem ============================================
rem  dsh-plugin-guard - Windows launcher
rem  DSH plugin conflict monitor + one-click
rem  enable/disable. Usage:
rem    guard.bat status              show status
rem    guard.bat scan                scan all plugins
rem    guard.bat check               detect conflicts/risks
rem    guard.bat disable <id>        disable a plugin
rem    guard.bat enable  <id>        enable a plugin
rem    guard.bat --profile <name>    choose profile (default web)
rem ============================================
chcp 65001 >nul
setlocal
set "SCRIPT_DIR=%~dp0"

where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js first.
    pause
    exit /b 1
)

node "%SCRIPT_DIR%dsh-plugin-guard\lib\cli.js" %*
set RC=%errorlevel%
echo.
if %RC% EQU 0 goto :ok
echo [INFO] Finished with warnings/errors (code %RC%).
goto :end

:ok
echo Done.

:end
endlocal
exit /b %RC%
