# PDFResumes Web App

Aplicación web para resumir documentos y generar quizzes tipo preguntas con alternativas.

## Características
- Subida de archivos: **PDF, DOCX, TXT, MD, CSV, JSON, LOG, RTF**.
- Extracción de texto según formato.
- Resumen en español:
  - Con IA (si defines `OPENAI_API_KEY`).
  - Con fallback local automático (sin API key).
- Quiz de opción múltiple basado en el documento.

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

## Variables opcionales
- `OPENAI_API_KEY`: activa generación con IA.
- `OPENAI_MODEL`: modelo a usar (por defecto: `gpt-4.1-mini`).

