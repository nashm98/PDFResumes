@echo off
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"
set "VENV_DIR=%CD%\.venv"
set "PORT=8000"

echo [1/4] Verificando Python...
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

echo [2/4] Preparando entorno virtual...
if not exist "%VENV_DIR%\Scripts\python.exe" (
  call %PYTHON_CMD% -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
  )
)

echo [3/4] Instalando dependencias ^(si aplica^)...
set "HAS_DEPS="
for /f "usebackq delims=" %%L in (`findstr /r /v "^[ ]*# ^[ ]*$" requirements.txt 2^>nul`) do (
  set "HAS_DEPS=1"
  goto :deps_done
)
:deps_done

if defined HAS_DEPS (
  call "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [WARN] No se pudieron instalar dependencias.
    echo [WARN] Si subes PDF/DOCX y falla, revisa tu conexion y ejecuta start.bat de nuevo.
  )
) else (
  echo [INFO] No hay dependencias obligatorias para instalar.
)

echo [4/4] Iniciando servidor en http://localhost:%PORT%
start "" "http://localhost:%PORT%"

echo.
echo La app esta levantando. Esta ventana debe quedar abierta.
echo Si el navegador muestra error al inicio, espera 2-3 segundos y recarga.
echo Para detener la app, cierra esta ventana o presiona Ctrl + C.
echo.

call "%VENV_DIR%\Scripts\python.exe" app.py
if errorlevel 1 (
  echo.
  echo [ERROR] El servidor se cerro con error.
  echo Verifica si el puerto %PORT% ya esta en uso o revisa el mensaje mostrado arriba.
)

pause
endlocal
