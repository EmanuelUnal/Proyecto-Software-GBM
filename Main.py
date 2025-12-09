import sqlite3
import tkinter as tk
import analisis
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.ticker as mticker
import sys, os
import shutil

# Try to import Pillow for better image support (JPEG, PNG); fall back to Tk PhotoImage for limited types.
try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False


def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


DB_PATH = resource_path("contabilidad_lechera.db")

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("V.A.C.A - Login / Registro")
        try:
            icon_path = Path(__file__).with_name("logo.ico")
            if icon_path.exists():
                root.iconbitmap(str(icon_path))
        except:
            pass
        self.root.geometry("1100x720")
        DB_PATH = Path(__file__).with_name("contabilidad_lechera.db")

        # Conexión a BD (facturas / usuarios)
        self.con = sqlite3.connect(DB_PATH)
        self.cursor = self.con.cursor()
        self._ensure_tables()

        # Conexión separada para pedidos (DB distinta)
        PEDIDOS_DB = DB_PATH.with_name("pedidos.db")
        self.ped_con = sqlite3.connect(PEDIDOS_DB)
        self.ped_cursor = self.ped_con.cursor()
        self._ensure_pedidos_tables()

        # Frames
        self.frame_login = ttk.Frame(self.root, padding=16)
        self.frame_register = ttk.Frame(self.root, padding=16)

        self.build_login_frame()
        self.build_register_frame()
        self.show_login()

    def _ensure_tables(self):
        # Tabla de usuarios: create with firma column
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                documento TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL,
                contrasena TEXT NOT NULL,
                rol TEXT NOT NULL,
                firma TEXT DEFAULT ''
            )
        """)
        # If DB existed before without 'firma', add the column
        self.cursor.execute("PRAGMA table_info(usuarios)")
        cols = [row[1] for row in self.cursor.fetchall()]
        if 'firma' not in cols:
            try:
                self.cursor.execute("ALTER TABLE usuarios ADD COLUMN firma TEXT DEFAULT ''")
            except Exception:
                # If alter fails for any reason, ignore; table still usable but without firma
                pass

        # Tabla de facturas
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor TEXT,
                fecha TEXT,
                producto TEXT,
                cantidad INTEGER,
                concepto TEXT,
                valoru REAL,
                iva REAL,
                retencion REAL,
                valort REAL,
                codigo_factura TEXT,
                codigo_pedido TEXT,
                subtotal REAL,
                total REAL
            )
        """)
        self.con.commit()

    def _ensure_pedidos_tables(self):
        # tablas en DB separada (pedidos.db)
        self.ped_cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedidos (
                codigo_pedido TEXT PRIMARY KEY,
                proveedor TEXT,
                fecha TEXT,
                estado TEXT
            )
        """)
        self.ped_cursor.execute("""
            CREATE TABLE IF NOT EXISTS pedido_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_pedido TEXT,
                producto TEXT,
                cantidad INTEGER,
                FOREIGN KEY(codigo_pedido) REFERENCES pedidos(codigo_pedido)
            )
        """)
        self.ped_con.commit()

        # sincronizar pedidos desde facturas (si existen códigos de pedido)
        try:
            self.cursor.execute("SELECT DISTINCT codigo_pedido, proveedor, fecha FROM facturas WHERE codigo_pedido IS NOT NULL AND codigo_pedido != ''")
            for codigo, proveedor, fecha in self.cursor.fetchall():
                self.ped_cursor.execute("SELECT 1 FROM pedidos WHERE codigo_pedido = ?", (codigo,))
                if not self.ped_cursor.fetchone():
                    self.ped_cursor.execute("INSERT INTO pedidos (codigo_pedido, proveedor, fecha, estado) VALUES (?, ?, ?, ?)",
                                            (codigo, proveedor or "", fecha or "", "Pendiente"))
                # items desde facturas
                self.cursor.execute("SELECT producto, cantidad FROM facturas WHERE codigo_pedido = ?", (codigo,))
                for producto, cantidad in self.cursor.fetchall():
                    self.ped_cursor.execute("""
                        SELECT 1 FROM pedido_items WHERE codigo_pedido = ? AND producto = ? AND cantidad = ?
                    """, (codigo, producto, cantidad))
                    if not self.ped_cursor.fetchone():
                        self.ped_cursor.execute("INSERT INTO pedido_items (codigo_pedido, producto, cantidad) VALUES (?, ?, ?)",
                                                (codigo, producto, cantidad))
            self.ped_con.commit()
        except Exception:
            pass

    # ---------------- LOGIN ----------------
    def build_login_frame(self):
        frm = self.frame_login
        try:
            icon_path = Path(__file__).with_name("logo.ico")
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass
        for w in frm.winfo_children():
            w.destroy()

        ttk.Label(frm, text="Iniciar Sesión", font=("Segoe UI", 14, "bold")).pack(pady=(0,10))

        inner = ttk.Frame(frm)
        inner.pack()

        ttk.Label(inner, text="Documento (ID):").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.e_doc = ttk.Entry(inner, width=30)
        self.e_doc.grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(inner, text="Contraseña:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.e_pw = ttk.Entry(inner, show="*", width=30)
        self.e_pw.grid(row=1, column=1, padx=6, pady=6)

        btn_frame = ttk.Frame(frm)
        btn_frame.pack(pady=12)

        ttk.Button(btn_frame, text="Iniciar Sesión", command=self.do_login).grid(row=0, column=0, padx=8)
        ttk.Button(btn_frame, text="Registrar Nuevo Usuario", command=self.show_register).grid(row=0, column=1, padx=8)
        ttk.Button(btn_frame, text="Salir", command=self.root.quit).grid(row=0, column=2, padx=8)

        ttk.Label(frm, text="Registra usuarios como Contadora o Auxiliar Contable", foreground="#333").pack(pady=(8,0))
        

    def show_login(self):
        self.frame_register.pack_forget()
        self.frame_login.pack(fill=tk.BOTH, expand=True)

    # ---------------- REGISTRO ----------------
    def build_register_frame(self):
        frm = self.frame_register
        for w in frm.winfo_children():
            w.destroy()

        ttk.Label(frm, text="Registro", font=("Segoe UI", 14, "bold")).pack(pady=(0,10))

        fields = ["Nombre completo", "Documento (ID)", "Correo", "Contraseña", "Confirmar contraseña"]
        self.reg_entries = {}
        for field in fields:
            ttk.Label(frm, text=field+":").pack(anchor="w", padx=10, pady=2)
            e = ttk.Entry(frm, width=36, show="*" if "Contraseña" in field else "")
            e.pack(padx=10, pady=2)
            self.reg_entries[field] = e

        ttk.Label(frm, text="Rol:").pack(anchor="w", padx=10, pady=2)
        self.rol_var = tk.StringVar(value="Auxiliar Contable")
        rol_frame = ttk.Frame(frm)
        rol_frame.pack(anchor="w", padx=10)
        ttk.Radiobutton(rol_frame, text="Auxiliar Contable", variable=self.rol_var, value="Auxiliar Contable").pack(side=tk.LEFT, padx=4)
        ttk.Radiobutton(rol_frame, text="Contadora", variable=self.rol_var, value="Contadora").pack(side=tk.LEFT, padx=4)

        btn_frame = ttk.Frame(frm)
        btn_frame.pack(pady=12)
        ttk.Button(btn_frame, text="Registrar", command=self.do_register).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Volver al Login", command=self.show_login).pack(side=tk.LEFT, padx=6)

    def show_register(self):
        self.frame_login.pack_forget()
        self.frame_register.pack(fill=tk.BOTH, expand=True)

    # ---------------- FUNCIONES ----------------
    def do_register(self):
        nombre = self.reg_entries["Nombre completo"].get().strip()
        doc = self.reg_entries["Documento (ID)"].get().strip()
        correo = self.reg_entries["Correo"].get().strip()
        pw1 = self.reg_entries["Contraseña"].get()
        pw2 = self.reg_entries["Confirmar contraseña"].get()
        rol = self.rol_var.get()

        if not all([nombre, doc, correo, pw1, pw2, rol]):
            messagebox.showwarning("Error", "Todos los campos son obligatorios")
            return
        if pw1 != pw2:
            messagebox.showwarning("Error", "Las contraseñas no coinciden")
            return
        self.cursor.execute("SELECT documento FROM usuarios WHERE documento = ?", (doc,))
        if self.cursor.fetchone():
            messagebox.showerror("Error", "Documento ya registrado")
            return
        self.cursor.execute("INSERT INTO usuarios (documento, nombre, correo, contrasena, rol, firma) VALUES (?, ?, ?, ?, ?, ?)",
                    (doc, nombre, correo, pw1, rol, ""))
        self.con.commit()
        messagebox.showinfo("Éxito", f"Usuario registrado como {rol}")
        self.show_login()

    def do_login(self):
        doc = self.e_doc.get().strip()
        pw = self.e_pw.get()
        if not doc or not pw:
            messagebox.showwarning("Faltan datos", "Documento y contraseña son obligatorios")
            return
        self.cursor.execute("SELECT documento, nombre, correo, contrasena, rol, firma FROM usuarios WHERE documento = ?", (doc,))
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Documento no registrado")
            return
        if pw != row[3]:
            messagebox.showerror("Error", "Contraseña incorrecta")
            return
        usuario = {"documento": row[0], "nombre": row[1], "correo": row[2], "rol": row[4], "firma": row[5] if len(row) > 5 else ""}
        self.launch_system(usuario)

    def launch_system(self, usuario):
        for w in self.root.winfo_children():
            w.destroy()
        app = SistemaContableApp(
            self.root,
            db_connection=self.con,
            usuario=usuario,
            cursor=self.cursor,
            ped_connection=self.ped_con,
            ped_cursor=self.ped_cursor
        )
        self.system_app = app

# -----------------
# Sistema Contable 
# -----------------
class SistemaContableApp:
    def __init__(self, root, db_connection, usuario, cursor, ped_connection=None, ped_cursor=None):
        self.root = root
        self.con = db_connection
        self.cursor = cursor
        # conexión y cursor para pedidos (base separada)
        self.ped_con = ped_connection
        self.ped_cursor = ped_cursor
        self.usuario = usuario
        self.root.title(f"V.A.C.A")
        try:
            icon_path = Path(__file__).with_name("logo.ico")
            if icon_path.exists():
                root.iconbitmap(str(icon_path))
        except:
            pass
        self.root.geometry("1100x720")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 50))
        self._create_bottom_bar()
        self.root.update()
        self.root.minsize(self.root.winfo_width(), self.root.winfo_height())


        rol = self.usuario.get("rol", "")
        if rol == "Auxiliar Contable":
            self.crear_tab_factura()
            self.crear_tab_generar_pedido()
            self.crear_tab_firma()
            self.crear_tab_cancelar_pedido()
        elif rol == "Contadora":
            self.crear_tab_analisis()
            self.crear_tab_graf()
            self.crear_tab_retenciones()
            self.crear_tab_revision_de_gastos()
            self._create_bottom_bar()


    def _create_bottom_bar(self):
        bottom = ttk.Frame(self.root)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=6)

        ttk.Label(bottom, text=f"Usuario: {self.usuario['nombre']} - {self.usuario['rol']}").pack(side=tk.LEFT, padx=10)
        ttk.Button(bottom, text="Cerrar Sesión", command=self.do_logout).pack(side=tk.RIGHT, padx=10)


    def do_logout(self):
        if messagebox.askyesno("Confirmar", "¿Cerrar sesión?"):
            for w in self.root.winfo_children():
                w.destroy()
            LoginApp(self.root)

    def crear_tab_factura(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Registrar Factura")

        # Hago 3 cajas: formulario, tabla y códigos/acciones
        form_box = ttk.LabelFrame(frame, text="Agregar Producto", padding=8)
        form_box.grid(row=0, column=0, sticky="w", padx=10, pady=(10,6))

        # --- Tabla de productos agregados (tabla temporal) dentro de un contenedor de ancho fijo ---
        columnas = ("producto", "cantidad", "concepto", "valoru", "iva", "retencion", "valort")

        # contenedor con ancho fijo para limitar la tabla temporal
        factura_holder = ttk.Frame(frame, width=420)
        factura_holder.grid(row=0, column=1, rowspan=1, padx=10, pady=10, sticky="ns")
        factura_holder.grid_propagate(False)   # evita que el contenido cambie el ancho

        # Treeview dentro del holder
        self.factura_table = ttk.Treeview(factura_holder, columns=columnas, show="headings", height=4)
        self.factura_table.heading("producto", text="Producto")
        self.factura_table.heading("cantidad", text="Cantidad")
        self.factura_table.heading("concepto", text="Concepto")
        self.factura_table.heading("valoru", text="ValorU")
        self.factura_table.heading("iva", text="Iva (%)")
        self.factura_table.heading("retencion", text="Retención")
        self.factura_table.heading("valort", text="ValorT")

        # columnas: ajustar anchos para que la tabla quede compacta
        self.factura_table.column("producto", width=240, anchor="w")
        self.factura_table.column("cantidad", width=105, anchor="center")
        self.factura_table.column("concepto", width=210, anchor="w")
        self.factura_table.column("valoru", width=135, anchor="e")
        self.factura_table.column("iva", width=60, anchor="center")
        self.factura_table.column("retencion", width=80, anchor="e")
        self.factura_table.column("valort", width=135, anchor="e")

        # llenar el holder sin que se expanda horizontalmente en el grid principal
        self.factura_table.pack(fill="both", expand=True)

        table_box = ttk.LabelFrame(frame, text="Productos en la Factura", padding=6)
        table_box.grid(row=2, column=0,columnspan=2, sticky="nsew", padx=10, pady=6)

        codes_box = ttk.LabelFrame(frame, text="Códigos y Acciones", padding=8)
        codes_box.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(6,10))

        # Ajustes de pesos del layout: dejar la columna derecha sin peso (fija) y dar espacio a la izquierda
        frame.grid_rowconfigure(0, weight=0)
        frame.grid_rowconfigure(1, weight=0)
        frame.grid_rowconfigure(2, weight=1)   # tabla principal (table_box) sí crece
        frame.grid_columnconfigure(0, weight=1)  # formulario / columna izquierda puede crecer
        frame.grid_columnconfigure(1, weight=0)  # columna del holder queda fija
        table_box.grid_rowconfigure(0, weight=1)
        table_box.grid_columnconfigure(0, weight=1)

        # Campos del formulario (en form_box)
        ttk.Label(form_box, text="Proveedor:").grid(row=0, column=0, sticky="e", padx=6, pady=4)#nombre del proveedor
        self.entry_proveedor = ttk.Entry(form_box)
        self.entry_proveedor.grid(row=0, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(form_box, text="Fecha (YYYY-MM-DD):").grid(row=0, column=2, sticky="e", padx=6, pady=4)#fecha de la factura
        self.entry_fecha = ttk.Entry(form_box)
        self.entry_fecha.grid(row=0, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(form_box, text="Producto:").grid(row=1, column=0, sticky="e", padx=6, pady=4)#nombre del producto
        self.entry_producto = ttk.Entry(form_box)
        self.entry_producto.grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(form_box, text="Cantidad:").grid(row=1, column=2, sticky="e", padx=6, pady=4)#cantidad del producto
        self.entry_cantidad = ttk.Entry(form_box)
        self.entry_cantidad.grid(row=1, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(form_box, text="Concepto:").grid(row=2, column=0, sticky="e", padx=6, pady=4)#descripcion del producto o su tipo, puede ser del tipo: agroquimico, medicamento, maquinaria, gastos administrativos, etc)
        self.entry_concepto = ttk.Entry(form_box)
        self.entry_concepto.grid(row=2, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(form_box, text="ValorU:").grid(row=2, column=2, sticky="e", padx=6, pady=4)#valor unitario del producto
        self.entry_valoru = ttk.Entry(form_box)
        self.entry_valoru.grid(row=2, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(form_box, text="Iva:").grid(row=3, column=0, sticky="e", padx=6, pady=4)#impuesto al consumo, su default es 1
        self.entry_iva = ttk.Entry(form_box)
        self.entry_iva.grid(row=3, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(form_box, text="Retencion:").grid(row=3, column=2, sticky="e", padx=6, pady=4)#impuesto directo al gobierno, se calcula en otra pestaña
        self.entry_retencion = ttk.Entry(form_box)
        self.entry_retencion.grid(row=3, column=3, sticky="w", padx=6, pady=4)

        # Botones para armar la factura (agregar item temporal y guardar factura)
        btn_frame_fact = ttk.Frame(form_box)
        btn_frame_fact.grid(row=4, column=0, columnspan=4, pady=6)
        ttk.Button(btn_frame_fact, text="Agregar Producto", command=self.agregar_producto_a_factura_table).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame_fact, text="Guardar Factura", command=self.guardar_factura).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame_fact, text="Limpiar Items", command=lambda: [self.factura_table.delete(i) for i in self.factura_table.get_children()]).pack(side=tk.LEFT, padx=6)


        # Tabla en table_box — permite expansión y columnas con ancho por defecto
        columns = ("proveedor", "fecha", "producto", "cantidad", "concepto", "valoru", "iva", "retencion", "valort", "codigo_factura", "codigo_pedido")
        self.productos_table = ttk.Treeview(table_box, columns=columns, show="headings", height=10)
        for col, title in [("proveedor","Proveedor"),("fecha","Fecha"),("producto","Producto"),("cantidad","Cantidad"),
                           ("concepto","Concepto"),("valoru","ValorU"),("iva","Iva"),("retencion","Retencion"),
                           ("valort","ValorT"),("codigo_factura","Codigo Factura"),("codigo_pedido","Codigo Pedido")]:
            self.productos_table.heading(col, text=title)
        # columnas ejemplo anchos
        self.productos_table.column("proveedor", width=150, anchor="w")
        self.productos_table.column("fecha", width=110, anchor="center")
        self.productos_table.column("producto", width=180, anchor="w")
        self.productos_table.column("cantidad", width=80, anchor="center")

        self.productos_table.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(table_box, orient="vertical", command=self.productos_table.yview)
        self.productos_table.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

        # Cargar datos desde la base de datos y mostrarlos en la tabla
        facturas = self.cargar_facturas()
        for f in facturas:
            # insertar sólo las primeras 11 columnas que tiene el Treeview
            self.productos_table.insert("", "end", values=f[:11])

        # Códigos y botón (en codes_box)
        ttk.Label(codes_box, text="Codigo factura:").grid(row=0, column=0, sticky="e", padx=6, pady=4)#codigo unico de la factura, puede ser del tipo: FE123456
        self.entry_codigo_factura = ttk.Entry(codes_box)
        self.entry_codigo_factura.grid(row=0, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(codes_box, text="Codigo pedido:").grid(row=0, column=2, sticky="e", padx=6, pady=4)#codigo unico del pedido
        self.entry_codigo_pedido = ttk.Entry(codes_box)
        self.entry_codigo_pedido.grid(row=0, column=3, sticky="w", padx=6, pady=4)

        ttk.Button(codes_box, text="Agregar Producto", command=self.agregar_producto).grid(row=0, column=4, padx=10, pady=4)#agrega la factura a la base de datos

    def crear_tab_firma(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Firma")

        ttk.Label(frame, text="Subir / Ver firma digital", font=("Segoe UI", 12)).pack(padx=10, pady=(10,6), anchor="center")

        # Area to display signature image
        self.firma_canvas_holder = ttk.Frame(frame, padding=8)
        self.firma_canvas_holder.pack(fill="both", expand=False, padx=10, pady=6)

        self.firma_label = ttk.Label(self.firma_canvas_holder, text="No hay firma cargada.")
        self.firma_label.pack()

        btns = ttk.Frame(frame)
        btns.pack(padx=10, pady=8, anchor="center")

        ttk.Button(btns, text="Seleccionar archivo de firma", command=self._seleccionar_y_guardar_firma).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Mostrar firma actual", command=self._mostrar_firma_actual).pack(side=tk.LEFT, padx=6)

        # Try to display current signature if exists
        self._mostrar_firma_actual()

    def _seleccionar_y_guardar_firma(self):
        # Abrir dialogo para seleccionar imagen
        filetypes = [("Imagen", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"), ("PNG", "*.png"), ("JPG", "*.jpg;*.jpeg"), ("GIF", "*.gif")]
        path = filedialog.askopenfilename(title="Seleccionar archivo de firma", filetypes=filetypes)
        if not path:
            return

        try:
            src = Path(path)
            app_dir = Path(__file__).parent
            # avoid collisions: prefix with documento to avoid overwriting different users' files
            stored_name = f"{self.usuario['documento']}_{src.name}"
            dst = app_dir / stored_name
            shutil.copy(src, dst)

            # Save filename in DB for this user
            self.cursor.execute("UPDATE usuarios SET firma = ? WHERE documento = ?", (stored_name, self.usuario['documento']))
            self.con.commit()
            # Update in-memory usuario
            self.usuario['firma'] = stored_name

            messagebox.showinfo("Éxito", f"Firma guardada como {stored_name}")
            self._mostrar_firma_actual()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la firma:\n{e}")

    def _mostrar_firma_actual(self):
        # Clear previous widgets in holder
        for w in self.firma_canvas_holder.winfo_children():
            w.destroy()

        firma_fname = self.usuario.get('firma', '') if isinstance(self.usuario, dict) else ""
        if not firma_fname:
            ttk.Label(self.firma_canvas_holder, text="No hay firma cargada.").pack()
            return

        app_dir = Path(__file__).parent
        img_path = app_dir / firma_fname
        if not img_path.exists():
            ttk.Label(self.firma_canvas_holder, text="Archivo de firma no encontrado.").pack()
            return

        try:
            if _HAS_PIL:
                img = Image.open(img_path)
                # Resize to fit nicely in UI if large
                max_w, max_h = 400, 200
                img.thumbnail((max_w, max_h))
                self._firma_photo = ImageTk.PhotoImage(img)
            else:
                # fallback: Tk PhotoImage supports PNG/GIF; may fail on JPG
                self._firma_photo = tk.PhotoImage(file=str(img_path))
            lbl = ttk.Label(self.firma_canvas_holder, image=self._firma_photo)
            lbl.image = self._firma_photo
            lbl.pack()
        except Exception as e:
            ttk.Label(self.firma_canvas_holder, text=f"No se pudo mostrar la firma: {e}").pack()

    def agregar_producto_a_factura_table(self):
        producto = self.entry_producto.get().strip()
        cantidad_s = self.entry_cantidad.get().strip()
        concepto = self.entry_concepto.get().strip()
        valoru_s = self.entry_valoru.get().strip()
        iva_s = self.entry_iva.get().strip()
        retencion_s = self.entry_retencion.get().strip()

        if not producto or not cantidad_s or not valoru_s:
            messagebox.showwarning("Faltan datos", "Producto, Cantidad y ValorU son obligatorios.")
            return
        try:
            cantidad = int(cantidad_s)
            valoru = float(valoru_s)
            iva = float(iva_s) if iva_s else 0.0
            retencion = float(retencion_s) if retencion_s else 0.0
        except Exception:
            messagebox.showerror("Error", "Cantidad debe ser entero. ValorU, Iva y Retención numéricos.")
            return
        if cantidad < 0 or valoru < 0:
            messagebox.showerror("Error", "Cantidad y ValorU deben ser >= 0.")
            return

        subtotal = cantidad * valoru
        valort = subtotal * (1 + iva / 100.0) 

        values = (producto, cantidad, concepto, valoru, iva, retencion, valort)
        self.factura_table.insert("", "end", values=values)

        # Limpiar campos del item (pero no proveedor/fecha/códigos)
        self.entry_producto.delete(0, tk.END)
        self.entry_cantidad.delete(0, tk.END)
        self.entry_concepto.delete(0, tk.END)
        self.entry_valoru.delete(0, tk.END)
        self.entry_iva.delete(0, tk.END)
        self.entry_retencion.delete(0, tk.END)

    def guardar_factura(self):
        proveedor = self.entry_proveedor.get().strip()
        fecha = self.entry_fecha.get().strip()
        codigo_fact = self.entry_codigo_factura.get().strip()
        codigo_ped = self.entry_codigo_pedido.get().strip()

        if not proveedor or not fecha or not codigo_fact:
            messagebox.showerror("Error", "Proveedor, Fecha y Código de factura son obligatorios para guardar.")
            return
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except Exception:
            messagebox.showerror("Error", "Fecha inválida. Use formato YYYY-MM-DD.")
            return

        items = self.factura_table.get_children()
        if not items:
            messagebox.showwarning("Sin ítems", "Agrega al menos un producto a la factura.")
            return

        try:
            for item in items:
                producto, cantidad, concepto, valoru, iva, retencion, valort = self.factura_table.item(item, "values")
                # convertir tipos correctamente
                cantidad = int(cantidad)
                valoru = float(valoru)
                iva = float(iva)
                retencion = float(retencion)
                subtotal = cantidad * valoru
                total = float(valort)

                self.cursor.execute("""
                    INSERT INTO facturas (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_factura, codigo_pedido, subtotal, total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_fact, codigo_ped, subtotal, total))
            self.con.commit()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo guardar la factura:\n{e}")
            return

        # Añadir visualmente todos los ítems a la tabla principal de facturas
        for item in items:
            producto, cantidad, concepto, valoru, iva, retencion, valort = self.factura_table.item(item, "values")
            vals = (proveedor, fecha, producto, int(cantidad), concepto, float(valoru), float(iva), float(retencion), float(valort), codigo_fact, codigo_ped)
            self.productos_table.insert("", "end", values=vals)

        # Limpiar tabla temporal y entradas de códigos (pero mantener proveedor/fecha si quieres)
        for item in items:
            self.factura_table.delete(item)

        # Opcional: limpiar códigos si prefieres
        # self.entry_codigo_factura.delete(0, tk.END)
        # self.entry_codigo_pedido.delete(0, tk.END)

        messagebox.showinfo("Factura guardada", f"Factura {codigo_fact} guardada con {len(items)} ítems.")
        
    def agregar_producto(self):
        # Leer campos
        proveedor = self.entry_proveedor.get().strip()
        fecha = self.entry_fecha.get().strip()
        producto = self.entry_producto.get().strip()
        cantidad_s = self.entry_cantidad.get().strip()
        concepto = self.entry_concepto.get().strip()
        valoru_s = self.entry_valoru.get().strip()
        iva_s = self.entry_iva.get().strip()
        retencion_s = self.entry_retencion.get().strip()
        codigo_fact = self.entry_codigo_factura.get().strip()
        codigo_ped = self.entry_codigo_pedido.get().strip()

        # Validaciones: no vacíos
        if not all([proveedor, fecha, producto, cantidad_s, concepto, valoru_s, iva_s, retencion_s, codigo_fact, codigo_ped]):
            messagebox.showerror("Error", "Debe completar todas las casillas.")
            return

        # Validar fecha formato YYYY-MM-DD
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except Exception:
            messagebox.showerror("Error", "Fecha inválida. Use formato YYYY-MM-DD.")
            return

        # Validar numéricos
        try:
            cantidad = int(cantidad_s)
            valoru = float(valoru_s)
            iva = float(iva_s)
            retencion = float(retencion_s)
        except Exception:
            messagebox.showerror("Error", "Cantidad debe ser entero. ValorU, Iva y Retencion deben ser numéricos.")
            return

        if cantidad < 0 or valoru < 0:
            messagebox.showerror("Error", "Cantidad y ValorU deben ser >= 0.")
            return

        # Cálculos: subtotal y valor total (aplica IVA porcentual)
        subtotal = cantidad * valoru
        valort = subtotal * (1 + iva / 100.0) - retencion
        total = valort

        # Insertar en la base de datos
        try:
            self.cursor.execute("""
                INSERT INTO facturas (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_factura, codigo_pedido, subtotal, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_fact, codigo_ped, subtotal, total))
            self.con.commit()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo guardar en la base de datos:\n{e}")
            return

        # Añadir fila a la tabla (Treeview espera 11 columnas)
        values = (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_fact, codigo_ped)
        self.productos_table.insert("", "end", values=values)

        # Limpiar entradas
        self.entry_proveedor.delete(0, tk.END)
        self.entry_fecha.delete(0, tk.END)
        self.entry_producto.delete(0, tk.END)
        self.entry_cantidad.delete(0, tk.END)
        self.entry_concepto.delete(0, tk.END)
        self.entry_valoru.delete(0, tk.END)
        self.entry_iva.delete(0, tk.END)
        self.entry_retencion.delete(0, tk.END)
        self.entry_codigo_factura.delete(0, tk.END)
        self.entry_codigo_pedido.delete(0, tk.END)

        messagebox.showinfo("Listo", "Producto agregado correctamente.")
        try:
            # sincronizar con pedidos.db si se dio un codigo_ped
            if codigo_ped:
                self.ped_cursor.execute("SELECT 1 FROM pedidos WHERE codigo_pedido = ?", (codigo_ped,))
                if not self.ped_cursor.fetchone():
                    # crear cabecera de pedido usando proveedor/fecha y estado pendiente
                    self.ped_cursor.execute("INSERT INTO pedidos (codigo_pedido, proveedor, fecha, estado) VALUES (?, ?, ?, ?)",
                                            (codigo_ped, proveedor, fecha, "Pendiente"))
                # insertar item si no existe
                self.ped_cursor.execute("SELECT 1 FROM pedido_items WHERE codigo_pedido = ? AND producto = ? AND cantidad = ?",
                                        (codigo_ped, producto, cantidad))
                if not self.ped_cursor.fetchone():
                    self.ped_cursor.execute("INSERT INTO pedido_items (codigo_pedido, producto, cantidad) VALUES (?, ?, ?)",
                                            (codigo_ped, producto, cantidad))
                self.ped_con.commit()
        except Exception:
            pass

    # -------------------------
    # TAB: Análisis
    # -------------------------
    def crear_tab_analisis(self):
#-----------Obtener productos de la base de datos-----------
        def lista():
            tabla = Path(__file__).with_name("contabilidad_lechera.db")
            conexion = sqlite3.connect(tabla)
            cursor = conexion.cursor()
            cursor.execute("SELECT DISTINCT producto FROM facturas")
            filas = cursor.fetchall()
            conexion.close()
            return sorted([fila[0] for fila in filas])
        
#-----Analizar comportamiento del precio de un producto--------
        def ana_productos():
            producto_pro = self.entrada_pro.get().strip()
            if producto_pro == "":
                messagebox.showwarning("Producto vacío", "Debe indicar el producto por evaluar.")
                return
            (a,b,c) = analisis.productos(producto_pro)
            if (a,b,c) == (0,0,0):
                messagebox.showerror("Producto no registrado", "El producto que se ha intentado analizar no tiene registros")
                return
            if (a,b,c) == (-1,-1,-1):
                messagebox.showwarning("Sin pedidos recientes", "No hay datos recientemente registrados que analizar")
                return
            r7.config(text=a, background="WHITE", borderwidth=2, relief="solid")
            r8.config(text=b, background="WHITE", borderwidth=2, relief="solid")
            r9.config(text=c, background="WHITE", borderwidth=2, relief="solid")

 #--------------Analizar posible proveedores-------------       
        def proveedores():
            producto_pro = self.entrada_pro.get().strip()
            if producto_pro == "":
                messagebox.showwarning("Producto vacío", "Debe indicar el producto por evaluar.")
                return
            (a,b,c) = analisis.recomendacion(producto_pro)
            if (a,b,c) == (0,0,0):
                messagebox.showerror("Producto no registrado", "El producto que se ha intentado analizar no tiene registros")
                return
            if (a,b,c) == (-1,-1,-1):
                messagebox.showwarning("Sin pedidos recientes", "No hay datos recientemente registrados que analizar")
                return
            r1.config(text=a, background="WHITE", borderwidth=2, relief="solid")
            r2.config(text=b, background="WHITE", borderwidth=2, relief="solid")
            r3.config(text=c, background="WHITE", borderwidth=2, relief="solid")

#--------------Análisis general de los gastos-----------------
        def general():
            (a,b,c) = analisis.general()
            if (a,b,c) == (-1,-1,-1):
                messagebox.showwarning("Sin datos", "No hay datos que actualizar")
            r4.config(text=a, background="WHITE", borderwidth=2, relief="solid")
            r5.config(text=b, background="WHITE", borderwidth=2, relief="solid")
            r6.config(text=c, background="WHITE", borderwidth=2, relief="solid")

#---------------------Modelar la interfaz---------------------
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Análisis de Gastos")

        fb = ttk.LabelFrame(frame, text="Herramientas de análisis", padding=8)
        fb.place(rely=0.02, relwidth=1, relheight=1)
        ttk.Label(fb, text="Escoger producto a evaluar:", anchor="center").place(rely=0.02, relx=0.4, relheight=0.04, relwidth=0.2)
        self.entrada_pro = ttk.Combobox(fb, values=lista(), state="readonly", width=30)
        self.entrada_pro.place(rely=0.08, relx=0.4, relheight=0.05, relwidth=0.2)

        ttk.Button(fb, text="Empresas", command=proveedores).place(rely=0.16, relx=0.13, relheight=0.07, relwidth=0.16)

        ttk.Button(fb, text="General", command=general).place(rely=0.16, relx=0.42, relheight=0.07, relwidth=0.16)

        ttk.Button(fb, text="Producto", command=ana_productos).place(rely=0.16, relx=0.71, relheight=0.07, relwidth=0.16)
        
        ttk.Label(fb, text="Proveedor más barato:", anchor="center").place(rely=0.25, relx=0.1, relheight=0.08, relwidth=0.2)
        ttk.Label(fb, text="Proveedor más confiable:", anchor="center").place(rely=0.5, relx=0.1, relheight=0.08, relwidth=0.2)
        ttk.Label(fb, text="Proveedor con menor\naumento de precios:", anchor="center").place(rely=0.75, relx=0.1, relheight=0.08, relwidth=0.2)
        ttk.Label(fb, text="Promedio de gastos en los\núltimos tres meses:", anchor="center").place(rely=0.25, relx=0.4, relheight=0.08, relwidth=0.2)
        ttk.Label(fb, text="Producto de mayor inversión:", anchor="center").place(rely=0.5, relx=0.4, relheight=0.08, relwidth=0.2)
        ttk.Label(fb, text="Aumento del gasto en tres meses:", anchor="center").place(rely=0.75, relx=0.4, relheight=0.08, relwidth=0.2)
        ttk.Label(fb, text="Precio actual:", anchor="center").place(rely=0.25, relx=0.7, relheight=0.08, relwidth=0.2)
        ttk.Label(fb, text="Comportamiento en los\núltimos seis meses:", anchor="center").place(rely=0.5, relx=0.7, relheight=0.08, relwidth=0.2)
        ttk.Label(fb, text="Posible comportamiento futuro:", anchor="center").place(rely=0.75, relx=0.7, relheight=0.08, relwidth=0.2)

        r1 = ttk.Label(fb, anchor="center")
        r2 = ttk.Label(fb, anchor="center")
        r3 = ttk.Label(fb, anchor="center")
        r4 = ttk.Label(fb, anchor="center")
        r5 = ttk.Label(fb, anchor="center")
        r6 = ttk.Label(fb, anchor="center")
        r7 = ttk.Label(fb, anchor="center")
        r8 = ttk.Label(fb, anchor="center")
        r9 = ttk.Label(fb, anchor="center")

        r1.place(rely=0.33, relx=0.1, relheight=0.17, relwidth=0.2)
        r2.place(rely=0.58, relx=0.1, relheight=0.17, relwidth=0.2)
        r3.place(rely=0.83, relx=0.1, relheight=0.17, relwidth=0.2)
        r4.place(rely=0.33, relx=0.4, relheight=0.17, relwidth=0.2)
        r5.place(rely=0.58, relx=0.4, relheight=0.17, relwidth=0.2)
        r6.place(rely=0.83, relx=0.4, relheight=0.17, relwidth=0.2)
        r7.place(rely=0.33, relx=0.7, relheight=0.17, relwidth=0.2)
        r8.place(rely=0.58, relx=0.7, relheight=0.17, relwidth=0.2)
        r9.place(rely=0.83, relx=0.7, relheight=0.17, relwidth=0.2)

    """
        r1.place(rely=0.25, relx=0.1, relheight=0.23, relwidth=0.2)
        r2.place(rely=0.5, relx=0.1, relheight=0.23, relwidth=0.2)
        r3.place(rely=0.75, relx=0.1, relheight=0.23, relwidth=0.2)
        r4.place(rely=0.25, relx=0.4, relheight=0.23, relwidth=0.2)
        r5.place(rely=0.5, relx=0.4, relheight=0.23, relwidth=0.2)
        r6.place(rely=0.75, relx=0.4, relheight=0.23, relwidth=0.2)
        r7.place(rely=0.25, relx=0.7, relheight=0.23, relwidth=0.2)
        r8.place(rely=0.5, relx=0.7, relheight=0.23, relwidth=0.2)
        r9.place(rely=0.75, relx=0.7, relheight=0.23, relwidth=0.2)
    """
    #--------------------------
    #TAB: Gráficos
    #--------------------------
    def crear_tab_graf(self):
#-----------Obtener productos de la base de datos-----------
        def lista():
            tabla = Path(__file__).with_name("contabilidad_lechera.db")
            conexion = sqlite3.connect(tabla)
            cursor = conexion.cursor()
            cursor.execute("SELECT DISTINCT producto FROM facturas")
            filas = cursor.fetchall()
            conexion.close()
            return sorted([fila[0] for fila in filas])
        
#-----------Mostrar gráfico del comportamiento de un producto-----------     
        def grafico_producto():
            for widget in self.grafico.winfo_children():
                widget.destroy()
            producto = self.entrada_producto.get().strip()
            if producto == "":
                messagebox.showwarning("Producto vacío", "Debe indicar qué producto desea analizar")
                return
            
            meses, valores = analisis.historial_productos(producto)
            if meses == 0:
                messagebox.showerror("No existe el producto", "No hay registros del producto que se intenta buscar")
                return
            if meses == -1:
                messagebox.showwarning("Sin pedidos recientes", "No hay datos recientemente registrados que analizar")
                return
            if meses == -2:
                messagebox.showwarning("Datos insuficientes", "No hay suficientes registros para realizar bien el análisis")
                return
            figura = Figure(figsize=(5, 4), dpi=100)
            graficar = figura.add_subplot(111)
            graficar.plot(meses, valores)
            graficar.set_title("Evolución precio {}".format(producto))
            canvas = FigureCanvasTkAgg(figura, master=self.grafico)
            canvas.draw()
            canvas.get_tk_widget().pack()
        
#-----------Mostrar un grafico de los gastos generales-----------     
        def grafico_gastos():
            for widget in self.grafico.winfo_children():
                widget.destroy()          
            meses, valores = analisis.historial_gasto()
            if meses == 0:
                messagebox.showerror("No hay datos", "No hay registros para analizar")
                return
            if meses == -1:
                messagebox.showwarning("Datos insuficientes", "No hay suficientes registros para realizar bien el análisis")
                return
            figura = Figure(figsize=(5, 4), dpi=100)
            graficar = figura.add_subplot(111)
            graficar.plot(meses, valores)
            graficar.set_title("Historial de gastos")
            graficar.ticklabel_format(style='plain', axis='y')     # desactiva notación científica
            graficar.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, pos: f"{x/1_000_000:.1f}M$"))
            canvas = FigureCanvasTkAgg(figura, master=self.grafico)
            canvas.draw()
            canvas.get_tk_widget().pack()

#-----------Mostrar un gráfico de los impuestos pagados-----------     
        def grafico_impuesto():
            for widget in self.grafico.winfo_children():
                widget.destroy()          
            meses, valores = analisis.historial_impuesto()
            if meses == 0:
                messagebox.showerror("No hay datos", "No hay registros para analizar")
                return
            if meses == -1:
                messagebox.showwarning("Datos insuficientes", "No hay suficientes registros para realizar bien el análisis")
                return
            figura = Figure(figsize=(5, 4), dpi=100)
            graficar = figura.add_subplot(111)
            graficar.plot(meses, valores)
            graficar.set_title("Historial de gastos")
            graficar.ticklabel_format(style='plain', axis='y')     # desactiva notación científica
            graficar.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, pos: f"{x/1_000_000:.1f}M$"))
            canvas = FigureCanvasTkAgg(figura, master=self.grafico)
            canvas.draw()
            canvas.get_tk_widget().pack()

#-----------Modelar interfaz-----------
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Gráficos")
        self.grafico = ttk.Label(frame, background="WHITE")
        self.grafico.place(rely=0.2, relwidth=1, relheight=0.80)
        boton1 = ttk.Button(frame, text="Precios de productos", command=grafico_producto)
        boton1.place(rely=0.05, relx=0.11, relheight=0.07, relwidth=0.15)
        self.entrada_producto = ttk.Combobox(frame, values=lista(), state="readonly", width=30)
        self.entrada_producto.place(rely=0.13, relx=0.11, relheight=0.04, relwidth=0.15)
        boton2 = ttk.Button(frame, text="Impuestos", command=grafico_impuesto)
        boton2.place(rely=0.05, relx=0.37, relheight=0.07, relwidth=0.15)
        boton3 = ttk.Button(frame, text="Gasto", command=grafico_gastos)
        boton3.place(rely=0.05, relx=0.63, relheight=0.07, relwidth=0.15)

    # -------------------------
    # TAB: Revisión de Gastos Mensuales
    # -------------------------
    def crear_tab_revision_de_gastos(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Revisión de Gastos Mensuales")

        ttk.Label(frame, text="Consulta rápida de gastos mensuales").grid(row=0, column=0, padx=10, pady=20, sticky="w")

        filter_box = ttk.LabelFrame(frame, text="Filtros", padding=6)
        filter_box.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,8))
        # Si existe una tabla previa de productos, destruirla para evitar referencias inválidas
        if hasattr(self, "productos_table") and isinstance(self.productos_table, ttk.Treeview):
            try:
                self.productos_table.destroy()
            except Exception:
                pass
        filter_box.grid_columnconfigure(6, weight=1)

        ttk.Label(filter_box, text="Proveedor:").grid(row=0, column=0, padx=6, pady=4, sticky="e")
        self.filter_proveedor = ttk.Entry(filter_box, width=20)
        self.filter_proveedor.grid(row=0, column=1, padx=6, pady=4, sticky="w")

        ttk.Label(filter_box, text="Producto:").grid(row=0, column=2, padx=6, pady=4, sticky="e")
        self.filter_producto = ttk.Entry(filter_box, width=20)
        self.filter_producto.grid(row=0, column=3, padx=6, pady=4, sticky="w")

        ttk.Label(filter_box, text="Desde (YYYY-MM-DD):").grid(row=0, column=4, padx=6, pady=4, sticky="e")
        self.filter_fecha_desde = ttk.Entry(filter_box, width=14)
        self.filter_fecha_desde.grid(row=0, column=5, padx=6, pady=4, sticky="w")

        ttk.Label(filter_box, text="Hasta (YYYY-MM-DD):").grid(row=0, column=6, padx=12, pady=4, sticky="e")
        self.filter_fecha_hasta = ttk.Entry(filter_box, width=14)
        self.filter_fecha_hasta.grid(row=0, column=7, padx=6, pady=4, sticky="w")

        ttk.Button(filter_box, text="Aplicar filtro", command=self.filtrar_gastos).grid(row=1, column=0, padx=6, pady=4, sticky="e")
        ttk.Button(filter_box, text="Limpiar filtro", command=self.limpiar_filtro).grid(row=1, column=1, padx=(0,6), pady=4, sticky="w")

        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        table_box = ttk.LabelFrame(frame, text="Productos en la Factura", padding=6)
        table_box.grid(row=2, column=0, sticky="nsew", padx=10, pady=6)

        table_box.grid_rowconfigure(0, weight=1)
        table_box.grid_columnconfigure(0, weight=1)

        columns = ("proveedor", "fecha", "producto", "cantidad", "concepto", "valoru", "iva", "retencion", "valort", "codigo_factura", "codigo_pedido")
        self.productos_table = ttk.Treeview(table_box, columns=columns, show="headings", height=12)
        for col, title in [("proveedor","Proveedor"),("fecha","Fecha"),("producto","Producto"),("cantidad","Cantidad"),
                           ("concepto","Concepto"),("valoru","ValorU"),("iva","Iva"),("retencion","Retencion"),
                           ("valort","ValorT"),("codigo_factura","Codigo Factura"),("codigo_pedido","Codigo Pedido")]:
            self.productos_table.heading(col, text=title)

        self.productos_table.column("proveedor", width=150, anchor="w")
        self.productos_table.column("fecha", width=110, anchor="center")
        self.productos_table.column("producto", width=180, anchor="w")
        self.productos_table.column("cantidad", width=80, anchor="center")

        self.productos_table.bind("<Double-1>", self._on_edit_product)

        self.productos_table.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(table_box, orient="vertical", command=self.productos_table.yview)
        self.productos_table.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

        facturas = self.cargar_facturas()
        self._refresh_productos_table(facturas)

    def _on_edit_product(self, event):
        """Handler para doble click: abre ventana de edición para la fila cliqueada."""
        item = self.productos_table.identify_row(event.y)
        if not item:
            return
        try:
            factura_id = int(item)
        except Exception:
            vals = self.productos_table.item(item, "values")
            if not vals:
                return
            codigo_fact = vals[9] if len(vals) > 9 else None
            if not codigo_fact:
                messagebox.showerror("Editar", "No se puede identificar el registro en la base de datos.")
                return
            self.cursor.execute("SELECT id FROM facturas WHERE codigo_factura = ? LIMIT 1", (codigo_fact,))
            r = self.cursor.fetchone()
            if not r:
                messagebox.showerror("Editar", "Registro no encontrado en la base de datos.")
                return
            factura_id = r[0]
        self._open_edit_window(factura_id)

    def _open_edit_window(self, factura_id):
        """Abre Toplevel con campos para editar la factura identificada por factura_id."""
        self.cursor.execute("SELECT proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_factura, codigo_pedido FROM facturas WHERE id = ?", (factura_id,))
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Editar", "No se encontró la factura en la base de datos.")
            return

        win = tk.Toplevel(self.root)
        win.title(f"Editar factura #{factura_id}")
        win.transient(self.root)
        win.grab_set()

        labels = ["Proveedor", "Fecha (YYYY-MM-DD)", "Producto", "Cantidad", "Concepto", "ValorU", "Iva (%)", "Retención", "ValorT", "Codigo Factura", "Codigo Pedido"]
        entries = {}
        for i, label in enumerate(labels):
            ttk.Label(win, text=label).grid(row=i, column=0, padx=8, pady=4, sticky="e")
            ent = ttk.Entry(win, width=30)
            ent.grid(row=i, column=1, padx=8, pady=4, sticky="w")
            ent.insert(0, "" if row[i] is None else str(row[i]))
            entries[label] = ent


        def _on_save():
            self._save_edited_product(factura_id, entries, win)

        ttk.Button(win, text="Guardar cambios", command=_on_save).grid(row=len(labels), column=0, padx=8, pady=8)
        ttk.Button(win, text="Cancelar", command=win.destroy).grid(row=len(labels), column=1, padx=8, pady=8, sticky="w")

    def _save_edited_product(self, factura_id, entries, win):
        """Valida, actualiza BD y actualiza fila del Treeview."""
        proveedor = entries["Proveedor"].get().strip()
        fecha = entries["Fecha (YYYY-MM-DD)"].get().strip()
        producto = entries["Producto"].get().strip()
        cantidad_s = entries["Cantidad"].get().strip()
        concepto = entries["Concepto"].get().strip()
        valoru_s = entries["ValorU"].get().strip()
        iva_s = entries["Iva (%)"].get().strip()
        retencion_s = entries["Retención"].get().strip()
        codigo_fact = entries["Codigo Factura"].get().strip()
        codigo_ped = entries["Codigo Pedido"].get().strip()

        if not all([proveedor, fecha, producto, cantidad_s, concepto, valoru_s, iva_s, retencion_s, codigo_fact, codigo_ped]):
            messagebox.showerror("Error", "Debe completar todas las casillas.")
            return
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except Exception:
            messagebox.showerror("Error", "Fecha inválida. Use formato YYYY-MM-DD.")
            return
        try:
            cantidad = int(cantidad_s)
            valoru = float(valoru_s)
            iva = float(iva_s)
            retencion = float(retencion_s)
        except Exception:
            messagebox.showerror("Error", "Cantidad debe ser entero. ValorU, Iva y Retención numéricos.")
            return
        if cantidad < 0 or valoru < 0:
            messagebox.showerror("Error", "Cantidad y ValorU deben ser >= 0.")
            return

        subtotal = cantidad * valoru
        valort = subtotal * (1 + iva / 100.0) - retencion
        total = valort

        try:
            self.cursor.execute("""
                UPDATE facturas
                SET proveedor=?, fecha=?, producto=?, cantidad=?, concepto=?, valoru=?, iva=?, retencion=?, valort=?, codigo_factura=?, codigo_pedido=?, subtotal=?, total=?
                WHERE id=?
            """, (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_fact, codigo_ped, subtotal, total, factura_id))
            self.con.commit()
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo actualizar la base de datos:\n{e}")
            return

        iid = str(factura_id)
        if iid in self.productos_table.get_children(''):
            newvals = (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_fact, codigo_ped)
            self.productos_table.item(iid, values=newvals)
        else:
            for item in self.productos_table.get_children(''):
                vals = self.productos_table.item(item, "values")
                if len(vals) > 9 and vals[9] == codigo_fact:
                    newvals = (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_fact, codigo_ped)
                    self.productos_table.item(item, values=newvals)
                    break

        win.destroy()
        messagebox.showinfo("Listo", "Factura actualizada correctamente.")

    def _refresh_productos_table(self, facturas):
        """Llena la Treeview productos_table con la lista de facturas pasada."""
        for item in self.productos_table.get_children():
            self.productos_table.delete(item)
        for f in facturas:
            try:
                raw_id = f[13] if f and len(f) > 13 else None
                iid = str(raw_id) if raw_id is not None else None
            except Exception:
                iid = None

            # Si hay un iid válido lo usamos; si no, dejamos que Tk lo genere (no pasar iid)
            if iid:
                self.productos_table.insert("", "end", iid=iid, values=f[:11])
            else:
                self.productos_table.insert("", "end", values=f[:11])

    def filtrar_gastos(self):
        """Aplica los filtros ingresados y refresca la tabla."""
        proveedor_f = self.filter_proveedor.get().strip().lower()
        producto_f = self.filter_producto.get().strip().lower()
        fecha_desde_s = self.filter_fecha_desde.get().strip()
        fecha_hasta_s = self.filter_fecha_hasta.get().strip()

        fecha_desde = None
        fecha_hasta = None
        try:
            if fecha_desde_s:
                fecha_desde = datetime.strptime(fecha_desde_s, "%Y-%m-%d")
            if fecha_hasta_s:
                fecha_hasta = datetime.strptime(fecha_hasta_s, "%Y-%m-%d")
        except Exception:
            messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            return

        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            messagebox.showerror("Error", "La fecha 'Desde' no puede ser posterior a 'Hasta'.")
            return

        facturas = self.cargar_facturas()
        resultados = []
        for f in facturas:

            if not f or len(f) < 2:
                continue
            proveedor = (f[0] or "").lower()
            fecha_s = f[1] or ""
            producto = (f[2] or "").lower()
            concepto = (f[4] or "").lower()

            if proveedor_f and proveedor_f not in proveedor:
                continue
            if producto_f and producto_f not in producto:
                continue
            # filtro por rango de fechas
            try:
                fecha_fact = datetime.strptime(fecha_s, "%Y-%m-%d")
            except Exception:
                # omitir filas con fecha inválida
                continue
            if fecha_desde and fecha_fact < fecha_desde:
                continue
            if fecha_hasta and fecha_fact > fecha_hasta:
                continue

            resultados.append(f)
        self._refresh_productos_table(resultados)
        
    def limpiar_filtro(self):
        """Limpia controles de filtro y recarga todas las facturas."""
        self.filter_proveedor.delete(0, tk.END)
        self.filter_producto.delete(0, tk.END)
        try:
            self.filter_fecha_desde.delete(0, tk.END)
            self.filter_fecha_hasta.delete(0, tk.END)
        except Exception:
            pass
        facturas = self.cargar_facturas()
        self._refresh_productos_table(facturas)


    # -------------------------
    # TAB: Registrar Pedidos
    # -------------------------

    def agregar_producto_tabla(self):
        producto = self.entry_producto_pedido.get()
        cantidad = self.entry_cantidad_pedido.get()

        if not producto or not cantidad.isdigit():
            messagebox.showwarning("Error", "Debe ingresar un producto y una cantidad válida.")
            return

        self.pedido_table.insert("", "end", values=(producto, cantidad))
        self.entry_producto_pedido.delete(0, "end")
        self.entry_cantidad_pedido.delete(0, "end")

    def registrar_pedido(self):
        proveedor = self.entry_proveedor_pedido.get().strip()
        fecha = self.entry_fecha_pedido.get().strip()
        estado = self.combo_estado.get().strip()
        productos = self.pedido_table.get_children()

        if not proveedor or not fecha or not productos:
            messagebox.showerror("Error", "Todos los campos y al menos un producto son obligatorios.")
            return

        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except Exception:
            messagebox.showerror("Error", "Fecha inválida. Use formato YYYY-MM-DD.")
            return

        self.ped_cursor.execute("SELECT codigo_pedido FROM pedidos ORDER BY codigo_pedido DESC LIMIT 1")
        ultimo = self.ped_cursor.fetchone()
        
        if ultimo:
            # ultimo[0] → 'PD5012' por ejemplo
            numero = int(ultimo[0].replace("PD", ""))
            nuevo_numero = numero + 1
        else:
            # Si es la primera vez o la base está vacía
            nuevo_numero = 5001  # o donde quieras empezar
        
        codigo_pedido = f"PD{nuevo_numero}"
        # Guardar pedido en pedidos.db
        try:
            self.ped_cursor.execute("INSERT INTO pedidos (codigo_pedido, proveedor, fecha, estado) VALUES (?, ?, ?, ?)",
                                    (codigo_pedido, proveedor, fecha, estado))
            for item in productos:
                producto, cantidad = self.pedido_table.item(item, "values")
                self.ped_cursor.execute("INSERT INTO pedido_items (codigo_pedido, producto, cantidad) VALUES (?, ?, ?)",
                                        (codigo_pedido, producto, int(cantidad)))
            self.ped_con.commit()
        except Exception as e:
            messagebox.showerror("Error BD Pedidos", f"No se pudo guardar el pedido en pedidos.db:\n{e}")
            return

        # Insertar visualmente en la tabla de la derecha (una fila por item)
        for item in productos:
            producto, cantidad = self.pedido_table.item(item, "values")
            self.tabla_registro_pedidos.insert("", "end", values=(codigo_pedido, proveedor, producto, cantidad, fecha, estado))

        messagebox.showinfo("Pedido Registrado",
                            f"Pedido guardado correctamente.\nCódigo generado: {codigo_pedido}")

        for item in productos:
            self.pedido_table.delete(item)

    def crear_tab_generar_pedido(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Generar Pedido")

        # permitir expansión para la parte derecha (registro de pedidos)
        frame.grid_columnconfigure(3, weight=1)
        frame.grid_rowconfigure(6, weight=1)

        # --- Datos generales del pedido --- (izquierda)
        ttk.Label(frame, text="Proveedor:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.entry_proveedor_pedido = ttk.Entry(frame, width=30)
        self.entry_proveedor_pedido.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Fecha (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_fecha_pedido = ttk.Entry(frame, width=20)
        self.entry_fecha_pedido.grid(row=1, column=1, padx=10, pady=5)

        # --- Productos --- (izquierda)
        ttk.Label(frame, text="Producto:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.entry_producto_pedido = ttk.Entry(frame)
        self.entry_producto_pedido.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Cantidad:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_cantidad_pedido = ttk.Entry(frame)
        self.entry_cantidad_pedido.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Estado del Pedido:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.combo_estado = ttk.Combobox(frame, values=["Pendiente", "En Proceso", "Entregado", "Cancelado"], width=20, state="readonly")
        self.combo_estado.grid(row=4, column=1, padx=10, pady=5)
        self.combo_estado.current(0)

        ttk.Button(frame, text="Agregar Producto",
                command=self.agregar_producto_tabla).grid(row=5, column=1, pady=10)

        # --- Tabla de productos agregados (izquierda, debajo) ---
        columnas = ("producto", "cantidad")
        self.pedido_table = ttk.Treeview(frame, columns=columnas, show="headings", height=8)
        self.pedido_table.heading("producto", text="Producto")
        self.pedido_table.heading("cantidad", text="Cantidad")
        self.pedido_table.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Botón registrar pedido
        ttk.Button(frame, text="Registrar Pedido",
                command=self.registrar_pedido).grid(row=7, column=0, columnspan=2, pady=15)

        # --- Tabla registro de pedidos (DERECHA) con más columnas ---
        ttk.Label(frame, text="Registro de Pedidos").grid(row=0, column=3, padx=10, pady=10, sticky="w")
        

        columnas_registro = ("codigo", "proveedor", "producto", "cantidad", "fecha", "estado")
        self.tabla_registro_pedidos = ttk.Treeview(frame, columns=columnas_registro, show="headings", height=18)
        self.tabla_registro_pedidos.heading("codigo", text="Código")
        self.tabla_registro_pedidos.heading("proveedor", text="Proveedor")
        self.tabla_registro_pedidos.heading("producto", text="Producto")
        self.tabla_registro_pedidos.heading("cantidad", text="Cantidad")
        self.tabla_registro_pedidos.heading("fecha", text="Fecha")
        self.tabla_registro_pedidos.heading("estado", text="Estado")
        # ajustar anchos
        self.tabla_registro_pedidos.column("codigo", width=120, anchor="center")
        self.tabla_registro_pedidos.column("proveedor", width=180, anchor="w")
        self.tabla_registro_pedidos.column("producto", width=160, anchor="w")
        self.tabla_registro_pedidos.column("cantidad", width=90, anchor="center")
        self.tabla_registro_pedidos.column("fecha", width=110, anchor="center")
        self.tabla_registro_pedidos.column("estado", width=110, anchor="center")

        self.tabla_registro_pedidos.grid(row=1, column=3, rowspan=10, padx=10, pady=10, sticky="nsew")
        self.tabla_registro_pedidos.bind("<Double-1>", self.editar_pedido)
        # Cargar pedidos guardados en pedidos.db (una fila por item)
        try:
            self.ped_cursor.execute("""
                SELECT p.codigo_pedido, p.proveedor, i.producto, i.cantidad, p.fecha, p.estado
                FROM pedidos p
                JOIN pedido_items i ON p.codigo_pedido = i.codigo_pedido
                ORDER BY p.fecha DESC, p.codigo_pedido DESC
            """)
            for row in self.ped_cursor.fetchall():
                self.tabla_registro_pedidos.insert("", "end", values=row)
        except Exception:
            pass
    def editar_pedido(self, event):
        item_id = self.tabla_registro_pedidos.focus()
        if not item_id:
            return

        codigo, proveedor, producto, cantidad, fecha, estado = self.tabla_registro_pedidos.item(item_id, "values")

        ventana = tk.Toplevel()
        ventana.title(f"Editar Pedido {codigo}")
        ventana.grab_set()

        ttk.Label(ventana, text="Proveedor:").grid(row=0, column=0, padx=10, pady=5)
        entry_proveedor = ttk.Entry(ventana, width=30)
        entry_proveedor.insert(0, proveedor)
        entry_proveedor.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(ventana, text="Producto:").grid(row=1, column=0, padx=10, pady=5)
        entry_producto = ttk.Entry(ventana, width=30)
        entry_producto.insert(0, producto)
        entry_producto.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(ventana, text="Cantidad:").grid(row=2, column=0, padx=10, pady=5)
        entry_cantidad = ttk.Entry(ventana, width=15)
        entry_cantidad.insert(0, cantidad)
        entry_cantidad.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(ventana, text="Fecha (YYYY-MM-DD):").grid(row=3, column=0, padx=10, pady=5)
        entry_fecha = ttk.Entry(ventana, width=15)
        entry_fecha.insert(0, fecha)
        entry_fecha.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(ventana, text="Estado:").grid(row=4, column=0, padx=10, pady=5)
        combo_estado = ttk.Combobox(
            ventana,
            values=["Pendiente", "En Proceso", "Entregado"],
            state="readonly"
        )
        combo_estado.set(estado if estado != "Cancelado" else "Pendiente")
        combo_estado.grid(row=4, column=1, padx=10, pady=5)

        def guardar_cambios():
            nuevo_proveedor = entry_proveedor.get().strip()
            nuevo_producto = entry_producto.get().strip()
            nueva_cantidad = entry_cantidad.get().strip()
            nueva_fecha = entry_fecha.get().strip()
            nuevo_estado = combo_estado.get().strip()

            if not nuevo_proveedor or not nuevo_producto or not nueva_cantidad.isdigit():
                messagebox.showerror("Error", "Datos inválidos.")
                return

            try:
                datetime.strptime(nueva_fecha, "%Y-%m-%d")
            except:
                messagebox.showerror("Error", "Fecha inválida.")
                return

            try:
                # --- Solo actualizamos campos generales en pedidos ---
                self.ped_cursor.execute("""
                    UPDATE pedidos SET proveedor=?, fecha=?, estado=?
                    WHERE codigo_pedido=?
                """, (nuevo_proveedor, nueva_fecha, nuevo_estado, codigo))

                # --- Actualizamos solo este item en pedido_items ---
                self.ped_cursor.execute("""
                    UPDATE pedido_items SET producto=?, cantidad=?
                    WHERE codigo_pedido=? AND producto=? AND cantidad=?
                """, (nuevo_producto, int(nueva_cantidad), codigo, producto, cantidad))

                self.ped_con.commit()

                # --- Actualizamos visualmente solo la fila seleccionada ---
                self.tabla_registro_pedidos.item(item_id, values=(
                    codigo, nuevo_proveedor, nuevo_producto, nueva_cantidad, nueva_fecha, nuevo_estado
                ))

                messagebox.showinfo("Éxito", "Pedido actualizado correctamente.")
                ventana.destroy()

            except Exception as e:
                messagebox.showerror("Error BD", f"No se pudo actualizar:\n{e}")

        ttk.Button(ventana, text="Guardar Cambios", command=guardar_cambios).grid(
            row=5, column=0, columnspan=2, pady=15
        )

    def crear_tab_cancelar_pedido(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Cancelar Pedido")
        
        # --- Filtros de búsqueda ---
        ttk.Label(frame, text="Proveedor:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.combo_filtro_proveedor = ttk.Combobox(frame, values=[], width=30, state="readonly")
        self.combo_filtro_proveedor.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Producto:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.combo_filtro_producto = ttk.Combobox(frame, values=[], width=30, state="readonly")
        self.combo_filtro_producto.grid(row=1, column=1, padx=10, pady=5)

        ttk.Button(frame, text="Filtrar Pedidos", command=self.filtrar_pedidos_cancelar).grid(
            row=2, column=0, columnspan=2, pady=10
        )

        # --- Tabla de pedidos filtrados ---
        columnas = ("codigo", "proveedor", "producto", "cantidad", "fecha", "estado")
        self.tabla_cancelar_pedidos = ttk.Treeview(frame, columns=columnas, show="headings", height=15)
        for col, texto in zip(columnas, ["Código", "Proveedor", "Producto", "Cantidad", "Fecha", "Estado"]):
            self.tabla_cancelar_pedidos.heading(col, text=texto)
            self.tabla_cancelar_pedidos.column(col, width=100, anchor="center")
        self.tabla_cancelar_pedidos.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Botón para cancelar pedido
        ttk.Button(frame, text="Cancelar Pedido", command=self.cancelar_pedido_seleccionado).grid(
            row=4, column=0, columnspan=2, pady=15
        )

        # --- Cargar valores iniciales para los filtros ---
        self.actualizar_filtros_cancelar()

    # ---------------------------------------------
    # Función para actualizar los valores de los filtros
    # ---------------------------------------------
    def actualizar_filtros_cancelar(self):
        try:
            # Proveedores únicos
            self.ped_cursor.execute("SELECT DISTINCT proveedor FROM pedidos")
            proveedores = [row[0] for row in self.ped_cursor.fetchall()]
            self.combo_filtro_proveedor['values'] = ["Todos"] + proveedores
            self.combo_filtro_proveedor.current(0)

            # Inicialmente productos vacíos
            self.combo_filtro_producto['values'] = ["Todos"]
            self.combo_filtro_producto.current(0)

            # Conectar evento de cambio de proveedor
            self.combo_filtro_proveedor.bind("<<ComboboxSelected>>", self.actualizar_productos_por_proveedor)

        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudieron cargar filtros:\n{e}")

    def actualizar_productos_por_proveedor(self, event=None):
        proveedor = self.combo_filtro_proveedor.get()
        try:
            if proveedor == "Todos":
                self.ped_cursor.execute("SELECT DISTINCT producto FROM pedido_items")
            else:
                # Solo productos del proveedor seleccionado
                self.ped_cursor.execute("""
                    SELECT DISTINCT i.producto
                    FROM pedido_items i
                    JOIN pedidos p ON i.codigo_pedido = p.codigo_pedido
                    WHERE p.proveedor = ?
                """, (proveedor,))
            productos = [row[0] for row in self.ped_cursor.fetchall()]
            self.combo_filtro_producto['values'] = ["Todos"] + productos
            self.combo_filtro_producto.current(0)
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudieron cargar productos:\n{e}")

    # ---------------------------------------------
    # Función para filtrar la tabla según selección
    # ---------------------------------------------
    def filtrar_pedidos_cancelar(self):
        proveedor = self.combo_filtro_proveedor.get().strip()
        producto = self.combo_filtro_producto.get().strip()

        query = """
            SELECT p.codigo_pedido, p.proveedor, i.producto, i.cantidad, p.fecha, p.estado
            FROM pedidos p
            JOIN pedido_items i ON p.codigo_pedido = i.codigo_pedido
            WHERE 1=1
        """
        params = []

        if proveedor != "":
            query += " AND p.proveedor = ?"
            params.append(proveedor)

        if producto != "":
            query += " AND i.producto = ?"
            params.append(producto)

        query += " ORDER BY p.fecha DESC, p.codigo_pedido DESC"

        # Limpiar tabla
        for row in self.tabla_cancelar_pedidos.get_children():
            self.tabla_cancelar_pedidos.delete(row)

        try:
            self.ped_cursor.execute(query, params)
            rows = self.ped_cursor.fetchall()

            if not rows:
                messagebox.showinfo("Sin resultados", "No se encontraron pedidos con esos filtros.")

            for row in rows:
                self.tabla_cancelar_pedidos.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudieron filtrar pedidos:\n{e}")

    # ---------------------------------------------
    # Función para cancelar pedido seleccionado
    # ---------------------------------------------
    def cancelar_pedido_seleccionado(self):
        item_id = self.tabla_cancelar_pedidos.focus()
        if not item_id:
            messagebox.showwarning("Seleccionar Pedido", "Seleccione un pedido para cancelar.")
            return

        codigo, proveedor, producto, cantidad, fecha, estado = self.tabla_cancelar_pedidos.item(item_id, "values")

        if estado == "Cancelado":
            messagebox.showinfo("Pedido ya cancelado", "Este pedido ya se encuentra cancelado.")
            return

        # Confirmación
        if not messagebox.askyesno("Confirmar Cancelación", f"¿Desea cancelar el pedido {codigo}?"):
            return

        try:
            # Actualizar base de datos
            self.ped_cursor.execute("UPDATE pedidos SET estado = 'Cancelado' WHERE codigo_pedido = ?", (codigo,))
            self.ped_con.commit()

            # Actualizar visualmente la tabla
            self.tabla_cancelar_pedidos.item(item_id, values=(codigo, proveedor, producto, cantidad, fecha, "Cancelado"))

            # Opcional: actualizar también la tabla principal de registro de pedidos
            for row_id in self.tabla_registro_pedidos.get_children():
                if self.tabla_registro_pedidos.item(row_id, "values")[0] == codigo:
                    self.tabla_registro_pedidos.item(row_id, values=(codigo, proveedor, producto, cantidad, fecha, "Cancelado"))

            messagebox.showinfo("Pedido Cancelado", f"El pedido {codigo} ha sido cancelado.")

        except Exception as e:
            messagebox.showerror("Error BD", f"No se pudo cancelar el pedido:\n{e}")


        
    def crear_tab_retenciones(self):
        frame_retenciones = ttk.Frame(self.notebook)
        frame_retenciones.grid_rowconfigure(1, weight=1)
        frame_retenciones.grid_columnconfigure(0, weight=1)
        self.notebook.add(frame_retenciones, text="Retenciones")
        
        ttk.Label(frame_retenciones, text="Filtrar por año:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.year = ttk.Combobox(frame_retenciones, state="readonly",
        values=[2020, 2021, 2022, 2023, 2024, 2025])
        self.year.grid(row=0, column=0, padx=100, pady=10, sticky="w")
        
        ttk.Label(frame_retenciones, text="Filtrar por mes:").grid(row=0, column=0, padx=250, pady=10, sticky="w")
        self.mes = ttk.Combobox(frame_retenciones, state="readonly",
        values=["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        self.mes.grid(row=0, column=0, padx=350, pady=10, sticky="w")
        
        ttk.Button(frame_retenciones, text="Aplicar", command=self.filtrar_retenciones).grid(row=0, column=0, padx=500, sticky='w', pady=0)

        ttk.Label(frame_retenciones, text="Estado = ").grid(row=0, column=0, padx=575, pady=10, sticky="w")
        self.lbl_resultado_estado = ttk.Label(frame_retenciones, text="?")
        self.lbl_resultado_estado.grid(row=0, column=0, padx=625, pady=10, sticky="w")

        columns = ("id", "proveedor", "subtotal", "retencion", "total")
        self.retenciones_table = ttk.Treeview(frame_retenciones, columns=columns, show="headings")
        self.retenciones_table.heading("id", text="ID")
        self.retenciones_table.heading("proveedor", text="Proveedor")
        self.retenciones_table.heading("subtotal", text="Subtotal")
        self.retenciones_table.heading("retencion", text="Retención")
        self.retenciones_table.heading("total", text="Total")
        self.retenciones_table.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        frame_botones = ttk.Frame(frame_retenciones)
        frame_botones.grid(row=4, column=0, columnspan=4, pady=10)
        ttk.Button(frame_retenciones, text="Calcular Retenciones", command=self.calcular_ret).grid(row=4, column=0, padx=10, sticky='w', pady=0)


        frame_label_retenciones = ttk.Frame(frame_retenciones)
        frame_label_retenciones.grid(row=4, column=1, columnspan=4, pady=10)
        ttk.Label(frame_retenciones, text="Retención total").grid(row=5, column=0, padx=10, sticky='w', pady=0)

        self.lbl_resultado = ttk.Label(frame_retenciones, text="$ 0.00",  background="#e0e0e0", foreground="#000000")
        self.lbl_resultado.grid(row=5, column=0, padx=100, pady=0, sticky='w')

        self.boton_pagar = ttk.Button(frame_retenciones, text="Pagar", command=self.pagar_retencion)
        self.boton_pagar.grid(row=5, column=0, padx=155, sticky='w', pady=0)
        self.boton_pagar.grid_remove()
   
    def cargar_facturas(self):
        # Selecciona las columnas en el mismo orden que las columnas de la Treeview 'productos_table'
        self.cursor.execute("""
            SELECT proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_factura, codigo_pedido, subtotal, total, id
            FROM facturas
        """)
        rows = self.cursor.fetchall()
        # Para la tabla de productos usamos sólo las primeras 11 columnas (las que mostró el Treeview)
        # retornamos también valores auxiliares para otras vistas cuando sea necesario
        # orden de retorno: (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_factura, codigo_pedido, subtotal, total, id)
        return rows

    def filtrar_retenciones(self):
        self.lbl_resultado.config(text="$ 0.00")
        year = self.year.get()
        mes = self.mes.current() + 1  # Mes actual (1-12)
        for item in self.retenciones_table.get_children():
            self.retenciones_table.delete(item)
        facturas = self.cargar_facturas()
        estado = self.cursor.execute("SELECT estado FROM estadoRetenciones WHERE year = ? AND month = ?", (year, mes)).fetchone()
        if estado == (1,):
            self.lbl_resultado_estado.config(text="PAGADO", foreground="green")
            self.boton_pagar.grid_remove()
        else:
            self.lbl_resultado_estado.config(text="PENDIENTE", foreground="red")
            self.boton_pagar.grid()
        
        for f in facturas:
            fecha_factura = datetime.strptime(f[1], "%Y-%m-%d")
            if (not year or fecha_factura.year == int(year)) and (not mes or fecha_factura.month == mes):
                filas = (f[13], f[0], f[11], f[7], f[12])  # id, proveedor, subtotal, retencion, total
                self.retenciones_table.insert("", "end", values=filas)

    def calcular_ret(self):
        year = self.year.get()
        mes = self.mes.current() + 1  # Mes actual (1-12)
        ret_mes = 0
        facturas = self.cargar_facturas()
        for f in facturas:
            fecha_factura = datetime.strptime(f[1], "%Y-%m-%d")
            if (not year or fecha_factura.year == int(year)) and (not mes or fecha_factura.month == mes):
                ret_mes += f[11]*f[7]/100  # subtotal * (retencion / 100)
        self.lbl_resultado.config(text=f"$ {ret_mes:.2f}")

    def pagar_retencion(self):
        year = self.year.get()
        mes = self.mes.current() + 1  # Mes actual (1-12)
        try:
            self.cursor.execute("INSERT OR REPLACE INTO estadoRetenciones (year, month, estado) VALUES (?, ?, ?)", (year, mes, 1))
            self.con.commit()
            messagebox.showinfo("Listo", "Retención marcada como pagada.")
            self.filtrar_retenciones()
        except:
            messagebox.showerror("Error", "No se pudo actualizar el estado de la retención.")


if __name__ == "__main__":
    root = tk.Tk()
    LoginApp(root)
    root.mainloop()
