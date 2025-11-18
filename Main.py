import sqlite3
import tkinter as tk
from tkinter import ttk
from pathlib import Path


class SistemaContableApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Contable - Empresa Lechera")
        self.root.geometry("1200x800")
        
        DB_PATH = Path(__file__).with_name("contabilidad_lechera.db")
        print("DB cargada desde:", DB_PATH)
        self.con = sqlite3.connect(DB_PATH)
        self.cursor = self.con.cursor()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        self.crear_tab_factura()
        self.crear_tab_analisis()
        self.crear_tab_gastos_mes()
        self.crear_tab_pedidos()
        self.crear_tab_retenciones()




    # -------------------------
    # TAB: Registrar Facturas
    # -------------------------
    def crear_tab_factura(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Registrar Factura")

        ttk.Label(frame, text="Proveedor:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_proveedor = ttk.Entry(frame)
        self.entry_proveedor.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Fecha (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5)
        self.entry_fecha = ttk.Entry(frame)
        self.entry_fecha.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Producto:").grid(row=2, column=0, padx=10, pady=5)
        self.entry_producto = ttk.Entry(frame)
        self.entry_producto.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Cantidad:").grid(row=3, column=0, padx=10, pady=5)
        self.entry_cantidad = ttk.Entry(frame)
        self.entry_cantidad.grid(row=3, column=1, padx=10, pady=5)

        ttk.Button(frame, text="Agregar Producto").grid(row=4, column=1, padx=10, pady=10)

        columns = ("producto", "cantidad")
        self.productos_table = ttk.Treeview(frame, columns=columns, show="headings")
        self.productos_table.heading("producto", text="Producto")
        self.productos_table.heading("cantidad", text="Cantidad")
        self.productos_table.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

    # -------------------------
    # TAB: Análisis
    # -------------------------
    def crear_tab_analisis(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Análisis de Gastos")

        ttk.Label(frame, text="Herramientas de análisis (Placeholder)").pack(pady=20)

    # -------------------------
    # TAB: Gastos del Mes
    # -------------------------
    def crear_tab_gastos_mes(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Gastos del Mes")

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
        
        columns = ("id", "proveedor", "subtotal", "retencion", "total")
        self.retenciones_table = ttk.Treeview(frame_retenciones, columns=columns, show="headings")
        self.retenciones_table.heading("id", text="ID")
        self.retenciones_table.heading("proveedor", text="Proveedor")
        self.retenciones_table.heading("subtotal", text="Subtotal")
        self.retenciones_table.heading("retencion", text="Retención")
        self.retenciones_table.heading("total", text="Total")
        self.retenciones_table.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

        frame_botones = ttk.Frame(frame_retenciones)
        frame_botones.grid(row=4, column=0, columnspan=4, pady=10)
        ttk.Button(frame_retenciones, text="Calcular Retenciones", command=self.calcular_ret).grid(row=1, column=0, padx=10, sticky='w', pady=0)
        facturas = self.cargar_facturas()
        for f in facturas:
            self.retenciones_table.insert("", "end", values=f)

        frame_label_retenciones = ttk.Frame(frame_retenciones)
        frame_label_retenciones.grid(row=5, column=0, columnspan=4, pady=10)
        ttk.Label(frame_retenciones, text="Retención total").grid(row=2, column=0, padx=10, sticky='w', pady=0)

        self.lbl_resultado = ttk.Label(frame_retenciones, text="0",  background="#e0e0e0", foreground="#000000")
        self.lbl_resultado.grid(row=4, column=0, padx=10, pady=0, sticky='w')
        #self.lbl_resultado.config(text=str("aaaaaaaaaaaaaaaaaaaaaaaaaaa"))



        


    def cargar_facturas(self):
        self.cursor.execute("SELECT id, proveedor, subtotal, retencion, total FROM facturas")
        facturas = self.cursor.fetchall()
        return facturas
    
    def calcular_ret(self):
        facturas = self.cargar_facturas()
        total_retencion = sum(f[3] for f in facturas)
        self.lbl_resultado.config(text=str("$ "+str(total_retencion)))




root = tk.Tk()
app = SistemaContableApp(root)
root.mainloop()
