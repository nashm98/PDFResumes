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
from email.parser import BytesParser
from email.policy import default

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
    stopwords = {
        "para", "como", "entre", "desde", "hasta", "sobre", "durante", "porque", "donde", "cuando",
        "esta", "este", "estas", "estos", "tambien", "segun", "hacia", "ellos", "ellas", "nosotros",
        "usted", "ustedes", "ser", "estar", "haber", "tener", "hacer", "poder", "deber", "que", "del",
        "las", "los", "una", "uno", "unos", "unas", "por", "con", "sin",
    }
    generic_words = {"proceso", "resultado", "principalmente", "tambien", "sistema", "metodo"}

    def keywords_from_sentence(sentence: str) -> list[str]:
        words = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]+", sentence)
        ranked = [w for w in words if len(w) > 5 and w.lower() not in stopwords and w.lower() not in generic_words]
        seen: set[str] = set()
        ordered: list[str] = []
        for word in ranked:
            key = word.lower()
            if key in seen:
                continue
            seen.add(key)
            ordered.append(word)
        return ordered

    sentences = split_sentences(text)
    usable = [s for s in sentences if len(s) > 60][:20]
    if not usable:
        return []

    quiz: list[QuizQuestion] = []
    pool_keywords: list[str] = []
    used_topics: set[str] = set()
    for sentence in usable:
        pool_keywords.extend(keywords_from_sentence(sentence)[:2])

    for sentence in usable:
        if len(quiz) >= count:
            break

        sentence_keywords = keywords_from_sentence(sentence)
        if not sentence_keywords:
            continue

        topic = sentence_keywords[0]
        if topic.lower() in used_topics:
            continue
        question = f"Según el texto, ¿cuál afirmación describe mejor el punto sobre '{topic}'?"

        correct = clean_text(sentence)
        distractors: list[str] = []

        for other in usable:
            other_clean = clean_text(other)
            if other_clean == correct or topic.lower() in other_clean.lower():
                continue
            distractors.append(other_clean)
            if len(distractors) == 2:
                break

        for alt in pool_keywords:
            if len(distractors) >= 3:
                break
            if alt.lower() == topic.lower():
                continue
            replaced = re.sub(rf"\b{re.escape(topic)}\b", alt, correct, count=1, flags=re.IGNORECASE)
            replaced = clean_text(replaced)
            if replaced != correct and replaced not in distractors:
                distractors.append(replaced)

        if len(distractors) < 3:
            continue

        options = [correct] + distractors[:3]
        shift = len(quiz) % len(options)
        options = options[shift:] + options[:shift]

        used_topics.add(topic.lower())
        quiz.append(
            QuizQuestion(
                question=question,
                options=options,
                answer=correct,
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




def parse_uploaded_file(content_type: str, payload: bytes) -> tuple[str, bytes]:
    if "multipart/form-data" not in content_type.lower():
        raise ValueError("Formato de envío inválido. Usa multipart/form-data.")

    envelope = (
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
        + payload
    )
    message = BytesParser(policy=default).parsebytes(envelope)
    if not message.is_multipart():
        raise ValueError("No se recibió un formulario multipart válido.")

    for part in message.iter_parts():
        if part.get_content_disposition() != "form-data":
            continue
        if part.get_param("name", header="content-disposition") != "file":
            continue

        filename = Path(part.get_filename() or "").name
        if not filename:
            raise ValueError("Debes subir un archivo.")

        file_payload = part.get_payload(decode=True) or b""
        if not file_payload:
            raise ValueError("El archivo está vacío.")
        return filename, file_payload

    raise ValueError("Debes subir un archivo en el campo 'file'.")

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

        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", "0") or 0)
        payload = self.rfile.read(content_length)

        try:
            filename, file_payload = parse_uploaded_file(content_type, payload)
            text = clean_text(extract_text_from_upload(filename, file_payload))
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
