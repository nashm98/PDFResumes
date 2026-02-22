@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"

set "VENV_DIR=%CD%\.venv"
set "PORT=8000"
set "APP_URL=http://127.0.0.1:%PORT%"
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

echo [4/6] Verificacion rapida de app.py...
call "%VENV_DIR%\Scripts\python.exe" -m py_compile app.py
if errorlevel 1 (
  echo [ERROR] app.py tiene errores de ejecucion/sintaxis.
  pause
  exit /b 1
)

echo [5/6] Verificando si ya hay servidor activo en %APP_URL% ...
call "%VENV_DIR%\Scripts\python.exe" -c "import socket; s=socket.socket(); s.settimeout(1.0); rc=s.connect_ex(('127.0.0.1', %PORT%)); s.close(); print('UP' if rc==0 else 'DOWN')" > "%STATUS_FILE%"
set "PORT_STATUS=DOWN"
if exist "%STATUS_FILE%" (
  set /p PORT_STATUS=<"%STATUS_FILE%"
  del /q "%STATUS_FILE%" >nul 2>nul
)

if /I "%PORT_STATUS%"=="UP" (
  echo [INFO] Ya hay un servicio respondiendo en %APP_URL%.
  echo [INFO] Abriendo navegador...
  start "" "%APP_URL%"
  echo [INFO] Si no ves PDFResumes, cierra el proceso que usa el puerto %PORT% y ejecuta nuevamente.
  pause
  exit /b 0
)

echo [6/6] Iniciando servidor web y abriendo navegador...
start "PDFResumesBrowser" cmd /c "timeout /t 2 /nobreak >nul && start \"\" \"%APP_URL%\""

echo.
echo La app web se esta ejecutando en %APP_URL%
echo Mantén esta ventana abierta mientras uses la pagina.
echo Para detenerla: Ctrl + C
echo.

call "%VENV_DIR%\Scripts\python.exe" app.py
if errorlevel 1 (
  echo.
  echo [ERROR] El servidor se cerro con error.
  echo [TIP] Revisa si el puerto %PORT% esta ocupado o si un antivirus bloqueo Python.
)

pause
exit /b 1
