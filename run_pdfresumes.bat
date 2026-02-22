@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"

set "VENV_DIR=%CD%\.venv"
set "PORT=8000"
set "APP_URL=http://127.0.0.1:%PORT%"
set "HEALTH_URL=%APP_URL%/"
set "LOG_FILE=%TEMP%\pdfresumes_server.log"

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
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -Uri '%HEALTH_URL%' -UseBasicParsing -TimeoutSec 2; if($r.StatusCode -ge 200 -and $r.StatusCode -lt 500){ exit 0 } else { exit 1 } } catch { exit 1 }"
if %errorlevel%==0 (
  echo [INFO] Ya hay un servicio HTTP respondiendo en %APP_URL%.
  echo [INFO] Abriendo navegador...
  start "" "%APP_URL%"
  echo [INFO] Si no ves PDFResumes, cierra la app que usa el puerto %PORT% y vuelve a ejecutar este archivo.
  pause
  exit /b 0
)

echo [5/6] Iniciando servidor de PDFResumes...
if exist "%LOG_FILE%" del /q "%LOG_FILE%" >nul 2>nul
start "PDFResumesServer" /min cmd /c "cd /d \"%CD%\" && \"%VENV_DIR%\Scripts\python.exe\" app.py > \"%LOG_FILE%\" 2>&1"

echo [6/6] Esperando a que el servidor responda...
set "READY="
for /L %%I in (1,1,30) do (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r=Invoke-WebRequest -Uri '%HEALTH_URL%' -UseBasicParsing -TimeoutSec 2; if($r.StatusCode -ge 200 -and $r.StatusCode -lt 500){ exit 0 } else { exit 1 } } catch { exit 1 }"
  if !errorlevel! == 0 (
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
  echo Si deseas detenerlo, cierra la ventana "PDFResumesServer" o finaliza python.exe desde el Administrador de tareas.
  pause
  exit /b 0
)

echo [ERROR] El servidor no respondio a tiempo.
if exist "%LOG_FILE%" (
  echo ---------- Ultimas lineas de log ----------
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content -Path '%LOG_FILE%' -Tail 40"
  echo -------------------------------------------
)
echo [TIP] Verifica si el puerto %PORT% esta ocupado o si el antivirus bloqueo Python.
pause
exit /b 1
