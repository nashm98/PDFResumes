from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app import clean_text, extract_text_from_upload, generate_quiz_locally, summarize_with_ai


class PDFResumesDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDFResumes Desktop")
        self.root.geometry("980x760")

        self.file_path: Path | None = None

        container = ttk.Frame(root, padding=14)
        container.pack(fill="both", expand=True)

        top = ttk.Frame(container)
        top.pack(fill="x")

        self.file_label = ttk.Label(top, text="Archivo: ninguno seleccionado")
        self.file_label.pack(side="left", fill="x", expand=True)

        ttk.Button(top, text="Seleccionar archivo", command=self.select_file).pack(side="left", padx=(8, 0))
        ttk.Button(top, text="Generar resumen y quiz", command=self.process_file).pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Listo para comenzar")
        ttk.Label(container, textvariable=self.status_var).pack(anchor="w", pady=(10, 8))

        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)

        summary_tab = ttk.Frame(notebook, padding=10)
        quiz_tab = ttk.Frame(notebook, padding=10)
        notebook.add(summary_tab, text="Resumen")
        notebook.add(quiz_tab, text="Quiz")

        self.summary_text = tk.Text(summary_tab, wrap="word", height=20)
        self.summary_text.pack(fill="both", expand=True)

        self.quiz_text = tk.Text(quiz_tab, wrap="word", height=20)
        self.quiz_text.pack(fill="both", expand=True)

    def select_file(self):
        path = filedialog.askopenfilename(
            title="Selecciona un archivo",
            filetypes=[
                ("Archivos soportados", "*.pdf *.docx *.txt *.md *.csv *.json *.log *.rtf"),
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
            return

        self.summary_text.delete("1.0", tk.END)
        lines = [ln.strip("• ").strip() for ln in summary.splitlines() if ln.strip()]
        if not lines:
            lines = [summary]
        self.summary_text.insert(tk.END, "Resumen:\n\n")
        for idx, item in enumerate(lines, start=1):
            self.summary_text.insert(tk.END, f"{idx}. {item}\n\n")

        self.quiz_text.delete("1.0", tk.END)
        if not quiz:
            self.quiz_text.insert(tk.END, "No fue posible generar preguntas para este archivo.")
        else:
            for idx, q in enumerate(quiz, start=1):
                self.quiz_text.insert(tk.END, f"{idx}) {q.question}\n")
                for opt_idx, option in enumerate(q.options, start=1):
                    marker = "✓" if option == q.answer else "-"
                    self.quiz_text.insert(tk.END, f"   {marker} Opción {opt_idx}: {option}\n")
                self.quiz_text.insert(tk.END, "\n")

        self.status_var.set(f"Procesado correctamente: {self.file_path.name}")


def main():
    root = tk.Tk()
    PDFResumesDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
