import os
import json
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox


import cv2
import random
import glob
from PIL import Image, ImageTk
from ultralytics import YOLO


try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


USUARIO_ACTUAL = ""
ACIERTOS = 0
DESACIERTOS = 0
HISTORIAL_FILE = "historial_sesiones.json"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema Educativo Inteligente")
        self.geometry("900x650")
        self.configure(bg="#1e1e24")
        
        # Centrar la ventana en la pantalla
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Estilos TTK
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure(".", background="#1e1e24", foreground="#ffffff", font=("Helvetica", 11))
        self.style.configure("TFrame", background="#1e1e24")
        self.style.configure("Card.TFrame", background="#282830", relief="flat")
        self.style.configure("TButton", background="#007acc", foreground="#ffffff", font=("Helvetica", 11, "bold"), borderwidth=0, padding=10)
        self.style.map("TButton", background=[("active", "#0098ff")])
        self.style.configure("Secundario.TButton", background="#4a4a5a", foreground="#ffffff")
        self.style.map("Secundario.TButton", background=[("active", "#6a6a7c")])
        self.style.configure("Modo.TButton", background="#26a69a", foreground="#ffffff", font=("Helvetica", 13, "bold"), padding=20)
        self.style.map("Modo.TButton", background=[("active", "#2bbbad")])
        self.style.configure("TLabel", background="#1e1e24", foreground="#ffffff")
        self.style.configure("Titulo.TLabel", font=("Helvetica", 22, "bold"), background="#1e1e24", foreground="#007acc")
        self.style.configure("Subtitulo.TLabel", font=("Helvetica", 14), background="#1e1e24", foreground="#b0b0b5")
        self.style.configure("CardTitulo.TLabel", font=("Helvetica", 16, "bold"), background="#282830", foreground="#26a69a")
        
        self.style.configure("Treeview", background="#282830", foreground="#ffffff", fieldbackground="#282830", rowheight=30, font=("Helvetica", 10))
        self.style.configure("Treeview.Heading", background="#007acc", foreground="#ffffff", font=("Helvetica", 11, "bold"))
        self.style.map("Treeview", background=[("selected", "#005999")])
        
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Inicializar puerto serie para Raspberry Pi 4 (UART)
        self.ser = None
        if SERIAL_AVAILABLE:
            try:
                self.ser = serial.Serial('/dev/serial0', 9600, timeout=1)
                print("📡 UART: Puerto /dev/serial0 abierto correctamente a 9600 baudios.")
            except Exception as e:
                print(f"UART: No se pudo abrir /dev/serial0 ({e}). Se continuará sin UART.")
        else:
            print("UART: El módulo 'pyserial' no está instalado. Se continuará sin UART.")
            

        print("Inicializando motores de IA en segundo plano...")
        self.modelo_digitos = YOLO("best_num.onnx", task="detect")
        self.yolo_model = None
        self.bucle_camara_iniciado = False
        
        self.mostrar_pantalla_registro()

    def enviar_resultado_uart(self, correcto):
        global ACIERTOS
        if hasattr(self, 'ser') and self.ser is not None:
            try:
                
                if correcto and ACIERTOS > 5:
                    dato = b'3'
                    print(f"¡Racha de Campeón! Enviando '3' por UART (Aciertos totales: {ACIERTOS})")
                else:
                    dato = b'1' if correcto else b'0'
                    
                self.ser.write(dato)
                print(f"UART: Enviado '{dato.decode()}' (correcto={correcto})")
            except Exception as e:
                print(f" UART: Error al enviar datos: {e}")

    def limpiar_pantalla(self):
        self.detener_stream_camara()
        for widget in self.container.winfo_children():
            widget.destroy()

    def iniciar_stream_camara(self, label_destino):
        self.lbl_stream_target = label_destino
        
        if hasattr(self, 'cap') and self.cap is not None and self.cap.isOpened():
            self.stream_activo = True
            return

        self.stream_activo = False
        try:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.stream_activo = True
                
                if not self.bucle_camara_iniciado:
                    self.bucle_camara_iniciado = True
                    self.actualizar_stream_camara()
            else:
                self.cap = None
                label_destino.config(text="[Error: No se pudo abrir la cámara index 0]", image="")
        except Exception as e:
            print(f"Error iniciando cámara: {e}")
            label_destino.config(text=f"[Error iniciando cámara: {e}]", image="")

    def actualizar_stream_camara(self):
        if not hasattr(self, 'cap') or self.cap is None or not self.cap.isOpened():
            return
            
        ret, frame = self.cap.read()
        if ret and frame is not None:
            self.ultimo_frame_capturado = frame.copy()
            
            if getattr(self, 'stream_activo', False):
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(img_rgb)
                img_pil.thumbnail((450, 280))
                
                self.photo_stream = ImageTk.PhotoImage(img_pil)
                if hasattr(self, 'lbl_stream_target') and self.lbl_stream_target.winfo_exists():
                    self.lbl_stream_target.config(image=self.photo_stream, text="")
                    
        self.after(50, self.actualizar_stream_camara)

    def pausar_stream_camara(self):
        self.stream_activo = False

    def detener_stream_camara(self):
        self.stream_activo = False
        self.bucle_camara_iniciado = False
        if hasattr(self, 'cap') and self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def mostrar_pantalla_registro(self):
        self.limpiar_pantalla()
        lbl_titulo = ttk.Label(self.container, text="Sistema Educativo Inteligente para Niños", style="Titulo.TLabel", anchor="center")
        lbl_titulo.pack(pady=(40, 10))
        lbl_sub = ttk.Label(self.container, text="Aprende matemáticas y conteo de forma divertida", style="Subtitulo.TLabel", anchor="center")
        lbl_sub.pack(pady=(0, 40))
        
        card = ttk.Frame(self.container, style="Card.TFrame")
        card.pack(pady=10, padx=50, fill="both", expand=True)
        
        lbl_instruccion = ttk.Label(card, text="Registro de Estudiante", style="CardTitulo.TLabel", background="#282830")
        lbl_instruccion.pack(pady=(30, 20))
        lbl_nombre = ttk.Label(card, text="Ingresa tu Nombre o ID:", font=("Helvetica", 12), background="#282830")
        lbl_nombre.pack(pady=5)
        
        self.entry_usuario = tk.Entry(card, font=("Helvetica", 14), bg="#383842", fg="#ffffff", insertbackground="white", borderwidth=0, highlightthickness=1, highlightbackground="#4a4a5a", highlightcolor="#007acc")
        self.entry_usuario.pack(pady=10, ipady=5, ipadx=10)
        
        btn_ingresar = ttk.Button(card, text="Iniciar Sesión", command=self.registrar_usuario)
        btn_ingresar.pack(pady=20)
        
        btn_historial = ttk.Button(self.container, text="Ver Historial de Sesiones", style="Secundario.TButton", command=self.mostrar_pantalla_historial)
        btn_historial.pack(pady=20)

    def registrar_usuario(self):
        global USUARIO_ACTUAL, ACIERTOS, DESACIERTOS
        nombre = self.entry_usuario.get().strip()
        if not nombre:
            messagebox.showwarning("Campo Vacío", "Por favor, ingresa tu nombre o ID para comenzar.")
            return
        
        USUARIO_ACTUAL = nombre
        ACIERTOS = 0
        DESACIERTOS = 0
        self.mostrar_pantalla_plataforma()

    def mostrar_pantalla_plataforma(self):
        self.limpiar_pantalla()
        lbl_titulo = ttk.Label(self.container, text=f"¡Bienvenido, {USUARIO_ACTUAL}!", style="Titulo.TLabel", anchor="center")
        lbl_titulo.pack(pady=(20, 5))
        lbl_sub = ttk.Label(self.container, text="Elige una de las siguientes actividades para comenzar:", style="Subtitulo.TLabel", anchor="center")
        lbl_sub.pack(pady=(0, 30))
        
        modos_frame = ttk.Frame(self.container)
        modos_frame.pack(pady=20, fill="x")
        
        card1 = ttk.Frame(modos_frame, style="Card.TFrame")
        card1.pack(side="left", padx=20, fill="both", expand=True)
        lbl_modo1 = ttk.Label(card1, text="Modo 1: Análisis de Pizarra", style="CardTitulo.TLabel", background="#282830", anchor="center")
        lbl_modo1.pack(pady=15)
        lbl_desc1 = ttk.Label(card1, text="Resuelve operaciones matemáticas en la pizarra utilizando un marcador y deja que la cámara evalúe tu respuesta.", font=("Helvetica", 11), background="#282830", wraplength=350, justify="center")
        lbl_desc1.pack(pady=15, padx=10)
        btn_modo1 = ttk.Button(card1, text="Jugar Modo 1", style="Modo.TButton", command=self.mostrar_modo_1)
        btn_modo1.pack(pady=20)
        
        card2 = ttk.Frame(modos_frame, style="Card.TFrame")
        card2.pack(side="right", padx=20, fill="both", expand=True)
        lbl_modo2 = ttk.Label(card2, text="Modo 2: Conteo de Objetos", style="CardTitulo.TLabel", background="#282830", anchor="center")
        lbl_modo2.pack(pady=15)
        lbl_desc2 = ttk.Label(card2, text="Cuenta los objetos que aparecen en la pantalla, escribe el número en la pizarra y comprueba si tu conteo es correcto.", font=("Helvetica", 11), background="#282830", wraplength=350, justify="center")
        lbl_desc2.pack(pady=15, padx=10)
        btn_modo2 = ttk.Button(card2, text="Jugar Modo 2", style="Modo.TButton", command=self.mostrar_modo_2)
        btn_modo2.pack(pady=20)
        
        btn_frame = ttk.Frame(self.container)
        btn_frame.pack(pady=30, fill="x")
        btn_cerrar = ttk.Button(btn_frame, text="Terminar y Guardar Sesión", style="Secundario.TButton", command=self.guardar_y_cerrar_sesion)
        btn_cerrar.pack(side="bottom", pady=10)

    def generar_operacion_matematica(self):
        operadores = ['+', '-', '*', '/']
        operador = random.choice(operadores)
        
        while True:
            if operador == '+':
                a = random.randint(1, 98)
                b = random.randint(1, 99 - a)
                resultado = a + b
            elif operador == '-':
                a = random.randint(1, 99)
                b = random.randint(1, a)
                resultado = a - b
            elif operador == '*':
                a = random.randint(1, 49)
                max_b = 99 // a
                if max_b < 1:
                    continue
                b = random.randint(1, max_b)
                resultado = a * b
            elif operador == '/':
                resultado = random.randint(1, 99)
                b = random.randint(1, 10)
                a = resultado * b
                
            if 0 <= resultado < 100:
                return a, operador, b, resultado

    def nuevo_ejercicio_modo1(self, iniciar=False):
        a, op, b, res = self.generar_operacion_matematica()
        self.current_a = a
        self.current_op = op
        self.current_b = b
        self.current_result = res
        self.texto_operacion = f"{a} {op} {b} = ?"
        
        if not iniciar:
            self.lbl_operacion.config(text=self.texto_operacion, foreground="#ffffff")
            self.entry_respuesta_sim.delete(0, tk.END)
            self.stream_activo = True

    def mostrar_modo_1(self):
        self.limpiar_pantalla()
        if not hasattr(self, 'modo1_aciertos'):
            self.modo1_aciertos = 0
            self.modo1_errores = 0
            
        self.nuevo_ejercicio_modo1(iniciar=True)

        lbl_titulo = ttk.Label(self.container, text="Modo 1: Análisis de Pizarra (Matemáticas)", style="Titulo.TLabel", anchor="center")
        lbl_titulo.pack(pady=10)
        
        self.card_modo1 = ttk.Frame(self.container, style="Card.TFrame")
        self.card_modo1.pack(pady=10, padx=20, fill="both", expand=True)
        
        left_frame = ttk.Frame(self.card_modo1, style="Card.TFrame")
        left_frame.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        
        self.lbl_stats_modo1 = ttk.Label(left_frame, text=f"Aciertos: {self.modo1_aciertos}  |  Errores: {self.modo1_errores}", font=("Helvetica", 12, "bold"), background="#282830", foreground="#b0b0b5")
        self.lbl_stats_modo1.pack(pady=5)
        
        self.lbl_operacion = ttk.Label(left_frame, text=self.texto_operacion, font=("Helvetica", 42, "bold"), background="#282830", foreground="#ffffff")
        self.lbl_operacion.pack(pady=20)
        
        btn_frame_ia = ttk.Frame(left_frame, style="Card.TFrame")
        btn_frame_ia.pack(pady=5)
        
        btn_evaluar_cam = ttk.Button(btn_frame_ia, text="Capturar Pizarra", style="TButton", command=self.evaluar_pizarra_camara)
        btn_evaluar_cam.pack(side="left", padx=5)
        
        btn_evaluar_file = ttk.Button(btn_frame_ia, text="Cargar Archivo", style="Secundario.TButton", command=self.seleccionar_imagen_evaluar_modo1)
        btn_evaluar_file.pack(side="left", padx=5)
        
        lbl_simulacion = ttk.Label(left_frame, text="Simulación manual por teclado:", font=("Helvetica", 10), background="#282830", foreground="#8a8a95")
        lbl_simulacion.pack(pady=(10, 2))
        
        sim_frame = ttk.Frame(left_frame, style="Card.TFrame")
        sim_frame.pack(pady=5)
        
        self.entry_respuesta_sim = tk.Entry(sim_frame, font=("Helvetica", 14), width=10, bg="#383842", fg="#ffffff", insertbackground="white", borderwidth=0, highlightthickness=1, highlightbackground="#4a4a5a", highlightcolor="#26a69a")
        self.entry_respuesta_sim.pack(side="left", padx=5, ipady=3)
        self.entry_respuesta_sim.bind("<Return>", lambda event: self.verificar_respuesta_sim())
        
        btn_verificar = ttk.Button(sim_frame, text="Verificar", style="TButton", command=self.verificar_respuesta_sim)
        btn_verificar.pack(side="left", padx=5)
        
        btn_nuevo = ttk.Button(left_frame, text="Nuevo Ejercicio", style="Secundario.TButton", command=lambda: self.nuevo_ejercicio_modo1(iniciar=False))
        btn_nuevo.pack(pady=10)
        
        right_frame = ttk.Frame(self.card_modo1, style="Card.TFrame")
        right_frame.pack(side="right", fill="both", expand=True, padx=20, pady=10)
        
        lbl_pizarra_title = ttk.Label(right_frame, text="Pizarra Detectada / Captura", font=("Helvetica", 12, "bold"), background="#282830", foreground="#26a69a")
        lbl_pizarra_title.pack(pady=5)
        
        self.lbl_imagen_modo1 = ttk.Label(right_frame, background="#282830", text="[Iniciando transmisión de cámara...]", foreground="#8a8a95", font=("Helvetica", 11, "italic"), anchor="center")
        self.lbl_imagen_modo1.pack(pady=15, fill="both", expand=True)
        
        btn_volver = ttk.Button(self.container, text="Volver al Menú Principal 🔙", style="Secundario.TButton", command=self.volver_al_menu_desde_modo1)
        btn_volver.pack(pady=10)
        
        self.iniciar_stream_camara(self.lbl_imagen_modo1)

    def verificar_respuesta_sim(self):
        global ACIERTOS, DESACIERTOS
        res_str = self.entry_respuesta_sim.get().strip()
        if not res_str:
            messagebox.showwarning("Campo Vacío", "Ingresa un número para simular la respuesta.")
            return
            
        try:
            respuesta_usr = int(res_str)
        except ValueError:
            messagebox.showerror("Error", "Ingresa un número entero válido.")
            return
            
        if respuesta_usr == self.current_result:
            self.modo1_aciertos += 1
            ACIERTOS += 1
            self.enviar_resultado_uart(True)
            self.lbl_operacion.config(foreground="#26a69a")
            messagebox.showinfo("¡Correcto!", "¡Excelente trabajo! Respuesta correcta.")
            self.nuevo_ejercicio_modo1(iniciar=False)
        else:
            self.modo1_errores += 1
            DESACIERTOS += 1
            self.enviar_resultado_uart(False)
            self.lbl_operacion.config(foreground="#ef5350")
            messagebox.showerror("Incorrecto", f"Respuesta incorrecta.\nEl resultado era: {self.current_result}")
            self.lbl_operacion.config(foreground="#ffffff")
            self.entry_respuesta_sim.delete(0, tk.END)
            
        self.lbl_stats_modo1.config(text=f"Aciertos: {self.modo1_aciertos}  |  Errores: {self.modo1_errores}")

    def evaluar_pizarra_camara(self):
        if not hasattr(self, 'ultimo_frame_capturado') or self.ultimo_frame_capturado is None:
            messagebox.showwarning("Cámara no lista", "El feed de la cámara se está reiniciando. Por favor, espera un segundo.")
            return
            
        self.pausar_stream_camara()
        self.lbl_imagen_modo1.config(image="", text="[Procesando con IA en segundo plano...]")
        
        frame_evaluar = self.ultimo_frame_capturado.copy()
        threading.Thread(target=self._async_evaluar_pizarra, args=(frame_evaluar,), daemon=True).start()
    
    def seleccionar_imagen_evaluar_modo1(self):
        from tkinter import filedialog
        ruta = filedialog.askopenfilename(
            title="Selecciona la imagen de la pizarra para evaluar",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp")]
        )
        if ruta:
            self.lbl_imagen_modo1.config(image="", text="[Procesando con IA...]")
            threading.Thread(target=self._async_evaluar_pizarra, args=(ruta,), daemon=True).start()

    def _async_evaluar_pizarra(self, origen):
        try:
            if origen is None or (not isinstance(origen, str) and origen.size == 0):
                raise ValueError("El fotograma de la cámara está vacío o corrupto.")

            resultados = self.modelo_digitos(origen, conf=0.40, imgsz=640, verbose=False)
            resultado_actual = resultados[0]
            
            img_bgr = resultado_actual.plot()
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_pil.thumbnail((450, 280))
            photo_img = ImageTk.PhotoImage(img_pil)
            
            boxes = resultado_actual.boxes
            numero_detectado = None
            if len(boxes) > 0:
                digitos_detectados = []
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    digit_char = resultado_actual.names[cls_id]
                    x1 = box.xyxy[0][0].item()
                    digitos_detectados.append((x1, digit_char))
                digitos_detectados.sort(key=lambda x: x[0])
                numero_str = "".join([d[1] for d in digitos_detectados])
                if numero_str.isdigit():
                    numero_detectado = int(numero_str)

            self.after(0, lambda: self._finalizar_evaluacion_modo1(numero_detectado, photo_img))
            
        except Exception as error_ia:
            mensaje_error = str(error_ia)
            self.after(0, lambda: messagebox.showerror("Error de Evaluación", f"Error en la inferencia: {mensaje_error}"))
            self.stream_activo = True    
    
    def _finalizar_evaluacion_modo1(self, numero_detectado, photo_img):
        global ACIERTOS, DESACIERTOS
        
        self.photo_img_modo1 = photo_img
        self.lbl_imagen_modo1.config(image=self.photo_img_modo1, text="")
        
        if numero_detectado is None:
            messagebox.showwarning("Sin Detecciones", "No se detectaron dígitos en la imagen de la pizarra.")
            self.stream_activo = True
            return
            
        if numero_detectado == self.current_result:
            self.modo1_aciertos += 1
            ACIERTOS += 1  # Suma previa para que la condicional UART verifique el valor correcto en tiempo real
            self.enviar_resultado_uart(True)
            self.lbl_operacion.config(foreground="#26a69a")
            messagebox.showinfo("¡Correcto!", f"La IA detectó el número {numero_detectado}.\n¡Respuesta correcta!")
            
            a, op, b, res = self.generar_operacion_matematica()
            self.current_a = a
            self.current_op = op
            self.current_b = b
            self.current_result = res
            self.texto_operacion = f"{a} {op} {b} = ?"
        else:
            self.modo1_errores += 1
            DESACIERTOS += 1
            self.enviar_resultado_uart(False)
            self.lbl_operacion.config(foreground="#ef5350")
            messagebox.showerror("Incorrecto", f"La IA detectó el número {numero_detectado}.\nEl resultado correcto era: {self.current_result}")
            
        self.lbl_stats_modo1.config(text=f"Aciertos: {self.modo1_aciertos}  |  Errores: {self.modo1_errores}")

    def mostrar_imagen_original_modo1(self, ruta):
        try:
            img_pil = Image.open(ruta)
            img_pil.thumbnail((450, 280))
            self.photo_img_modo1 = ImageTk.PhotoImage(img_pil)
            self.lbl_imagen_modo1.config(image=self.photo_img_modo1, text="")
        except Exception as e:
            print(f"Error mostrando imagen original Modo 1: {e}")

    def volver_al_menu_desde_modo1(self):
        self.mostrar_pantalla_plataforma()

    def cargar_modelo_yolo(self):
        if hasattr(self, 'yolo_model') and self.yolo_model is not None:
            return self.yolo_model
        
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(directorio_actual, "formas.onnx")
        
        print(f"Forzando la carga de: {model_path}")
        try:
            self.yolo_model = YOLO(model_path, task="detect")
            print(f"VERIFICACIÓN DE CLASES: {self.yolo_model.names}")
            return self.yolo_model
        except Exception as e:
            print(f"Error al cargar el ONNX: {e}")
            return None

    def nuevo_reto_modo2(self, Invisalign=False):
        self.imagen_nombre_modo2 = f"{random.randint(1, 10)}.png"
        self.ruta_imagen_modo2 = os.path.join(".", self.imagen_nombre_modo2)
        
        if not os.path.exists(self.ruta_imagen_modo2):
            pngs = glob.glob("*.png")
            pngs_validas = [p for p in pngs if os.path.basename(p).replace(".png", "").isdigit()]
            if pngs_validas:
                self.ruta_imagen_modo2 = random.choice(pngs_validas)
                self.imagen_nombre_modo2 = os.path.basename(self.ruta_imagen_modo2)
            elif pngs:
                self.ruta_imagen_modo2 = random.choice(pngs)
                self.imagen_nombre_modo2 = os.path.basename(self.ruta_imagen_modo2)
            else:
                messagebox.showerror("Error", "No se encontraron imágenes .png en la carpeta actual.")
                self.volver_al_menu_desde_modo2()
                return

        try:
            model = self.cargar_modelo_yolo()
            if model is None:
                return

            img_matriz = cv2.imread(self.ruta_imagen_modo2)
            if img_matriz is None:
                raise ValueError(f"No se pudo leer la imagen: {self.ruta_imagen_modo2}")

            resultados = model.predict(source=img_matriz, conf=0.25, imgsz=640, verbose=False)
            self.resultado_yolo_actual = resultados[0]
            
            boxes = self.resultado_yolo_actual.boxes
            names = self.resultado_yolo_actual.names
            self.conteos_modo2 = {'circle': 0, 'cross': 0, 'square': 0, 'triangle': 0}
            
            for box in boxes:
                cls_id = int(box.cls[0].item())
                name = names.get(cls_id, "").lower().strip()
            
                if 'square' in name or 'cuadrado' in name:
                    self.conteos_modo2['square'] += 1
                elif 'circle' in name or 'circulo' in name:
                    self.conteos_modo2['circle'] += 1
                elif 'triangle' in name or 'triangulo' in name:
                    self.conteos_modo2['triangle'] += 1
                elif 'cross' in name or 'cruz' in name:
                    self.conteos_modo2['cross'] += 1
                    
        except Exception as e:
            print(f" Error detallado en predicción Modo 2: {e}")
            messagebox.showerror("Error de Inferencia", f"No se pudo analizar la imagen con la IA: {e}")
            self.volver_al_menu_desde_modo2()
            return

        self.tipo_pregunta_modo2 = random.randint(0, 3)
        if self.tipo_pregunta_modo2 == 0:
            self.pregunta_texto_modo2 = "¿Cuántos círculos hay?"
            self.respuesta_correcta_modo2 = self.conteos_modo2['circle']
        elif self.tipo_pregunta_modo2 == 1:
            self.pregunta_texto_modo2 = "¿Cuántos cuadrados hay?"
            self.respuesta_correcta_modo2 = self.conteos_modo2['square']
        elif self.tipo_pregunta_modo2 == 2:
            self.pregunta_texto_modo2 = "¿Cuántos triángulos hay?"
            self.respuesta_correcta_modo2 = self.conteos_modo2['triangle']
        else:
            self.pregunta_texto_modo2 = "¿Cuántas figuras hay en total?"
            self.respuesta_correcta_modo2 = sum(self.conteos_modo2.values())

        if not Invisalign:
            self.lbl_pregunta_modo2.config(text=self.pregunta_texto_modo2)
            self.entry_respuesta_modo2.delete(0, tk.END)
            self.lbl_pizarra_modo2.config(image="", text="[Captura o carga tu respuesta para evaluar]")
            self.mostrar_imagen_original_modo2()
            self.iniciar_stream_camara(self.lbl_pizarra_modo2)

    def mostrar_imagen_original_modo2(self):
        try:
            img_pil = Image.open(self.ruta_imagen_modo2)
            img_pil.thumbnail((450, 280))
            self.photo_img_modo2 = ImageTk.PhotoImage(img_pil)
            self.lbl_imagen_modo2.config(image=self.photo_img_modo2)
        except Exception as e:
            print(f"Error cargando imagen original Modo 2: {e}")

    def mostrar_imagen_deteccion_modo2(self):
        try:
            img_bgr = self.resultado_yolo_actual.plot()
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_pil.thumbnail((450, 280))
            self.photo_img_modo2 = ImageTk.PhotoImage(img_pil)
            self.lbl_imagen_modo2.config(image=self.photo_img_modo2)
        except Exception as e:
            print(f"Error cargando imagen de detección figuras: {e}")

    def mostrar_pizarra_deteccion_modo2(self):
        try:
            img_bgr = self.resultado_digitos_actual.plot()
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_pil.thumbnail((450, 280))
            self.photo_img_pizarra_modo2 = ImageTk.PhotoImage(img_pil)
            self.lbl_pizarra_modo2.config(image=self.photo_img_pizarra_modo2, text="")
        except Exception as e:
            print(f"Error mostrando detección dígitos en Modo 2: {e}")

    def mostrar_modo_2(self):
        self.limpiar_pantalla()
        if not hasattr(self, 'modo2_aciertos'):
            self.modo2_aciertos = 0
            self.modo2_errores = 0
            
        self.nuevo_reto_modo2(Invisalign=True)

        lbl_titulo = ttk.Label(self.container, text="Modo 2: Conteo de Objetos (IA)", style="Titulo.TLabel", anchor="center")
        lbl_titulo.pack(pady=5)
        
        self.card_modo2 = ttk.Frame(self.container, style="Card.TFrame")
        self.card_modo2.pack(pady=10, padx=20, fill="both", expand=True)
        
        left_frame = ttk.Frame(self.card_modo2, style="Card.TFrame")
        left_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        
        self.lbl_stats_modo2 = ttk.Label(left_frame, text=f"Aciertos: {self.modo2_aciertos}  |  Errores: {self.modo2_errores}", font=("Helvetica", 12, "bold"), background="#282830", foreground="#b0b0b5")
        self.lbl_stats_modo2.pack(pady=5)
        
        self.lbl_pregunta_modo2 = ttk.Label(left_frame, text=self.pregunta_texto_modo2, font=("Helvetica", 14, "bold"), background="#282830", foreground="#26a69a")
        self.lbl_pregunta_modo2.pack(pady=5)
        
        self.lbl_imagen_modo2 = ttk.Label(left_frame, background="#282830")
        self.lbl_imagen_modo2.pack(pady=5)
        
        self.mostrar_imagen_original_modo2()
        
        btn_nuevo = ttk.Button(left_frame, text="Siguiente Imagen", style="Secundario.TButton", command=lambda: self.nuevo_reto_modo2(Invisalign=False))
        btn_nuevo.pack(pady=10)
        
        right_frame = ttk.Frame(self.card_modo2, style="Card.TFrame")
        right_frame.pack(side="right", fill="both", expand=True, padx=15, pady=10)
        
        lbl_pizarra_title = ttk.Label(right_frame, text="Captura de tu Pizarra", font=("Helvetica", 12, "bold"), background="#282830", foreground="#26a69a")
        lbl_pizarra_title.pack(pady=5)
        
        btn_frame_m2 = ttk.Frame(right_frame, style="Card.TFrame")
        btn_frame_m2.pack(pady=5)
        
        btn_camara = ttk.Button(btn_frame_m2, text="Capturar Pizarra", style="TButton", command=self.evaluar_conteo_camara)
        btn_camara.pack(side="left", padx=5)
        
        btn_archivo = ttk.Button(btn_frame_m2, text="Cargar Archivo", style="Secundario.TButton", command=self.seleccionar_imagen_evaluar_modo2)
        btn_archivo.pack(side="left", padx=5)
        
        self.lbl_pizarra_modo2 = ttk.Label(right_frame, background="#282830", text="[Iniciando transmisión de cámara...]", foreground="#8a8a95", font=("Helvetica", 11, "italic"), anchor="center")
        self.lbl_pizarra_modo2.pack(pady=10, fill="both", expand=True)
        
        sim_frame_m2 = ttk.Frame(right_frame, style="Card.TFrame")
        sim_frame_m2.pack(pady=5)
        
        lbl_sim_m2 = ttk.Label(sim_frame_m2, text="Teclado (Prueba):", font=("Helvetica", 10), background="#282830", foreground="#8a8a95")
        lbl_sim_m2.pack(side="left", padx=5)
        
        self.entry_respuesta_modo2 = tk.Entry(sim_frame_m2, font=("Helvetica", 14), width=8, bg="#383842", fg="#ffffff", insertbackground="white", borderwidth=0, highlightthickness=1, highlightbackground="#4a4a5a", highlightcolor="#26a69a")
        self.entry_respuesta_modo2.pack(side="left", padx=5, ipady=2)
        self.entry_respuesta_modo2.bind("<Return>", lambda event: self.verificar_respuesta_modo2())
        
        btn_verificar_m2 = ttk.Button(sim_frame_m2, text="Verificar ✔️", style="TButton", command=self.verificar_respuesta_modo2)
        btn_verificar_m2.pack(side="left", padx=5)
        
        btn_volver = ttk.Button(self.container, text="Volver al Menú Principal 🔙", style="Secundario.TButton", command=self.volver_al_menu_desde_modo2)
        btn_volver.pack(pady=10)
        
        self.iniciar_stream_camara(self.lbl_pizarra_modo2)

    def evaluar_conteo_camara(self):
        if not hasattr(self, 'ultimo_frame_capturado') or self.ultimo_frame_capturado is None:
            messagebox.showerror("Error", "No hay captura de cámara activa.")
            return
            
        self.pausar_stream_camara()
        self.lbl_pizarra_modo2.config(image="", text="[Procesando con IA...]")
        threading.Thread(target=self._async_evaluar_conteo, args=(self.ultimo_frame_capturado,), daemon=True).start()

    def seleccionar_imagen_evaluar_modo2(self):
        from tkinter import filedialog
        ruta = filedialog.askopenfilename(
            title="Selecciona la imagen de la pizarra para evaluar",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp")]
        )
        if ruta:
            self.lbl_pizarra_modo2.config(image="", text="[Procesando con IA...]")
            threading.Thread(target=self._async_evaluar_conteo, args=(ruta,), daemon=True).start()

    def _async_evaluar_conteo(self, origen):
        try:
            resultados = self.modelo_digitos(origen, conf=0.40, imgsz=640, verbose=False)
            self.resultado_digitos_actual = resultados[0]
            boxes = self.resultado_digitos_actual.boxes
            numero_detectado = None
            if len(boxes) > 0:
                digitos_detectados = []
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    digit_char = self.resultado_digitos_actual.names[cls_id]
                    x1 = box.xyxy[0][0].item()
                    digitos_detectados.append((x1, digit_char))
                digitos_detectados.sort(key=lambda x: x[0])
                numero_str = "".join([d[1] for d in digitos_detectados])
                if numero_str.isdigit():
                    numero_detectado = int(numero_str)
                    
            self.after(0, lambda: self._finalizar_evaluacion_modo2(numero_detectado))
        except Exception as e:
            self.stream_activo = True
            self.after(0, lambda: messagebox.showerror("Error de Evaluación", f"Error en inferencia: {e}"))

    def _finalizar_evaluacion_modo2(self, numero_detectado):
        global ACIERTOS, DESACIERTOS
        if numero_detectado is None:
            messagebox.showwarning("Sin Detecciones", "No se detectaron dígitos en la imagen.")
            self.iniciar_stream_camara(self.lbl_pizarra_modo2)
            return
            
        self.mostrar_pizarra_deteccion_modo2()
        if numero_detectado == self.respuesta_correcta_modo2:
            self.modo2_aciertos += 1
            ACIERTOS += 1  # Suma previa antes del UART
            self.enviar_resultado_uart(True)
            messagebox.showinfo("¡Correcto!", f"La IA detectó el número {numero_detectado} en la pizarra.\n¡Respuesta correcta!")
            self.mostrar_imagen_deteccion_modo2()
        else:
            self.modo2_errores += 1
            DESACIERTOS += 1
            self.enviar_resultado_uart(False)
            messagebox.showerror("Incorrecto", f"La IA detectó el número {numero_detectado}.\nEl conteo esperado era: {self.respuesta_correcta_modo2}")
            self.mostrar_imagen_deteccion_modo2()
            
        self.lbl_stats_modo2.config(text=f"Aciertos: {self.modo2_aciertos}  |  Errores: {self.modo2_errores}")

    def verificar_respuesta_modo2(self):
        global ACIERTOS, DESACIERTOS
        res_str = self.entry_respuesta_modo2.get().strip()
        if not res_str:
            messagebox.showwarning("Campo Vacío", "Ingresa una respuesta para continuar.")
            return
            
        try:
            respuesta_usr = int(res_str)
        except ValueError:
            messagebox.showerror("Error", "Ingresa un número entero válido.")
            return
            
        if respuesta_usr == self.respuesta_correcta_modo2:
            self.modo2_aciertos += 1
            ACIERTOS += 1
            self.enviar_resultado_uart(True)
            messagebox.showinfo("¡Correcto!", "¡Excelente conteo! Tu respuesta es correcta.")
            self.mostrar_imagen_deteccion_modo2()
        else:
            self.modo2_errores += 1
            DESACIERTOS += 1
            self.enviar_resultado_uart(False)
            messagebox.showerror("Incorrecto", f"Respuesta incorrecta.\nEl conteo correcto era: {self.respuesta_correcta_modo2}")
            self.mostrar_imagen_deteccion_modo2()
            
        self.lbl_stats_modo2.config(text=f"Aciertos: {self.modo2_aciertos}  |  Errores: {self.modo2_errores}")

    def volver_al_menu_desde_modo2(self):
        self.mostrar_pantalla_plataforma()

    def mostrar_pantalla_historial(self):
        self.limpiar_pantalla()
        lbl_titulo = ttk.Label(self.container, text="Historial de Sesiones Registradas", style="Titulo.TLabel", anchor="center")
        lbl_titulo.pack(pady=20)
        
        datos = []
        if os.path.exists(HISTORIAL_FILE):
            try:
                with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                    datos = json.load(f)
            except Exception as e:
                messagebox.showerror("Error de Lectura", f"No se pudo leer el archivo de historial: {e}")
        
        tabla_frame = ttk.Frame(self.container)
        tabla_frame.pack(fill="both", expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(tabla_frame)
        scrollbar.pack(side="right", fill="y")
        
        columnas = ("usuario", "fecha", "aciertos", "desaciertos", "puntaje")
        tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=tabla.yview)
        
        tabla.heading("usuario", text="Usuario / ID")
        tabla.heading("fecha", text="Fecha y Hora")
        tabla.heading("aciertos", text="Aciertos")
        tabla.heading("desaciertos", text="Desaciertos")
        tabla.heading("puntaje", text="Puntaje Final")
        
        tabla.column("usuario", width=150, anchor="center")
        tabla.column("fecha", width=200, anchor="center")
        tabla.column("aciertos", width=100, anchor="center")
        tabla.column("desaciertos", width=100, anchor="center")
        tabla.column("puntaje", width=120, anchor="center")

        try:
            datos_ordenados = sorted(datos, key=lambda x: x.get("fecha", ""), reverse=True)
            for d in datos_ordenados:
                tabla.insert("", "end", values=(
                    d.get("usuario", "N/A"),
                    d.get("fecha", "N/A"),
                    d.get("aciertos", 0),
                    d.get("desaciertos", 0),
                    d.get("puntaje", 0)
                ))
        except Exception as e:
            print(f"Error cargando tabla: {e}")
            
        tabla.pack(fill="both", expand=True)
        
        btn_volver = ttk.Button(self.container, text="Regresar al Registro 🔙", style="Secundario.TButton", command=self.mostrar_pantalla_registro)
        btn_volver.pack(pady=20)

    def guardar_y_cerrar_sesion(self):
        global USUARIO_ACTUAL, ACIERTOS, DESACIERTOS
        if not USUARIO_ACTUAL:
            self.mostrar_pantalla_registro()
            return
            
        if not messagebox.askyesno("Finalizar Sesión", "¿Estás seguro de que deseas terminar y guardar esta sesión?"):
            return
            
        total_respuestas = ACIERTOS + DESACIERTOS
        puntaje_final = (ACIERTOS * 10) if total_respuestas > 0 else 0
        
        nueva_sesion = {
            "usuario": USUARIO_ACTUAL,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "aciertos": ACIERTOS,
            "desaciertos": DESACIERTOS,
            "puntaje": puntaje_final
        }
        
        datos = []
        if os.path.exists(HISTORIAL_FILE):
            try:
                with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                    datos = json.load(f)
            except Exception:
                datos = []
                
        datos.append(nueva_sesion)
        
        try:
            with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Sesión Guardada", f"¡Sesión de {USUARIO_ACTUAL} guardada exitosamente!\nPuntaje: {puntaje_final}")
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"No se pudo guardar la sesión: {e}")
            
        USUARIO_ACTUAL = ""
        ACIERTOS = 0
        DESACIERTOS = 0
        self.mostrar_pantalla_registro()

if __name__ == "__main__":
    app = App()
    app.mainloop()