@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"

set "VENV_DIR=%CD%\.venv"
set "PORT=8000"
set "APP_URL=http://localhost:%PORT%"

echo [1/5] Verificando Python...
where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON_CMD=python"
  ) else (
    echo [ERROR] Python no esta instalado o no esta en PATH.
    echo Instala Python 3 desde https://www.python.org/downloads/
    pause
    exit /b 1
  )
)

echo [2/5] Preparando entorno virtual...
if not exist "%VENV_DIR%\Scripts\python.exe" (
  call %PYTHON_CMD% -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
  )
)

echo [3/5] Instalando dependencias ^(si aplica^)...
if exist requirements.txt (
  call "%VENV_DIR%\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] No se pudieron instalar dependencias.
    echo [TIP] Revisa conexion de red o ejecuta desde una carpeta local corta (no OneDrive profundo).
    pause
    exit /b 1
  )
) else (
  echo [INFO] No existe requirements.txt, continuando...
)

echo [4/5] Verificando estado del servidor...
call "%VENV_DIR%\Scripts\python.exe" -c "import socket; s=socket.socket(); s.settimeout(1.5); rc=s.connect_ex(('127.0.0.1', %PORT%)); s.close(); print('UP' if rc==0 else 'DOWN')" > "%TEMP%\pdfresumes_port_status.txt"
set /p PORT_STATUS=<"%TEMP%\pdfresumes_port_status.txt"
del /q "%TEMP%\pdfresumes_port_status.txt" >nul 2>nul

if /I "%PORT_STATUS%"=="UP" (
  echo [INFO] Ya hay un servicio usando el puerto %PORT%.
  echo [INFO] Abriendo navegador en %APP_URL% ...
  start "" "%APP_URL%"
  echo [INFO] Si no es PDFResumes, cierra el proceso que usa ese puerto y vuelve a ejecutar este archivo.
  pause
  exit /b 0
)

echo [5/5] Iniciando servidor web en %APP_URL%
start "" "%APP_URL%"

echo.
echo La app web se esta ejecutando.
echo Mantén esta ventana abierta mientras uses la pagina.
echo Para detenerla: Ctrl + C
echo.

call "%VENV_DIR%\Scripts\python.exe" app.py
if errorlevel 1 (
  echo.
  echo [ERROR] El servidor se cerro con error.
  echo [TIP] Si el puerto %PORT% esta ocupado, cierra esa app e intenta nuevamente.
)

pause
endlocal
