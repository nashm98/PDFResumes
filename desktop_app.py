from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app import clean_text, extract_text_from_upload, generate_quiz_locally, summarize_with_ai


class PDFResumesDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDFResumes Desktop")
        self.root.geometry("1120x760")
        self.root.minsize(960, 640)

        self.file_path: Path | None = None
        self._apply_theme()

        wrapper = ttk.Frame(root, style="App.TFrame", padding=18)
        wrapper.pack(fill="both", expand=True)

        hero = ttk.Frame(wrapper, style="Card.TFrame", padding=16)
        hero.pack(fill="x", pady=(0, 12))

        ttk.Label(
            hero,
            text="Resume y estudia documentos con una interfaz moderna",
            style="Title.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            hero,
            text="Sube PDF, DOCX, DOC, TXT y más para generar un resumen profesional y un quiz de comprensión.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(6, 0))

        upload_card = ttk.Frame(wrapper, style="Card.TFrame", padding=14)
        upload_card.pack(fill="x", pady=(0, 12))

        self.file_label = ttk.Label(upload_card, text="Archivo: ninguno seleccionado", style="Body.TLabel")
        self.file_label.grid(row=0, column=0, sticky="w")
        ttk.Button(upload_card, text="Seleccionar archivo", command=self.select_file, style="Secondary.TButton").grid(
            row=0, column=1, padx=(10, 0)
        )
        self.process_btn = ttk.Button(
            upload_card,
            text="Generar resumen y quiz",
            command=self.process_file,
            style="Primary.TButton",
        )
        self.process_btn.grid(row=0, column=2, padx=(10, 0))
        upload_card.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Listo para comenzar")
        ttk.Label(upload_card, textvariable=self.status_var, style="Muted.TLabel").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(10, 0)
        )

        content = ttk.Panedwindow(wrapper, orient="horizontal")
        content.pack(fill="both", expand=True)

        summary_card = ttk.Frame(content, style="Card.TFrame", padding=12)
        quiz_card = ttk.Frame(content, style="Card.TFrame", padding=12)
        content.add(summary_card, weight=1)
        content.add(quiz_card, weight=1)

        ttk.Label(summary_card, text="Resumen del documento", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self.summary_text = tk.Text(
            summary_card,
            wrap="word",
            bg="#101010",
            fg="#f2f2f2",
            insertbackground="#ffffff",
            relief="flat",
            padx=14,
            pady=14,
            font=("Segoe UI", 11),
        )
        self.summary_text.pack(fill="both", expand=True)

        ttk.Label(quiz_card, text="Quiz de comprensión", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        self.quiz_text = tk.Text(
            quiz_card,
            wrap="word",
            bg="#101010",
            fg="#f2f2f2",
            insertbackground="#ffffff",
            relief="flat",
            padx=14,
            pady=14,
            font=("Segoe UI", 11),
        )
        self.quiz_text.pack(fill="both", expand=True)

    def _apply_theme(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        self.root.configure(bg="#0b0b0b")
        style.configure("App.TFrame", background="#0b0b0b")
        style.configure("Card.TFrame", background="#161616", borderwidth=1, relief="solid")
        style.configure("Title.TLabel", background="#161616", foreground="#ffffff", font=("Segoe UI", 16, "bold"))
        style.configure("Section.TLabel", background="#161616", foreground="#ffffff", font=("Segoe UI", 12, "bold"))
        style.configure("Body.TLabel", background="#161616", foreground="#f5f5f5", font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background="#161616", foreground="#b5b5b5", font=("Segoe UI", 10))

        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8))
        style.map("Primary.TButton", background=[("!disabled", "#ffffff"), ("disabled", "#bfbfbf")], foreground=[("!disabled", "#111111")])

        style.configure("Secondary.TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.map("Secondary.TButton", background=[("!disabled", "#262626")], foreground=[("!disabled", "#ffffff")])

    def select_file(self):
        path = filedialog.askopenfilename(
            title="Selecciona un archivo",
            filetypes=[
                ("Archivos soportados", "*.pdf *.docx *.doc *.txt *.md *.csv *.json *.log *.rtf"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not path:
            return

        self.file_path = Path(path)
        self.file_label.config(text=f"Archivo: {self.file_path.name}")
        self.status_var.set("Archivo cargado. Presiona 'Generar resumen y quiz'.")

    def process_file(self):
        if not self.file_path:
            messagebox.showwarning("Atención", "Primero selecciona un archivo.")
            return

        self.process_btn.state(["disabled"])
        self.status_var.set("Procesando archivo...")
        self.root.update_idletasks()

        try:
            payload = self.file_path.read_bytes()
            extracted = extract_text_from_upload(self.file_path.name, payload)
            text = clean_text(extracted)
            if len(text) < 30:
                raise ValueError("El archivo no contiene suficiente texto para procesar.")

            summary = summarize_with_ai(text)
            quiz = generate_quiz_locally(text)
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo procesar el archivo:\n{exc}")
            self.status_var.set("Error al procesar el archivo")
            self.process_btn.state(["!disabled"])
            return

        self.summary_text.delete("1.0", tk.END)
        lines = [ln.strip("• ").strip() for ln in summary.splitlines() if ln.strip()]
        items = lines if lines else [summary.strip()]

        self.summary_text.insert(tk.END, "Resumen ejecutivo\n\n", ("title",))
        for idx, item in enumerate(items, start=1):
            self.summary_text.insert(tk.END, f"{idx}. {item}\n\n")

        self.quiz_text.delete("1.0", tk.END)
        if not quiz:
            self.quiz_text.insert(tk.END, "No fue posible generar preguntas para este archivo.")
        else:
            for idx, q in enumerate(quiz, start=1):
                self.quiz_text.insert(tk.END, f"{idx}) {q.question}\n", ("question",))
                for opt_idx, option in enumerate(q.options, start=1):
                    marker = "✅" if option == q.answer else "○"
                    self.quiz_text.insert(tk.END, f"   {marker} {opt_idx}. {option}\n")
                self.quiz_text.insert(tk.END, "\n")

        self.summary_text.tag_configure("title", foreground="#ffffff", font=("Segoe UI", 12, "bold"))
        self.quiz_text.tag_configure("question", foreground="#ffffff", font=("Segoe UI", 11, "bold"))

        self.status_var.set(f"Procesado correctamente: {self.file_path.name}")
        self.process_btn.state(["!disabled"])


def main():
    root = tk.Tk()
    PDFResumesDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
