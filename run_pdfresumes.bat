@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"

set "VENV_DIR=%CD%\.venv"
set "PORT=8000"
set "APP_URL=http://127.0.0.1:%PORT%"
set "LOG_FILE=%TEMP%\pdfresumes_server.log"
set "STATUS_FILE=%TEMP%\pdfresumes_port_status.txt"

echo [1/6] Verificando Python...
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

echo [2/6] Preparando entorno virtual...
if not exist "%VENV_DIR%\Scripts\python.exe" (
  call %PYTHON_CMD% -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
  )
)

echo [3/6] Instalando dependencias...
if exist requirements.txt (
  call "%VENV_DIR%\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] No se pudieron instalar dependencias.
    echo [TIP] Revisa conexion de red o ejecuta desde una carpeta local corta.
    pause
    exit /b 1
  )
)

echo [4/6] Verificando si ya hay servidor activo en %APP_URL% ...
call "%VENV_DIR%\Scripts\python.exe" -c "import socket; s=socket.socket(); s.settimeout(1.0); rc=s.connect_ex(('127.0.0.1', %PORT%)); s.close(); print('UP' if rc==0 else 'DOWN')" > "%STATUS_FILE%"
set "PORT_STATUS=DOWN"
if exist "%STATUS_FILE%" (
  set /p PORT_STATUS=<"%STATUS_FILE%"
  del /q "%STATUS_FILE%" >nul 2>nul
)

if /I "%PORT_STATUS%"=="UP" (
  echo [INFO] Ya hay un servicio respondiendo en %APP_URL%.
  start "" "%APP_URL%"
  echo [INFO] Si no ves PDFResumes, cierra el proceso que usa el puerto %PORT% y ejecuta nuevamente.
  pause
  exit /b 0
)

echo [5/6] Iniciando servidor de PDFResumes...
if exist "%LOG_FILE%" del /q "%LOG_FILE%" >nul 2>nul
start "PDFResumesServer" /min cmd /c "cd /d \"%CD%\" && \"%VENV_DIR%\Scripts\python.exe\" app.py > \"%LOG_FILE%\" 2>&1"

echo [6/6] Esperando a que el servidor responda...
set "READY="
for /L %%I in (1,1,40) do (
  call "%VENV_DIR%\Scripts\python.exe" -c "import socket; s=socket.socket(); s.settimeout(1.0); rc=s.connect_ex(('127.0.0.1', %PORT%)); s.close(); raise SystemExit(0 if rc==0 else 1)"
  if !errorlevel! EQU 0 (
    set "READY=1"
    goto :ready
  )
  timeout /t 1 /nobreak >nul
)

:ready
if defined READY (
  echo [OK] Servidor listo. Abriendo navegador en %APP_URL%
  start "" "%APP_URL%"
  echo.
  echo PDFResumes esta en ejecucion.
  echo Para detenerlo, cierra la ventana "PDFResumesServer" o finaliza python.exe.
  pause
  exit /b 0
)

echo [ERROR] El servidor no respondio en 40 segundos.
if exist "%LOG_FILE%" (
  echo ---------- Ultimas lineas de log ----------
  type "%LOG_FILE%"
  echo -------------------------------------------
)
echo [TIP] Verifica si el puerto %PORT% esta ocupado o si el antivirus bloqueo Python.
pause
exit /b 1
