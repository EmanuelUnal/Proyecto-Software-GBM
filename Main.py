import tkinter as tk
from tkinter import ttk

# Main application window
root = tk.Tk()
root.title("Sistema Contable - Empresa Lechera")
root.geometry("900x600")

# Notebook for tabs
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# -----------------
# TAB 1: Registrar Factura de Insumos
# -----------------
frame_factura = ttk.Frame(notebook)
notebook.add(frame_factura, text="Registrar Factura")

ttk.Label(frame_factura, text="Proveedor:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
entry_proveedor = ttk.Entry(frame_factura)
entry_proveedor.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(frame_factura, text="Fecha (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
entry_fecha = ttk.Entry(frame_factura)
entry_fecha.grid(row=1, column=1, padx=10, pady=5)

# Productos y cantidades (simple table-like grid)
ttk.Label(frame_factura, text="Producto:").grid(row=2, column=0, padx=10, pady=5)
entry_producto = ttk.Entry(frame_factura)
entry_producto.grid(row=2, column=1, padx=10, pady=5)

ttk.Label(frame_factura, text="Cantidad:").grid(row=3, column=0, padx=10, pady=5)
entry_cantidad = ttk.Entry(frame_factura)
entry_cantidad.grid(row=3, column=1, padx=10, pady=5)

btn_agregar_producto = ttk.Button(frame_factura, text="Agregar Producto")
btn_agregar_producto.grid(row=4, column=1, padx=10, pady=10, sticky="e")

# Table for the list of products
columns = ("producto", "cantidad")
productos_table = ttk.Treeview(frame_factura, columns=columns, show='headings')
productos_table.heading("producto", text="Producto")
productos_table.heading("cantidad", text="Cantidad")
productos_table.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

# -----------------
# TAB 2: Análisis de Gastos
# -----------------
frame_analisis = ttk.Frame(notebook)
notebook.add(frame_analisis, text="Análisis de Gastos")

ttk.Label(frame_analisis, text="Herramientas de análisis (Placeholder)", font=("Arial", 12)).pack(pady=20)

# -----------------
# TAB 3: Gastos del Mes
# -----------------
frame_gastos_mes = ttk.Frame(notebook)
notebook.add(frame_gastos_mes, text="Gastos del Mes")

ttk.Label(frame_gastos_mes, text="Consulta rápida de gastos mensuales (Placeholder)", font=("Arial", 12)).pack(pady=20)

# -----------------
# TAB 4: Registrar Pedido de Insumos
# -----------------
frame_pedido = ttk.Frame(notebook)
notebook.add(frame_pedido, text="Registrar Pedido")

ttk.Label(frame_pedido, text="Proveedor:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
entry_proveedor_pedido = ttk.Entry(frame_pedido)
entry_proveedor_pedido.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(frame_pedido, text="Fecha (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
entry_fecha_pedido = ttk.Entry(frame_pedido)
entry_fecha_pedido.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(frame_pedido, text="Producto:").grid(row=2, column=0, padx=10, pady=5)
entry_producto_pedido = ttk.Entry(frame_pedido)
entry_producto_pedido.grid(row=2, column=1, padx=10, pady=5)

ttk.Label(frame_pedido, text="Cantidad:").grid(row=3, column=0, padx=10, pady=5)
entry_cantidad_pedido = ttk.Entry(frame_pedido)
entry_cantidad_pedido.grid(row=3, column=1, padx=10, pady=5)

ttk.Label(frame_pedido, text="Estado del Pedido:").grid(row=4, column=0, padx=10, pady=5)
combo_estado = ttk.Combobox(frame_pedido, values=["Pendiente", "En Proceso", "Entregado", "Cancelado"])
combo_estado.grid(row=4, column=1, padx=10, pady=5)

btn_agregar_pedido = ttk.Button(frame_pedido, text="Agregar Producto al Pedido")
btn_agregar_pedido.grid(row=5, column=1, padx=10, pady=10, sticky="e")

pedido_columns = ("producto", "cantidad", "estado")
pedido_table = ttk.Treeview(frame_pedido, columns=pedido_columns, show="headings")
pedido_table.heading("producto", text="Producto")
pedido_table.heading("cantidad", text="Cantidad")
pedido_table.heading("estado", text="Estado")
pedido_table.grid(row=6, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

# Start the application
root.mainloop()
