import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import threading
import re

from pix2text import Pix2Text
from sympy import symbols, sympify, Eq, solve, integrate, sin, cos, tan


class MathApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Математический помощник")
        self.root.geometry("900x650")
        self.root.configure(bg="#FFE4EC")

        self.image_path = None
        self.model = None
        self.loading = True

        self.setup_ui()
        self.load_model()

    # ---------------- UI ----------------
    def setup_ui(self):
        top = tk.Frame(self.root, bg="#FFE4EC")
        top.pack(pady=10)

        btn_style = {
            "font": ("Segoe UI", 13, "bold"),  # крупнее шрифт
            "bg": "#FFB6C1",
            "fg": "#4A3B42",
            "activebackground": "#FF69B4",
            "relief": tk.RAISED,
            "bd": 2,
            "width": 18,  # шире кнопки
            "height": 2  # 🔥 ВАЖНО: делает их выше
        }

        tk.Button(top, text="📁 Загрузить фото", command=self.load_image, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="🔍 Распознать", command=self.recognize, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="🧮 Вычислить", command=self.calculate, **btn_style).pack(side=tk.LEFT, padx=5)

        self.img_label = tk.Label(self.root, bg="white")
        self.img_label.pack(pady=10)

        self.entry = tk.Entry(self.root, font=("Courier", 14))
        self.entry.pack(fill=tk.X, padx=15, pady=5)

        self.output = tk.Text(self.root, height=10, font=("Segoe UI", 12))
        self.output.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.status = tk.Label(self.root, text="Загрузка модели...", bg="#FFD1DC")
        self.status.pack(fill=tk.X)

    # ---------------- MODEL ----------------
    def load_model(self):
        def load():
            try:
                self.model = Pix2Text()
                self.loading = False
                self.status.config(text="Модель готова")
            except Exception as e:
                self.status.config(text=f"Ошибка модели: {e}")

        threading.Thread(target=load, daemon=True).start()

    # ---------------- IMAGE ----------------
    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if not path:
            return

        self.image_path = path
        img = Image.open(path)
        img.thumbnail((500, 300))
        photo = ImageTk.PhotoImage(img)

        self.img_label.config(image=photo)
        self.img_label.image = photo

    # ---------------- CLEAN ----------------
    def clean(self, text):
        if not text:
            return ""

        text = text.replace(' ', '')
        text = text.replace('÷', '/')
        text = text.replace('\\div', '/')
        text = text.replace('×', '*')
        text = text.replace('\\times', '*')
        text = text.replace('−', '-')

        return text

    # ---------------- PARSER ----------------
    def parse(self, expr):
        expr = self.clean(expr)

        expr = expr.replace('^', '**')

        # тригонометрия
        expr = expr.replace('sin', 'sin')
        expr = expr.replace('cos', 'cos')
        expr = expr.replace('tan', 'tan')

        # неявное умножение
        expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)
        expr = re.sub(r'(\d)\(', r'\1*(', expr)
        expr = re.sub(r'\)(\d)', r')*\1', expr)
        expr = re.sub(r'\)\(', r')*(', expr)

        return expr

    # ---------------- RECOGNIZE ----------------
    def recognize(self):
        if not self.image_path:
            messagebox.showwarning("Ошибка", "Сначала загрузите фото")
            return

        if self.loading:
            messagebox.showwarning("Ошибка", "Модель ещё грузится")
            return

        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "Распознавание...\n")

        def run():
            try:
                latex = self.model.recognize_formula(self.image_path)
                clean = self.clean(latex)

                self.root.after(0, lambda: self.show_result(latex, clean))
            except Exception as e:
                self.root.after(0, lambda: self.output.insert(tk.END, f"Ошибка: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def show_result(self, latex, clean):
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, f"Распознано:\n{latex}\n\n")
        self.output.insert(tk.END, f"Очищено:\n{clean}\n")

        self.entry.delete(0, tk.END)
        self.entry.insert(0, clean)

    # ---------------- CALCULATE ----------------
    def calculate(self):
        expr = self.entry.get().strip()

        if not expr:
            messagebox.showwarning("Ошибка", "Введите выражение")
            return

        self.output.delete(1.0, tk.END)

        try:
            x = symbols('x')

            # уравнение
            if '=' in expr:
                left, right = expr.split('=')

                left = self.parse(left)
                right = self.parse(right)

                eq = Eq(sympify(left), sympify(right))
                result = solve(eq, x)

                self.output.insert(tk.END, f"Решение: {result}")
                return

            expr = self.parse(expr)

            # интегралы (очень простая поддержка)
            if expr.startswith("integrate"):
                result = eval(expr, {"integrate": integrate, "x": x})
            else:
                result = sympify(expr)

            if hasattr(result, 'is_number') and result.is_number:
                result = float(result)
                if result.is_integer():
                    result = int(result)

            self.output.insert(tk.END, f"Результат: {result}")

        except Exception as e:
            self.output.insert(tk.END, f"Ошибка: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MathApp(root)
    root.mainloop()