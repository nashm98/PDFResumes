# PDFResumes

Aplicación web para resumir documentos y generar quizzes tipo preguntas con alternativas.

## Características
- Subida de archivos: **PDF, DOCX, DOC, TXT, MD, CSV, JSON, LOG, RTF**.
- Extracción de texto según formato.
- Resumen en español:
  - Con IA (si defines `OPENAI_API_KEY`).
  - Con fallback local automático (sin API key).
- Quiz de opción múltiple basado en el documento.

> Nota: para leer PDFs se usa `pypdf` (incluido en `requirements.txt`).

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución
```bash
python app.py
```
Abre: `http://localhost:8000`

## Inicio rápido (automático)
```bash
./start.sh
```
Este script:
- Crea y activa `.venv` si no existe.
- Intenta instalar `requirements.txt` (si falla por red, continúa en modo local).
- Inicia el servidor y abre el navegador automáticamente en `http://localhost:8000`.

## Inicio rápido en Windows (doble clic)
- Haz doble clic en `start.bat`.
- O desde CMD/PowerShell:
```bat
start.bat
```
Este archivo prepara `.venv`, instala dependencias si las hay y abre `http://localhost:8000` automáticamente.

Si al abrirse el navegador aparece error de conexión, espera 2-3 segundos y recarga la página.

## Ejecutable para Windows (.exe)
Si quieres usarlo como programa de Windows:

1. Ejecuta `build_exe.bat` (doble clic).
2. Esto genera `dist\PDFResumesApp.exe` incluyendo la dependencia de PDF (`pypdf`) dentro del ejecutable.
3. Abre `PDFResumesApp.exe` y tendrás una aplicación de escritorio (sin abrir navegador).

## Un solo archivo para ejecutar todo en Windows
- Haz doble clic en `run_pdfresumes.bat`.
- Ese archivo hace todo automáticamente:
  - si no existe `dist\PDFResumesApp.exe`, lo compila;
  - luego abre la app de escritorio sin que tengas que ejecutar más pasos.

## Modo escritorio
- `desktop_app.py` ejecuta la app como interfaz nativa de Windows (Tkinter), sin servidor web ni navegador, con interfaz visual moderna en escala de negros.

## Variables opcionales
- `OPENAI_API_KEY`: activa generación con IA.
- `OPENAI_MODEL`: modelo a usar (por defecto: `gpt-4.1-mini`).
