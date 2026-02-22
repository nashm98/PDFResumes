@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Verificando Python...
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

echo [2/3] Instalando PyInstaller...
call %PYTHON_CMD% -m pip install pyinstaller
if errorlevel 1 (
  echo [ERROR] No se pudo instalar PyInstaller.
  pause
  exit /b 1
)

echo [3/3] Generando ejecutable...
call %PYTHON_CMD% -m PyInstaller --onefile --windowed --name PDFResumesApp --hidden-import pypdf desktop_app.py
if errorlevel 1 (
  echo [ERROR] Fallo la generacion del .exe.
  pause
  exit /b 1
)

echo.
echo Listo. Ejecutable creado en: dist\PDFResumesApp.exe
pause
endlocal
