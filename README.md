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

## Inicio rápido en Windows (UN solo archivo)
- Haz doble clic en `run_pdfresumes.bat`.
- Ese único archivo hace todo automáticamente para abrir la **página web**:
  - verifica Python,
  - crea/usa `.venv`,
  - instala dependencias (`requirements.txt`),
  - verifica si ya hay un servidor HTTP activo en `127.0.0.1:8000`,
  - si no existe, levanta `app.py`, espera salud del servidor y recién ahí abre el navegador,
  - si falla, muestra log de diagnóstico en pantalla.

Si al abrirse el navegador aparece error de conexión, espera 2-3 segundos y recarga la página.

## Compatibilidad
- `start.bat` se mantiene por compatibilidad y ahora delega en `run_pdfresumes.bat`.
- `build_exe.bat` y `desktop_app.py` quedan como flujo opcional para modo escritorio, pero el flujo recomendado es web con `run_pdfresumes.bat`.

## Variables opcionales
- `OPENAI_API_KEY`: activa generación con IA.
- `OPENAI_MODEL`: modelo a usar (por defecto: `gpt-4.1-mini`).
