import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from pathlib import Path
from datetime import datetime


class SistemaContableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("V.A.C.A")
        root.iconbitmap("logo.ico")
        self.root.geometry("1200x800")
        
        DB_PATH = Path(__file__).with_name("contabilidad_lechera.db")
        self.con = sqlite3.connect(DB_PATH)
        self.cursor = self.con.cursor()

        # Asegurar que la tabla existe (si no, crearla)
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

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        self.crear_tab_factura()
        self.crear_tab_analisis()
        self.crear_tab_revision_de_gastos()
        self.crear_tab_pedidos()
        self.crear_tab_retenciones()

    # -------------------------
    # TAB: Registrar Facturas
    # -------------------------
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
        
        
        #self.tipo_producto = ttk.Entry(fb, text = "General")
        #self.tipo_producto.grid(row=1, column=1, padx=10, pady=5)
        #ttk.Label(fb, text="(Vacío para la información general)").grid(row=2, column=0, padx=10, pady=0)


    # -------------------------
    # TAB: Gastos del Mes
    # -------------------------
    def crear_tab_revision_de_gastos(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Revisión de Gastos Mensuales")

        ttk.Label(frame, text="Consulta rápida de gastos mensuales (Placeholder)").pack(pady=20)

    # -------------------------
    # TAB: Registrar Pedidos
    # -------------------------
    def crear_tab_pedidos(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Registrar Pedido")

        ttk.Label(frame, text="Proveedor:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_proveedor_pedido = ttk.Entry(frame)
        self.entry_proveedor_pedido.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Fecha (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
        self.entry_fecha_pedido = ttk.Entry(frame)
        self.entry_fecha_pedido.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Producto:").grid(row=2, column=0, padx=10, pady=5)
        self.entry_producto_pedido = ttk.Entry(frame)
        self.entry_producto_pedido.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Cantidad:").grid(row=3, column=0, padx=10, pady=5)
        self.entry_cantidad_pedido = ttk.Entry(frame)
        self.entry_cantidad_pedido.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Estado del Pedido:").grid(row=4, column=0, padx=10, pady=5)
        self.combo_estado = ttk.Combobox(frame, values=["Pendiente", "En Proceso", "Entregado", "Cancelado"])
        self.combo_estado.grid(row=4, column=1, padx=10, pady=5)

        ttk.Button(frame, text="Agregar Producto al Pedido").grid(row=5, column=1, padx=10, pady=10)

        columns = ("producto", "cantidad", "estado")
        self.pedido_table = ttk.Treeview(frame, columns=columns, show="headings")
        self.pedido_table.heading("producto", text="Producto")
        self.pedido_table.heading("cantidad", text="Cantidad")
        self.pedido_table.heading("estado", text="Estado")
        self.pedido_table.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

    # -------------------------
    # TAB: Retenciones
    # -------------------------
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




root = tk.Tk()
app = SistemaContableApp(root)
root.mainloop()
