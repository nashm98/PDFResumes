@echo off
setlocal
cd /d "%~dp0"

REM start.bat se mantiene por compatibilidad, pero delega al lanzador unico.
call run_pdfresumes.bat

endlocal
