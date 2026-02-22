import cgi
import json
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request as urlrequest
from urllib.parse import urlparse

BASE_DIR = Path(__file__).parent

ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".rtf",
    ".pdf",
    ".docx",
    ".csv",
    ".json",
    ".log",
}

MIME_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".html": "text/html; charset=utf-8",
}


@dataclass
class QuizQuestion:
    question: str
    options: list[str]
    answer: str


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 30]


def summarize_locally(text: str, max_sentences: int = 5) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return "No se pudo generar un resumen porque el archivo no contiene texto legible."
    return "\n".join(f"• {s}" for s in sentences[:max_sentences])


def generate_quiz_locally(text: str, count: int = 5) -> list[QuizQuestion]:
    sentences = split_sentences(text)
    quiz: list[QuizQuestion] = []
    usable = sentences[: min(20, len(sentences))]

    for i, sentence in enumerate(usable[:count]):
        words = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]+", sentence) if len(w) > 4]
        if len(words) < 2:
            continue
        answer = words[1]
        masked = re.sub(rf"\b{re.escape(answer)}\b", "_____", sentence, count=1)

        distractors = []
        for other in usable:
            candidates = [
                w
                for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]+", other)
                if len(w) > 4 and w.lower() != answer.lower()
            ]
            if candidates:
                distractors.append(candidates[0])
            if len(distractors) >= 3:
                break

        options = list(dict.fromkeys([answer] + distractors))
        if len(options) < 2:
            continue
        shift = i % len(options)
        options = options[shift:] + options[:shift]

        quiz.append(
            QuizQuestion(
                question=f"¿Qué palabra completa correctamente la frase?\n\n{masked}",
                options=options,
                answer=answer,
            )
        )
    return quiz


def extract_pdf_text(file_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "No se pudo leer PDF: falta la dependencia 'pypdf'. "
            "Ejecuta start.bat nuevamente o instala con 'pip install -r requirements.txt'."
        ) from exc

    reader = PdfReader(str(file_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if not clean_text(text):
        raise RuntimeError("No se encontró texto legible dentro del PDF.")
    return text


def extract_docx_text(file_path: Path) -> str:
    try:
        with zipfile.ZipFile(file_path) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    except Exception as exc:
        raise RuntimeError("No se pudo leer DOCX: archivo inválido o dañado.") from exc

    text = re.sub(r"<[^>]+>", " ", xml)
    return text


def extract_text_from_upload(filename: str, payload: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Formato no soportado")

    if ext in {".txt", ".md", ".rtf", ".csv", ".json", ".log"}:
        return payload.decode("utf-8", errors="ignore")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)

    try:
        if ext == ".pdf":
            return extract_pdf_text(tmp_path)
        if ext == ".docx":
            return extract_docx_text(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return ""


def summarize_with_ai(text: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return summarize_locally(text)

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    body = {
        "model": model,
        "input": "Resume en español el siguiente contenido en máximo 8 bullets claros.\n\n" + text[:25000],
    }
    req = urlrequest.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("output_text", "").strip() or summarize_locally(text)
    except Exception:
        return summarize_locally(text)


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: int = 200):
        encoded = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path):
        ext = path.suffix.lower()
        mime = MIME_TYPES.get(ext, "text/plain; charset=utf-8")
        content = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send_file(BASE_DIR / "templates" / "index.html")
            return
        if path.startswith("/static/"):
            rel = path.removeprefix("/static/")
            file_path = (BASE_DIR / "static" / rel).resolve()
            static_root = (BASE_DIR / "static").resolve()
            if static_root in file_path.parents and file_path.exists() and file_path.is_file():
                self._send_file(file_path)
                return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/process":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            },
        )

        if "file" not in form:
            self._send_json({"error": "Debes subir un archivo."}, 400)
            return

        file_item = form["file"]
        filename = Path(file_item.filename or "").name
        if not filename:
            self._send_json({"error": "Debes subir un archivo."}, 400)
            return

        try:
            payload = file_item.file.read()
            text = clean_text(extract_text_from_upload(filename, payload))
        except Exception as exc:
            self._send_json({"error": f"No se pudo leer el archivo: {exc}"}, 400)
            return

        if len(text) < 30:
            self._send_json({"error": "El archivo no contiene suficiente texto para procesar."}, 400)
            return

        summary = summarize_with_ai(text)
        quiz = generate_quiz_locally(text)

        self._send_json(
            {
                "summary": summary,
                "quiz": [q.__dict__ for q in quiz],
                "text_length": len(text),
                "filename": filename,
            }
        )


def run():
    port = int(os.getenv("PORT", "8000"))
    try:
        server = ThreadingHTTPServer(("0.0.0.0", port), AppHandler)
    except OSError as exc:
        print(f"[ERROR] No se pudo iniciar el servidor en el puerto {port}: {exc}")
        print("Cierra la otra aplicación que use ese puerto o configura PORT con otro valor.")
        raise

    print(f"Servidor disponible en http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
