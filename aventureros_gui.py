import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests

API_URL = "http://localhost:8000"
CLASES_POSIBLES = ["Paladin", "picaro", "sacerdote", "barbaro"]

class AventureroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gremio De Aventureros")
        self.root.geometry("500x720")
        self.root.configure(bg="#f0f2f5")
        self.id_por_nombre = {}  # mapa nombre → id

        self.estilo_frame = {"padx": 15, "pady": 10, "bd": 2, "relief": "groove", "bg": "#ffffff"}
        self.estilo_label = {"bg": "#ffffff", "font": ("Helvetica", 10)}
        self.estilo_entry = {"width": 35, "font": ("Helvetica", 10)}
        self.estilo_button = {"bg": "#000000", "fg": "white", "font": ("Helvetica", 10, "bold"), "padx": 5, "pady": 2}

        self.crear_widgets()

    def crear_widgets(self):
        self.crear_seccion_crear()
        self.crear_seccion_ver()
        self.crear_seccion_mision()
        self.crear_seccion_completar()
        self.crear_seccion_resultado()

    def crear_seccion_crear(self):
        frame = tk.LabelFrame(self.root, text="Crear Aventurero", **self.estilo_frame)
        frame.pack(padx=10, pady=5, fill="x")

        tk.Label(frame, text="Nombre:", **self.estilo_label).grid(row=0, column=0, sticky="e")
        self.nombre_entry = tk.Entry(frame, **self.estilo_entry)
        self.nombre_entry.grid(row=0, column=1, pady=2)

        tk.Label(frame, text="Clase:", **self.estilo_label).grid(row=1, column=0, sticky="e")
        self.clase_var = tk.StringVar(value=CLASES_POSIBLES[0])
        self.clase_menu = tk.OptionMenu(frame, self.clase_var, *CLASES_POSIBLES)
        self.clase_menu.config(width=33, font=("Helvetica", 10))
        self.clase_menu.grid(row=1, column=1, pady=2)

        tk.Button(frame, text="Crear Aventurero", command=self.crear_aventurero, **self.estilo_button).grid(row=2, column=0, columnspan=2, pady=5)

    def crear_seccion_ver(self):
        frame = tk.LabelFrame(self.root, text="Consultar Aventurero", **self.estilo_frame)
        frame.pack(padx=10, pady=5, fill="x")

        tk.Label(frame, text="Nombre:", **self.estilo_label).grid(row=0, column=0, sticky="e")
        self.ver_nombre_entry = tk.Entry(frame, **self.estilo_entry)
        self.ver_nombre_entry.grid(row=0, column=1, pady=2)

        tk.Button(frame, text="Ver Aventurero", command=self.ver_aventurero, **self.estilo_button).grid(row=1, column=0, columnspan=2, pady=5)

    def crear_seccion_mision(self):
        frame = tk.LabelFrame(self.root, text="Agregar Misión", **self.estilo_frame)
        frame.pack(padx=10, pady=5, fill="x")

        labels = ["Aventurero:", "Misión:", "Descripción:", "XP (opcional):"]
        entries = []

        for i, text in enumerate(labels):
            tk.Label(frame, text=text, **self.estilo_label).grid(row=i, column=0, sticky="e")
            entry = tk.Entry(frame, **self.estilo_entry)
            entry.grid(row=i, column=1, pady=2)
            entries.append(entry)

        self.nombre_mision_entry, self.mision_nombre_entry, self.mision_desc_entry, self.mision_xp_entry = entries

        tk.Button(frame, text="Agregar Misión", command=self.agregar_mision, **self.estilo_button).grid(row=4, column=0, columnspan=2, pady=5)

    def crear_seccion_completar(self):
        frame = tk.LabelFrame(self.root, text="Completar Misión", **self.estilo_frame)
        frame.pack(padx=10, pady=5, fill="x")

        tk.Label(frame, text="Aventurero:", **self.estilo_label).grid(row=0, column=0, sticky="e")
        self.completar_entry = tk.Entry(frame, **self.estilo_entry)
        self.completar_entry.grid(row=0, column=1, pady=2)

        tk.Button(frame, text="Completar Misión", command=self.completar_mision, **self.estilo_button).grid(row=1, column=0, columnspan=2, pady=5)

    def crear_seccion_resultado(self):
        frame = tk.LabelFrame(self.root, text="Resultado", **self.estilo_frame)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.resultado_text = scrolledtext.ScrolledText(frame, height=12, wrap="word", font=("Courier", 10))
        self.resultado_text.pack(fill="both", expand=True)

    def mostrar_resultado(self, texto):
        self.resultado_text.delete("1.0", tk.END)
        self.resultado_text.insert(tk.END, texto)

    def crear_aventurero(self):
        nombre = self.nombre_entry.get()
        clase = self.clase_var.get()
        try:
            res = requests.post(f"{API_URL}/personajes", json={"nombre": nombre, "clase": clase})
            datos = res.json()
            self.id_por_nombre[nombre] = datos["id"]
            self.mostrar_resultado(datos)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def ver_aventurero(self):
        nombre = self.ver_nombre_entry.get()
        try:
            for i in range(1, 100):  # Scan de los 100 primeros ids por ahora (mejor con un endpoint de búsqueda por nombre)
                res = requests.get(f"{API_URL}/personajes/{i}")
                if res.status_code == 200:
                    datos = res.json()
                    if datos["nombre"].lower() == nombre.lower():
                        self.id_por_nombre[nombre] = i
                        self.mostrar_resultado(datos)
                        return
            raise Exception("Aventurero no encontrado.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def agregar_mision(self):
        nombre = self.nombre_mision_entry.get()
        id_aventurero = self.id_por_nombre.get(nombre)
        if not id_aventurero:
            messagebox.showerror("Error", "Debes consultar primero al aventurero.")
            return

        nombre_m = self.mision_nombre_entry.get()
        descripcion = self.mision_desc_entry.get()
        experiencia = self.mision_xp_entry.get()
        xp = int(experiencia) if experiencia else 50

        try:
            res = requests.post(
                f"{API_URL}/personajes/{id_aventurero}/misiones/{nombre_m}",
                json={"nombre": nombre_m, "descripcion": descripcion, "experiencia": xp}
            )
            self.mostrar_resultado(res.json())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def completar_mision(self):
        nombre = self.completar_entry.get()
        id_aventurero = self.id_por_nombre.get(nombre)
        if not id_aventurero:
            messagebox.showerror("Error", "Debes consultar primero al aventurero.")
            return

        try:
            res = requests.post(f"{API_URL}/personajes/{id_aventurero}/completar")
            self.mostrar_resultado(res.json())
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = AventureroApp(root)
    root.mainloop()
