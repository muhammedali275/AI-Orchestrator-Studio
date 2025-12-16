@echo off
setlocal ENABLEDELAYEDEXPANSION
echo Starting ZainOne Orchestrator Studio Frontend...

REM Compute version from root package.json
set "_PKG_JSON="
for /f "usebackq delims=" %%A in (package.json) do set "_PKG_JSON=!_PKG_JSON! %%A"
for /f "tokens=2 delims=:," %%V in ('echo !_PKG_JSON! ^| findstr /i "\"version\""') do set "VERSION=%%~V"
set "VERSION=!VERSION: =!"
set "VERSION=!VERSION:\"=!"
if not defined VERSION set "VERSION=dev"
echo Detected version: !VERSION!
set "REACT_APP_VERSION=!VERSION!"

cd frontend
npm start
