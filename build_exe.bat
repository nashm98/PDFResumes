@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"

set "VENV_DIR=%CD%\.venv_build"
set "BUILD_INFO=dist\PDFResumesApp.buildinfo"

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
    pause
    exit /b 1
  )
)

echo [2/5] Preparando entorno de build...
if not exist "%VENV_DIR%\Scripts\python.exe" (
  call %PYTHON_CMD% -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual de build.
    pause
    exit /b 1
  )
)

echo [3/5] Instalando dependencias de app + PyInstaller...
call "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
if exist requirements.txt (
  call "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] No se pudieron instalar dependencias de requirements.txt.
    pause
    exit /b 1
  )
)
call "%VENV_DIR%\Scripts\python.exe" -m pip install pyinstaller
if errorlevel 1 (
  echo [ERROR] No se pudo instalar PyInstaller.
  pause
  exit /b 1
)

echo [4/5] Verificando modulo pypdf...
call "%VENV_DIR%\Scripts\python.exe" -c "import pypdf; print('pypdf', pypdf.__version__)"
if errorlevel 1 (
  echo [ERROR] pypdf no esta disponible en el entorno de build.
  pause
  exit /b 1
)

echo [5/5] Generando ejecutable limpio...
if exist build rmdir /s /q build
if exist dist\PDFResumesApp.exe del /q dist\PDFResumesApp.exe
call "%VENV_DIR%\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name PDFResumesApp --hidden-import pypdf desktop_app.py
if errorlevel 1 (
  echo [ERROR] Fallo la generacion del .exe.
  pause
  exit /b 1
)

if not exist dist mkdir dist
> "%BUILD_INFO%" echo build_ok=true
>> "%BUILD_INFO%" call "%VENV_DIR%\Scripts\python.exe" -c "import pypdf; print('pypdf=' + pypdf.__version__)"

echo.
echo Listo. Ejecutable creado en: dist\PDFResumesApp.exe
echo Marca de build: %BUILD_INFO%
pause
endlocal
