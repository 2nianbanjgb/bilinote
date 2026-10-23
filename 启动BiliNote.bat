@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PORT=3015"
set "CONTAINER=bilinote"
set "SILENT=%~1"

echo ============================================
echo   BiliNote launcher
echo ============================================

rem --- 1. start Docker Desktop if it is not running ---
tasklist /FI "IMAGENAME eq Docker Desktop.exe" 2>nul | find /I "Docker Desktop.exe" >nul
if errorlevel 1 (
    echo [1/3] Docker Desktop is not running, starting it...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
) else (
    echo [1/3] Docker Desktop is already running.
)

rem --- 2. wait for the docker engine (max ~4 min) ---
echo [2/3] Waiting for the docker engine...
set /a n=0
:wait_engine
docker info >nul 2>&1
if not errorlevel 1 goto engine_ready
set /a n+=1
if !n! GEQ 80 goto engine_failed
ping -n 4 127.0.0.1 >nul
goto wait_engine

:engine_failed
echo.
echo [ERROR] Docker engine did not start within 4 minutes.
echo         Open Docker Desktop by hand, fix the error it shows, then run this file again.
if /I not "%SILENT%"=="/silent" pause
exit /b 1

:engine_ready
echo       Docker engine is up.

rem --- 3. start the container (create it on first ever run) ---
echo [3/3] Starting BiliNote container...
docker inspect --type container %CONTAINER% >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\start-bilinote.ps1" -Port %PORT%
) else (
    docker start %CONTAINER% >nul 2>&1
)

rem --- wait until the web UI answers (max ~80s) ---
set /a n=0
:wait_web
curl.exe -s -f -o nul --max-time 3 "http://127.0.0.1:%PORT%/api/sys_health"
if not errorlevel 1 goto web_ready
set /a n+=1
if !n! GEQ 40 goto web_slow
ping -n 3 127.0.0.1 >nul
goto wait_web

:web_slow
echo.
echo [WARN] Container is running but the web UI did not answer.
echo        Logs: docker exec %CONTAINER% tail -50 /var/log/supervisor/backend.log
if /I not "%SILENT%"=="/silent" pause
exit /b 1

:web_ready
echo.
echo BiliNote is ready: http://127.0.0.1:%PORT%/
if /I "%SILENT%"=="/silent" exit /b 0

start "" "http://127.0.0.1:%PORT%/"
exit /b 0
