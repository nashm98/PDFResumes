@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"

REM Usar rutas cortas para evitar errores de Windows Long Path en OneDrive/rutas profundas.
set "BUILD_ROOT=%SystemDrive%\PDFResumesBuild"
set "VENV_DIR=%BUILD_ROOT%\venv"
set "WORK_DIR=%BUILD_ROOT%\work"
set "DIST_DIR=%CD%\dist"
set "BUILD_INFO=%DIST_DIR%\PDFResumesApp.buildinfo"

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
    pause
    exit /b 1
  )
)

echo [2/6] Preparando carpetas de build con ruta corta...
if not exist "%BUILD_ROOT%" mkdir "%BUILD_ROOT%"
if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"

echo [3/6] Preparando entorno virtual de build...
if not exist "%VENV_DIR%\Scripts\python.exe" (
  call %PYTHON_CMD% -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual de build.
    pause
    exit /b 1
  )
)

echo [4/6] Instalando dependencias de app + PyInstaller...
call "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip --disable-pip-version-check
if exist requirements.txt (
  call "%VENV_DIR%\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] No se pudieron instalar dependencias de requirements.txt.
    echo [TIP] Si aparece un error de Long Path, habilita rutas largas en Windows o ejecuta el proyecto desde una ruta mas corta.
    pause
    exit /b 1
  )
)
call "%VENV_DIR%\Scripts\python.exe" -m pip install --disable-pip-version-check pyinstaller
if errorlevel 1 (
  echo [ERROR] No se pudo instalar PyInstaller.
  echo [TIP] Esto suele ocurrir por rutas demasiado largas en Windows.
  pause
  exit /b 1
)

echo [5/6] Verificando modulo pypdf...
call "%VENV_DIR%\Scripts\python.exe" -c "import pypdf; print('pypdf', pypdf.__version__)"
if errorlevel 1 (
  echo [ERROR] pypdf no esta disponible en el entorno de build.
  pause
  exit /b 1
)

echo [6/6] Generando ejecutable limpio...
if exist "%WORK_DIR%\build" rmdir /s /q "%WORK_DIR%\build"
if exist "%WORK_DIR%\__pycache__" rmdir /s /q "%WORK_DIR%\__pycache__"
if exist "%DIST_DIR%\PDFResumesApp.exe" del /q "%DIST_DIR%\PDFResumesApp.exe"

call "%VENV_DIR%\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name PDFResumesApp --hidden-import pypdf --workpath "%WORK_DIR%\build" --specpath "%WORK_DIR%" --distpath "%DIST_DIR%" desktop_app.py
if errorlevel 1 (
  echo [ERROR] Fallo la generacion del .exe.
  echo [TIP] Si el error menciona Long Path, mueve el proyecto a una ruta corta como C:\PDFResumes.
  pause
  exit /b 1
)

> "%BUILD_INFO%" echo build_ok=true
>> "%BUILD_INFO%" call "%VENV_DIR%\Scripts\python.exe" -c "import pypdf; print('pypdf=' + pypdf.__version__)"
>> "%BUILD_INFO%" echo build_root=%BUILD_ROOT%

echo.
echo Listo. Ejecutable creado en: %DIST_DIR%\PDFResumesApp.exe
echo Marca de build: %BUILD_INFO%
pause
endlocal
