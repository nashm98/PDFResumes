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
    ".doc",
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
    sentences = [clean_text(s) for s in split_sentences(text) if 45 <= len(clean_text(s)) <= 260][:35]
    if len(sentences) < 2:
        return []

    def keyphrases(sentence: str) -> list[str]:
        patterns = [
            r"\b\d{1,2} de [a-záéíóúñ]+ de \d{4}\b",  # fechas
            r"\b(?:19|20)\d{2}\b",  # años
            r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}\b",  # nombres propios
            r"\b\d+[.,]?\d*\b",  # números
            r"\"([^\"]{4,80})\"",  # texto entre comillas
        ]

        found: list[str] = []
        for pattern in patterns:
            for m in re.finditer(pattern, sentence, flags=re.IGNORECASE):
                val = m.group(1) if m.lastindex else m.group(0)
                val = clean_text(val).strip(" ,.;:()[]{}")
                if len(val) < 2:
                    continue
                if val.lower() in {"primera", "segunda", "tema", "capitulo", "capítulo"}:
                    continue
                if val not in found:
                    found.append(val)

        if not found:
            words = [w for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]+", sentence) if len(w) >= 7 and w.lower() not in {"primera", "segunda", "durante", "porque", "tambien"}]
            for w in words[:3]:
                if w not in found:
                    found.append(w)

        return found[:5]

    candidates: list[tuple[str, str]] = []
    for sentence in sentences:
        picks = [
            ph for ph in keyphrases(sentence)
            if ph.lower() in sentence.lower()
            and not ph.lower().startswith(("la ", "el ", "los ", "las ", "un ", "una "))
        ]
        if not picks:
            continue
        candidates.append((sentence, picks[0]))

    if len(candidates) < 2:
        return []

    quiz: list[QuizQuestion] = []
    used_questions: set[str] = set()

    all_phrases = [ph for _, ph in candidates]

    for sentence, answer in candidates:
        if len(quiz) >= count:
            break

        mode = len(quiz) % 3
        if mode == 0:
            masked = re.sub(re.escape(answer), "_____", sentence, count=1, flags=re.IGNORECASE)
            question = f"Completa la afirmación según el texto: {masked}"
            if question in used_questions:
                continue

            distractors: list[str] = []
            for alt in all_phrases:
                if alt.lower() == answer.lower() or alt in distractors:
                    continue
                if answer.lower() in alt.lower() or alt.lower() in answer.lower():
                    continue
                distractors.append(alt)
                if len(distractors) == 3:
                    break

            if len(distractors) < 3:
                continue

            options = [answer] + distractors[:3]
            correct = answer
        else:
            question = f"Según el texto, ¿qué enunciado es correcto respecto a '{answer}'?"
            if question in used_questions:
                continue

            distractors = [s for s in sentences if s != sentence][:3]
            if len(distractors) < 3:
                continue
            options = [sentence] + distractors
            correct = sentence

        shift = len(quiz) % 4
        options = options[shift:] + options[:shift]

        quiz.append(QuizQuestion(question=question, options=options, answer=correct))
        used_questions.add(question)

    return quiz


def generate_quiz_with_ai(text: str) -> list[QuizQuestion]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return generate_quiz_locally(text)

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    prompt = (
        "Genera 5 preguntas de opción múltiple en español sobre el texto. "
        "Devuelve SOLO JSON con formato: "
        "[{\"question\":str,\"options\":[str,str,str,str],\"answer\":str}]. "
        "La respuesta correcta debe estar incluida exactamente dentro de options."
    )
    body = {
        "model": model,
        "input": f"{prompt}\n\nTEXTO:\n{text[:18000]}",
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
        raw = (data.get("output_text") or "").strip()
        parsed = json.loads(raw)
        quiz: list[QuizQuestion] = []
        for item in parsed:
            question = clean_text(str(item.get("question", "")))
            options = [clean_text(str(o)) for o in item.get("options", []) if clean_text(str(o))]
            answer = clean_text(str(item.get("answer", "")))
            if not question or len(options) != 4 or answer not in options:
                continue
            quiz.append(QuizQuestion(question=question, options=options, answer=answer))
        return quiz or generate_quiz_locally(text)
    except Exception:
        return generate_quiz_locally(text)
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


def extract_doc_text(file_path: Path) -> str:
    """Fallback básico para .doc clásico.

    Los archivos .doc binarios no tienen un parser estándar en la librería base,
    así que intentamos recuperar texto visible para evitar fallar en Windows.
    """
    data = file_path.read_bytes()
    text = data.decode("latin-1", errors="ignore")
    text = re.sub(r"[^\x20-\x7E\xA0-\xFF\n\r\t]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 80:
        raise RuntimeError(
            "No se pudo leer DOC clásico (.doc). Convierte el archivo a .docx o .txt e inténtalo de nuevo."
        )
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
        if ext == ".doc":
            return extract_doc_text(tmp_path)
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
        quiz = generate_quiz_with_ai(text)

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
