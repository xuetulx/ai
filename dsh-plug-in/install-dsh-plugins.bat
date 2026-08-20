@echo off
rem ============================================
rem  DSH Plugin Batch Installer - Windows launcher
rem  Finds Git Bash from PATH, git.exe, or common install dirs
rem  Usage: install-dsh-plugins.bat [--full] [--profile web] [--yes]
rem ============================================
setlocal enabledelayedexpansion

set "BASH="

rem 1. Try bash.exe already in PATH
where bash >nul 2>nul
if %errorlevel% == 0 (
    set "BASH=bash"
    goto :run
)

rem 2. Try git.exe in PATH, derive bash.exe from its install dir
rem    Git for Windows layout: Git\cmd\git.exe  ->  Git\bin\bash.exe
where git >nul 2>nul
if %errorlevel% == 0 (
    for /f "delims=" %%a in ('where git') do (
        set "CANDIDATE=%%~dpa..\bin\bash.exe"
        if exist "!CANDIDATE!" (
            set "BASH=!CANDIDATE!"
            goto :run
        )
    )
)

rem 3. Search common installation locations
for %%p in (
    "C:\Program Files\Git\bin\bash.exe"
    "C:\Program Files (x86)\Git\bin\bash.exe"
    "%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
    "%USERPROFILE%\scoop\apps\git\current\bin\bash.exe"
    "%USERPROFILE%\scoop\apps\git-with-openssh\current\bin\bash.exe"
) do (
    if exist "%%~p" (
        set "BASH=%%~p"
        goto :run
    )
)

rem Not found anywhere
(
echo [ERROR] Git Bash not found.
echo.
echo Possible fixes:
echo   1. Install Git for Windows: https://git-scm.com/download/win
echo   2. Or add your bash.exe folder to the system PATH
echo.
echo Press any key to exit.
)
pause >nul
exit /b 1

:run
set "SCRIPT_DIR=%~dp0"
"%BASH%" "%SCRIPT_DIR%install-dsh-plugins.sh" %*
set "RC=%errorlevel%"
if %RC% neq 0 (
    echo.
    echo [INFO] Installer finished with errors. Press any key to close.
    pause >nul
)
endlocal
exit /b %RC%
