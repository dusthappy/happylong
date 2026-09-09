@echo off
REM happlylong CLI launcher for Windows
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%~dp0happlylong.py" %*
) else (
    python "%~dp0happlylong.py" %*
)
