import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).with_name("contabilidad_lechera.db")

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("V.A.C.A - Login / Registro")
        try:
            root.iconbitmap("logo.ico")
        except:
            pass
        self.root.geometry("1100x720")

        # Conexión a BD
        self.con = sqlite3.connect(DB_PATH)
        self.cursor = self.con.cursor()
        self._ensure_tables()

        # Frames
        self.frame_login = ttk.Frame(self.root, padding=16)
        self.frame_register = ttk.Frame(self.root, padding=16)

        self.build_login_frame()
        self.build_register_frame()
        self.show_login()

    def _ensure_tables(self):
        # Tabla de usuarios
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                documento TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL,
                contrasena TEXT NOT NULL,
                rol TEXT NOT NULL
            )
        """)
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

    # ---------------- LOGIN ----------------
    def build_login_frame(self):
        frm = self.frame_login
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
        self.cursor.execute("INSERT INTO usuarios (documento, nombre, correo, contrasena, rol) VALUES (?, ?, ?, ?, ?)",
                            (doc, nombre, correo, pw1, rol))
        self.con.commit()
        messagebox.showinfo("Éxito", f"Usuario registrado como {rol}")
        self.show_login()

    def do_login(self):
        doc = self.e_doc.get().strip()
        pw = self.e_pw.get()
        if not doc or not pw:
            messagebox.showwarning("Faltan datos", "Documento y contraseña son obligatorios")
            return
        self.cursor.execute("SELECT documento, nombre, correo, contrasena, rol FROM usuarios WHERE documento = ?", (doc,))
        row = self.cursor.fetchone()
        if not row:
            messagebox.showerror("Error", "Documento no registrado")
            return
        if pw != row[3]:
            messagebox.showerror("Error", "Contraseña incorrecta")
            return
        usuario = {"documento": row[0], "nombre": row[1], "correo": row[2], "rol": row[4]}
        self.launch_system(usuario)

    def launch_system(self, usuario):
        for w in self.root.winfo_children():
            w.destroy()
        app = SistemaContableApp(self.root, db_connection=self.con, usuario=usuario, cursor=self.cursor)
        self.system_app = app

# -----------------
# Sistema Contable 
# -----------------
class SistemaContableApp:
    def __init__(self, root, db_connection, usuario, cursor):
        self.root = root
        self.con = db_connection
        self.cursor = cursor
        self.usuario = usuario
        self.root.title(f"V.A.C.A")
        try:
            root.iconbitmap("logo.ico")
        except:
            pass
        self.root.geometry("1100x720")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        rol = self.usuario.get("rol", "")
        if rol == "Auxiliar Contable":
            self.crear_tab_factura()
            self.generar_pedido()
        elif rol == "Contadora":
            self.crear_tab_analisis()
            self.crear_tab_revision_de_gastos()
            self.crear_tab_retenciones()

        self._create_top_bar()

    def _create_top_bar(self):
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, pady=6, padx=6)
        ttk.Label(top, text=f"Usuario: {self.usuario['nombre']}").pack(side=tk.LEFT, padx=(6,12))
        ttk.Label(top, text=f"Rol: {self.usuario['rol']}").pack(side=tk.LEFT)
        ttk.Button(top, text="Cerrar Sesión", command=self.do_logout).pack(side=tk.RIGHT)

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
        form_box.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,6))

        table_box = ttk.LabelFrame(frame, text="Productos en la Factura", padding=6)
        table_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)

        codes_box = ttk.LabelFrame(frame, text="Códigos y Acciones", padding=8)
        codes_box.grid(row=2, column=0, sticky="ew", padx=10, pady=(6,10))

        # permitir que la tabla crezca cuando la ventana cambie de tamaño
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
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
    
    # -------------------------
    # TAB: Análisis
    # -------------------------
    def crear_tab_analisis(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Análisis de Gastos")

        fb = ttk.LabelFrame(frame, text="Herramientas de análisis", padding=8)
        fb.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,6))

        ttk.Label(fb, text="Empresas:").grid(row=1, column=0, padx=10, pady=5)
        ttk.Button(fb, text="Evaluar").grid(row=3, column=0, padx=10, pady=5)

        ttk.Label(fb, text="General:").grid(row=1, column=1, padx=200, pady=5)
        ttk.Button(fb, text="Evaluar").grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(fb, text="Producto:").grid(row=1, column=2, padx=10, pady=5)
        ttk.Entry(fb).grid(row=2, column=2, padx=10, pady=5)
        ttk.Button(fb, text="Evaluar").grid(row=3, column=2, padx=10, pady=5)

        ttk.Label(fb).grid(row=4, column=2, padx=10, pady=5)
        ttk.Label(fb).grid(row=5, column=2, padx=10, pady=5)
        ttk.Label(fb).grid(row=6, column=2, padx=10, pady=5)
        
        r1 = ttk.Label(fb, text="R1,1").grid(row=10, column=0, padx=10, pady=5)
        r2 = ttk.Label(fb, text="R2,1").grid(row=11, column=0, padx=10, pady=5)
        r3 = ttk.Label(fb, text="R3,1").grid(row=12, column=0, padx=10, pady=5)
        r4 = ttk.Label(fb, text="R1,2").grid(row=10, column=1, padx=10, pady=5)
        r5 = ttk.Label(fb, text="R2,2").grid(row=11, column=1, padx=10, pady=5)
        r6 = ttk.Label(fb, text="R3,2").grid(row=12, column=1, padx=10, pady=5)
        r7 = ttk.Label(fb, text="R1,3").grid(row=10, column=2, padx=10, pady=5)
        r8 = ttk.Label(fb, text="R2,3").grid(row=11, column=2, padx=10, pady=5)
        r9 = ttk.Label(fb, text="R3,3").grid(row=12, column=2, padx=10, pady=5)
        
    def crear_tab_revision_de_gastos(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Revisión de Gastos Mensuales")

        ttk.Label(frame, text="Consulta rápida de gastos mensuales (Placeholder)").pack(pady=20)

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
        proveedor = self.entry_proveedor_pedido.get()
        fecha = self.entry_fecha_pedido.get()
        estado = self.combo_estado.get()
        productos = self.pedido_table.get_children()

        if not proveedor or not fecha or not productos:
            messagebox.showerror("Error", "Todos los campos y al menos un producto son obligatorios.")
            return

        codigo_pedido = "PED-" + datetime.now().strftime("%Y%m%d%H%M%S")

        # Insertar cada producto del pedido al registro
        for item in productos:
            producto, cantidad = self.pedido_table.item(item, "values")
            self.tabla_registro_pedidos.insert("", "end", values=(codigo_pedido, producto, cantidad))

        messagebox.showinfo("Pedido Registrado",
                            f"Pedido guardado correctamente.\nCódigo generado: {codigo_pedido}")

        # Limpiar la tabla de productos para un nuevo pedido
        for item in productos:
            self.pedido_table.delete(item)

    def generar_pedido(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Generar Pedido")

        # --- Datos generales del pedido ---
        ttk.Label(frame, text="Proveedor:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.entry_proveedor_pedido = ttk.Entry(frame, width=30)
        self.entry_proveedor_pedido.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Fecha (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_fecha_pedido = ttk.Entry(frame, width=20)
        self.entry_fecha_pedido.grid(row=1, column=1, padx=10, pady=5)

        # --- Productos ---
        ttk.Label(frame, text="Producto:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.entry_producto_pedido = ttk.Entry(frame)
        self.entry_producto_pedido.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Cantidad:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_cantidad_pedido = ttk.Entry(frame)
        self.entry_cantidad_pedido.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Estado del Pedido:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.combo_estado = ttk.Combobox(frame, values=["Pendiente", "En Proceso", "Entregado", "Cancelado"], width=20)
        self.combo_estado.grid(row=4, column=1, padx=10, pady=5)
        self.combo_estado.current(0)

        ttk.Button(frame, text="Agregar Producto",
                command=self.agregar_producto_tabla).grid(row=5, column=1, pady=10)

        # --- Tabla de productos agregados (izquierda) ---
        columnas = ("producto", "cantidad")
        self.pedido_table = ttk.Treeview(frame, columns=columnas, show="headings", height=8)
        self.pedido_table.heading("producto", text="Producto")
        self.pedido_table.heading("cantidad", text="Cantidad")
        self.pedido_table.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

        # Botón registrar pedido
        ttk.Button(frame, text="Registrar Pedido",
                command=self.registrar_pedido).grid(row=7, column=0, columnspan=2, pady=15)

        # --- Tabla registro de pedidos (DERECHA) ---
        ttk.Label(frame, text="Registro de Pedidos").grid(row=0, column=3, padx=10, pady=10)

        columnas_registro = ("codigo", "producto", "cantidad")
        self.tabla_registro_pedidos = ttk.Treeview(frame, columns=columnas_registro, show="headings", height=18)
        self.tabla_registro_pedidos.heading("codigo", text="Código")
        self.tabla_registro_pedidos.heading("producto", text="Producto")
        self.tabla_registro_pedidos.heading("cantidad", text="Cantidad")
        self.tabla_registro_pedidos.grid(row=1, column=3, rowspan=10, padx=10, pady=10, sticky="n")

    def crear_tab_retenciones(self):
        frame_retenciones = ttk.Frame(self.notebook)
        self.notebook.add(frame_retenciones, text="Retenciones")
        
        ttk.Label(frame_retenciones, text="Filtrar por Mes:").grid(row=0, column=0, padx=10, pady=10)
        self.mes = ttk.Combobox(frame_retenciones, state="readonly",
        values=["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])#.grid(row=0, column=1, padx=0, pady=10)
        self.mes.grid(row=0, column=1, padx=10, pady=10)
        self.mes.bind("<<ComboboxSelected>>", self.filtrar_por_mes)
        self.mes_Nro = self.mes.current() + 1  # Mes actual (1-12)
        


        columns = ("id", "proveedor", "subtotal", "retencion", "total")
        self.retenciones_table = ttk.Treeview(frame_retenciones, columns=columns, show="headings")
        self.retenciones_table.heading("id", text="ID")
        self.retenciones_table.heading("proveedor", text="Proveedor")
        self.retenciones_table.heading("subtotal", text="Subtotal")
        self.retenciones_table.heading("retencion", text="Retención")
        self.retenciones_table.heading("total", text="Total")
        self.retenciones_table.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

        frame_botones = ttk.Frame(frame_retenciones)
        frame_botones.grid(row=4, column=0, columnspan=4, pady=10)
        ttk.Button(frame_retenciones, text="Calcular Retenciones", command=self.calcular_ret).grid(row=4, column=0, padx=10, sticky='w', pady=0)


        frame_label_retenciones = ttk.Frame(frame_retenciones)
        frame_label_retenciones.grid(row=4, column=1, columnspan=4, pady=10)
        ttk.Label(frame_retenciones, text="Retención total").grid(row=5, column=0, padx=10, sticky='w', pady=0)

        self.lbl_resultado = ttk.Label(frame_retenciones, text="0",  background="#e0e0e0", foreground="#000000")
        self.lbl_resultado.grid(row=5, column=0, padx=100, pady=0, sticky='w')
   
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
    
    def calcular_ret(self):
        facturas = self.cargar_facturas()
        mes_seleccionado = self.mes_Nro # Obtener el índice del mes seleccionado (0-11) y convertir a 1-12
        retenciones_mes = 0
        for f in facturas:
            fecha_factura = datetime.strptime(f[1], "%Y-%m-%d")    
            if fecha_factura.month == mes_seleccionado:
                retenciones_mes += f[7]
        self.lbl_resultado.config(text=str("$ "+str(retenciones_mes)))
    
    def filtrar_por_mes(self, event):
        mes_seleccionado = event.widget.current() + 1  # Obtener el índice del mes seleccionado (0-11) y convertir a 1-12

        # Limpiar la tabla antes de agregar los nuevos datos
        for item in self.retenciones_table.get_children():
            self.retenciones_table.delete(item)

        facturas = self.cargar_facturas()
        for f in facturas:
            fecha_factura = datetime.strptime(f[1], "%Y-%m-%d")
            if fecha_factura.month == mes_seleccionado:
                filas = (f[13], f[0], f[11], f[7], f[12])  # id, proveedor, subtotal, retencion, total
                self.retenciones_table.insert("", "end", values=filas)
        self.mes_Nro = self.mes.current() + 1  # Mes actual (1-12)

if __name__ == "__main__":
    root = tk.Tk()
    LoginApp(root)
    root.mainloop()


