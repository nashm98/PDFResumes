@echo off
setlocal
cd /d "%~dp0"

set "EXE_PATH=dist\PDFResumesApp.exe"

if not exist "%EXE_PATH%" (
  echo [INFO] No existe %EXE_PATH%. Se compilara automaticamente...
  call build_exe.bat
  if errorlevel 1 (
    echo [ERROR] No se pudo construir el ejecutable.
    pause
    exit /b 1
  )
)

echo [INFO] Ejecutando %EXE_PATH%...
start "" "%EXE_PATH%"

endlocal
