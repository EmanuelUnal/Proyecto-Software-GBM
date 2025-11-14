import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

class SistemaContabilidadLechera:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Contabilidad - Empresa Lechera")
        self.root.geometry("1000x700")
        
        # Inicializar base de datos
        self.inicializar_bd()
        
        # Crear notebook (pestañas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Crear pestañas
        self.crear_pestana_facturas()
        self.crear_pestana_pedidos()
        self.crear_pestana_analisis()
        self.crear_pestana_consultas()
        
    def inicializar_bd(self):
        """Inicializa la base de datos con tablas y datos de ejemplo"""
        self.conn = sqlite3.connect('contabilidad_lechera.db')
        self.cursor = self.conn.cursor()
        
        # Crear tabla de facturas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS facturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor TEXT NOT NULL,
                fecha TEXT NOT NULL,
                categoria TEXT NOT NULL,
                producto TEXT NOT NULL,
                cantidad REAL NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                retencion REAL NOT NULL,
                total REAL NOT NULL
            )
        ''')
        
        # Crear tabla de pedidos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor TEXT NOT NULL,
                fecha_pedido TEXT NOT NULL,
                fecha_entrega TEXT,
                categoria TEXT NOT NULL,
                producto TEXT NOT NULL,
                cantidad REAL NOT NULL,
                estado TEXT NOT NULL
            )
        ''')
        
        # Insertar datos de ejemplo si la tabla está vacía
        self.cursor.execute('SELECT COUNT(*) FROM facturas')
        if self.cursor.fetchone()[0] == 0:
            self.insertar_datos_ejemplo()
        
        self.conn.commit()
    
    def insertar_datos_ejemplo(self):
        """Inserta datos de ejemplo en la base de datos"""
        proveedores = {
            'Jornales': ['Juan Pérez', 'María López', 'Carlos Gómez'],
            'Agroquímicos': ['AgroSuministros Ltda', 'QuimicoAgro SA'],
            'Concentrado': ['Nutrigran SA', 'AlimentoGanado Ltda'],
            'Dotaciones': ['Uniformes del Campo', 'Seguridad Industrial SA'],
            'Maquinaria': ['TecnoAgro SA', 'Maquinaria del Valle']
        }
        
        productos = {
            'Jornales': ['Ordeño', 'Alimentación', 'Limpieza', 'Mantenimiento'],
            'Agroquímicos': ['Herbicida', 'Fertilizante', 'Insecticida'],
            'Concentrado': ['Concentrado Premium', 'Suplemento Mineral', 'Sal mineralizada'],
            'Dotaciones': ['Botas', 'Guantes', 'Overol', 'Delantal'],
            'Maquinaria': ['Bomba de agua', 'Ordeñadora', 'Tanque enfriador']
        }
        
        # Generar facturas de los últimos 3 meses
        facturas_ejemplo = []
        for i in range(50):
            categoria = random.choice(list(proveedores.keys()))
            proveedor = random.choice(proveedores[categoria])
            producto = random.choice(productos[categoria])
            fecha = (datetime.now() - timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d')
            cantidad = random.randint(1, 20)
            
            # Precios según categoría
            precios = {
                'Jornales': random.randint(40000, 60000),
                'Agroquímicos': random.randint(50000, 200000),
                'Concentrado': random.randint(80000, 150000),
                'Dotaciones': random.randint(30000, 80000),
                'Maquinaria': random.randint(500000, 2000000)
            }
            
            precio_unitario = precios[categoria]
            subtotal = cantidad * precio_unitario
            retencion = self.calcular_retencion(categoria, subtotal)
            total = subtotal - retencion
            
            facturas_ejemplo.append((proveedor, fecha, categoria, producto, cantidad, 
                                   precio_unitario, subtotal, retencion, total))
        
        self.cursor.executemany('''
            INSERT INTO facturas (proveedor, fecha, categoria, producto, cantidad,
                                precio_unitario, subtotal, retencion, total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', facturas_ejemplo)
        
        # Generar pedidos de ejemplo
        pedidos_ejemplo = []
        estados = ['Pendiente', 'En tránsito', 'Entregado', 'Cancelado']
        for i in range(20):
            categoria = random.choice(list(proveedores.keys()))
            proveedor = random.choice(proveedores[categoria])
            producto = random.choice(productos[categoria])
            fecha_pedido = (datetime.now() - timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
            fecha_entrega = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            cantidad = random.randint(1, 15)
            estado = random.choice(estados)
            
            pedidos_ejemplo.append((proveedor, fecha_pedido, fecha_entrega, categoria, 
                                  producto, cantidad, estado))
        
        self.cursor.executemany('''
            INSERT INTO pedidos (proveedor, fecha_pedido, fecha_entrega, categoria,
                               producto, cantidad, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', pedidos_ejemplo)
        
        self.conn.commit()
    
    def calcular_retencion(self, categoria, monto):
        """Calcula la retención según la categoría"""
        porcentajes = {
            'Jornales': 0.0,  # Sin retención
            'Agroquímicos': 0.025,  # 2.5%
            'Concentrado': 0.025,  # 2.5%
            'Dotaciones': 0.035,  # 3.5%
            'Maquinaria': 0.04  # 4%
        }
        return monto * porcentajes.get(categoria, 0.0)
    
    def crear_pestana_facturas(self):
        """Crea la pestaña para registrar facturas"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📄 Registrar Factura")
        
        # Frame para formulario
        form_frame = ttk.LabelFrame(frame, text="Nueva Factura de Insumos", padding=15)
        form_frame.pack(fill='x', padx=10, pady=10)
        
        # Proveedor
        ttk.Label(form_frame, text="Proveedor:").grid(row=0, column=0, sticky='w', pady=5)
        self.factura_proveedor = ttk.Entry(form_frame, width=30)
        self.factura_proveedor.grid(row=0, column=1, pady=5, padx=5)
        
        # Fecha
        ttk.Label(form_frame, text="Fecha:").grid(row=0, column=2, sticky='w', pady=5, padx=(20, 0))
        self.factura_fecha = ttk.Entry(form_frame, width=15)
        self.factura_fecha.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.factura_fecha.grid(row=0, column=3, pady=5, padx=5)
        
        # Categoría
        ttk.Label(form_frame, text="Categoría:").grid(row=1, column=0, sticky='w', pady=5)
        self.factura_categoria = ttk.Combobox(form_frame, width=28, values=[
            'Jornales', 'Agroquímicos', 'Concentrado', 'Dotaciones', 'Maquinaria'
        ])
        self.factura_categoria.grid(row=1, column=1, pady=5, padx=5)
        
        # Producto
        ttk.Label(form_frame, text="Producto:").grid(row=1, column=2, sticky='w', pady=5, padx=(20, 0))
        self.factura_producto = ttk.Entry(form_frame, width=30)
        self.factura_producto.grid(row=1, column=3, pady=5, padx=5)
        
        # Cantidad
        ttk.Label(form_frame, text="Cantidad:").grid(row=2, column=0, sticky='w', pady=5)
        self.factura_cantidad = ttk.Entry(form_frame, width=15)
        self.factura_cantidad.grid(row=2, column=1, pady=5, padx=5, sticky='w')
        
        # Precio unitario
        ttk.Label(form_frame, text="Precio Unit.:").grid(row=2, column=2, sticky='w', pady=5, padx=(20, 0))
        self.factura_precio = ttk.Entry(form_frame, width=15)
        self.factura_precio.grid(row=2, column=3, pady=5, padx=5, sticky='w')
        
        # Botones
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=15)
        
        ttk.Button(btn_frame, text="💾 Guardar Factura", command=self.guardar_factura).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Limpiar", command=self.limpiar_factura).pack(side='left', padx=5)
        
        # Información de retención
        self.info_retencion = ttk.Label(form_frame, text="", foreground='blue')
        self.info_retencion.grid(row=4, column=0, columnspan=4, pady=5)
        
        # Actualizar info de retención al cambiar categoría
        self.factura_categoria.bind('<<ComboboxSelected>>', self.actualizar_info_retencion)
    
    def actualizar_info_retencion(self, event=None):
        """Muestra información de retención según la categoría"""
        categoria = self.factura_categoria.get()
        porcentajes = {
            'Jornales': '0%',
            'Agroquímicos': '2.5%',
            'Concentrado': '2.5%',
            'Dotaciones': '3.5%',
            'Maquinaria': '4%'
        }
        if categoria in porcentajes:
            self.info_retencion.config(text=f"ℹ️ Retención aplicable: {porcentajes[categoria]}")
    
    def guardar_factura(self):
        """Guarda una nueva factura en la base de datos"""
        try:
            proveedor = self.factura_proveedor.get()
            fecha = self.factura_fecha.get()
            categoria = self.factura_categoria.get()
            producto = self.factura_producto.get()
            cantidad = float(self.factura_cantidad.get())
            precio_unitario = float(self.factura_precio.get())
            
            if not all([proveedor, fecha, categoria, producto]):
                messagebox.showwarning("Advertencia", "Por favor complete todos los campos")
                return
            
            subtotal = cantidad * precio_unitario
            retencion = self.calcular_retencion(categoria, subtotal)
            total = subtotal - retencion
            
            self.cursor.execute('''
                INSERT INTO facturas (proveedor, fecha, categoria, producto, cantidad,
                                    precio_unitario, subtotal, retencion, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (proveedor, fecha, categoria, producto, cantidad, precio_unitario,
                  subtotal, retencion, total))
            
            self.conn.commit()
            messagebox.showinfo("Éxito", 
                              f"Factura registrada correctamente\n\n"
                              f"Subtotal: ${subtotal:,.0f}\n"
                              f"Retención: ${retencion:,.0f}\n"
                              f"Total: ${total:,.0f}")
            self.limpiar_factura()
            
        except ValueError:
            messagebox.showerror("Error", "Cantidad y precio deben ser números válidos")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
    
    def limpiar_factura(self):
        """Limpia el formulario de factura"""
        self.factura_proveedor.delete(0, tk.END)
        self.factura_producto.delete(0, tk.END)
        self.factura_cantidad.delete(0, tk.END)
        self.factura_precio.delete(0, tk.END)
        self.factura_categoria.set('')
        self.info_retencion.config(text='')
    
    def crear_pestana_pedidos(self):
        """Crea la pestaña para gestionar pedidos"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📦 Pedidos")
        
        # Frame para formulario
        form_frame = ttk.LabelFrame(frame, text="Nuevo Pedido de Insumos", padding=15)
        form_frame.pack(fill='x', padx=10, pady=10)
        
        # Proveedor
        ttk.Label(form_frame, text="Proveedor:").grid(row=0, column=0, sticky='w', pady=5)
        self.pedido_proveedor = ttk.Entry(form_frame, width=30)
        self.pedido_proveedor.grid(row=0, column=1, pady=5, padx=5)
        
        # Fecha pedido
        ttk.Label(form_frame, text="Fecha Pedido:").grid(row=0, column=2, sticky='w', pady=5, padx=(20, 0))
        self.pedido_fecha = ttk.Entry(form_frame, width=15)
        self.pedido_fecha.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.pedido_fecha.grid(row=0, column=3, pady=5, padx=5)
        
        # Categoría
        ttk.Label(form_frame, text="Categoría:").grid(row=1, column=0, sticky='w', pady=5)
        self.pedido_categoria = ttk.Combobox(form_frame, width=28, values=[
            'Jornales', 'Agroquímicos', 'Concentrado', 'Dotaciones', 'Maquinaria'
        ])
        self.pedido_categoria.grid(row=1, column=1, pady=5, padx=5)
        
        # Producto
        ttk.Label(form_frame, text="Producto:").grid(row=1, column=2, sticky='w', pady=5, padx=(20, 0))
        self.pedido_producto = ttk.Entry(form_frame, width=30)
        self.pedido_producto.grid(row=1, column=3, pady=5, padx=5)
        
        # Cantidad
        ttk.Label(form_frame, text="Cantidad:").grid(row=2, column=0, sticky='w', pady=5)
        self.pedido_cantidad = ttk.Entry(form_frame, width=15)
        self.pedido_cantidad.grid(row=2, column=1, pady=5, padx=5, sticky='w')
        
        # Estado
        ttk.Label(form_frame, text="Estado:").grid(row=2, column=2, sticky='w', pady=5, padx=(20, 0))
        self.pedido_estado = ttk.Combobox(form_frame, width=28, values=[
            'Pendiente', 'En tránsito', 'Entregado', 'Cancelado'
        ])
        self.pedido_estado.current(0)
        self.pedido_estado.grid(row=2, column=3, pady=5, padx=5)
        
        # Fecha entrega
        ttk.Label(form_frame, text="Fecha Entrega:").grid(row=3, column=0, sticky='w', pady=5)
        self.pedido_fecha_entrega = ttk.Entry(form_frame, width=15)
        self.pedido_fecha_entrega.grid(row=3, column=1, pady=5, padx=5, sticky='w')
        
        # Botones
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=4, pady=15)
        
        ttk.Button(btn_frame, text="💾 Guardar Pedido", command=self.guardar_pedido).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Limpiar", command=self.limpiar_pedido).pack(side='left', padx=5)
        
        # Lista de pedidos
        list_frame = ttk.LabelFrame(frame, text="Pedidos Registrados", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview para pedidos
        self.pedidos_tree = ttk.Treeview(list_frame, columns=(
            'ID', 'Proveedor', 'Fecha', 'Categoría', 'Producto', 'Cantidad', 'Estado'
        ), show='headings', height=8)
        
        self.pedidos_tree.heading('ID', text='ID')
        self.pedidos_tree.heading('Proveedor', text='Proveedor')
        self.pedidos_tree.heading('Fecha', text='Fecha Pedido')
        self.pedidos_tree.heading('Categoría', text='Categoría')
        self.pedidos_tree.heading('Producto', text='Producto')
        self.pedidos_tree.heading('Cantidad', text='Cantidad')
        self.pedidos_tree.heading('Estado', text='Estado')
        
        self.pedidos_tree.column('ID', width=40)
        self.pedidos_tree.column('Proveedor', width=150)
        self.pedidos_tree.column('Fecha', width=100)
        self.pedidos_tree.column('Categoría', width=120)
        self.pedidos_tree.column('Producto', width=150)
        self.pedidos_tree.column('Cantidad', width=80)
        self.pedidos_tree.column('Estado', width=100)
        
        self.pedidos_tree.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.pedidos_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.pedidos_tree.configure(yscrollcommand=scrollbar.set)
        
        # Botón actualizar lista
        ttk.Button(list_frame, text="🔄 Actualizar Lista", command=self.cargar_pedidos).pack(pady=5)
        
        self.cargar_pedidos()
    
    def guardar_pedido(self):
        """Guarda un nuevo pedido"""
        try:
            proveedor = self.pedido_proveedor.get()
            fecha_pedido = self.pedido_fecha.get()
            categoria = self.pedido_categoria.get()
            producto = self.pedido_producto.get()
            cantidad = float(self.pedido_cantidad.get())
            estado = self.pedido_estado.get()
            fecha_entrega = self.pedido_fecha_entrega.get() or None
            
            if not all([proveedor, fecha_pedido, categoria, producto, estado]):
                messagebox.showwarning("Advertencia", "Por favor complete los campos obligatorios")
                return
            
            self.cursor.execute('''
                INSERT INTO pedidos (proveedor, fecha_pedido, fecha_entrega, categoria,
                                   producto, cantidad, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (proveedor, fecha_pedido, fecha_entrega, categoria, producto, cantidad, estado))
            
            self.conn.commit()
            messagebox.showinfo("Éxito", "Pedido registrado correctamente")
            self.limpiar_pedido()
            self.cargar_pedidos()
            
        except ValueError:
            messagebox.showerror("Error", "Cantidad debe ser un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
    
    def limpiar_pedido(self):
        """Limpia el formulario de pedido"""
        self.pedido_proveedor.delete(0, tk.END)
        self.pedido_producto.delete(0, tk.END)
        self.pedido_cantidad.delete(0, tk.END)
        self.pedido_fecha_entrega.delete(0, tk.END)
        self.pedido_categoria.set('')
        self.pedido_estado.current(0)
    
    def cargar_pedidos(self):
        """Carga la lista de pedidos"""
        for item in self.pedidos_tree.get_children():
            self.pedidos_tree.delete(item)
        
        self.cursor.execute('''
            SELECT id, proveedor, fecha_pedido, categoria, producto, cantidad, estado
            FROM pedidos ORDER BY fecha_pedido DESC
        ''')
        
        for row in self.cursor.fetchall():
            self.pedidos_tree.insert('', 'end', values=row)
    
    def crear_pestana_analisis(self):
        """Crea la pestaña de análisis estadístico"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Análisis")
        
        # Frame superior con estadísticas
        stats_frame = ttk.LabelFrame(frame, text="Estadísticas de Gastos", padding=15)
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=10, width=80, wrap='word')
        self.stats_text.pack(fill='x')
        
        # Frame para gráfica
        graph_frame = ttk.LabelFrame(frame, text="Gráficas", padding=10)
        graph_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Botones para diferentes gráficas
        btn_frame = ttk.Frame(graph_frame)
        btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(btn_frame, text="📊 Gastos por Categoría", 
                  command=self.grafica_por_categoria).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📈 Tendencia Mensual", 
                  command=self.grafica_tendencia).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Actualizar Análisis", 
                  command=self.actualizar_analisis).pack(side='left', padx=5)
        
        # Canvas para gráficas
        self.graph_canvas_frame = ttk.Frame(graph_frame)
        self.graph_canvas_frame.pack(fill='both', expand=True)
        
        self.actualizar_analisis()
    
    def actualizar_analisis(self):
        """Actualiza el análisis estadístico"""
        # Obtener estadísticas
        self.cursor.execute('SELECT SUM(total), AVG(total), MIN(total), MAX(total) FROM facturas')
        stats = self.cursor.fetchone()
        
        self.cursor.execute('SELECT categoria, SUM(total) FROM facturas GROUP BY categoria')
        categorias = self.cursor.fetchall()
        
        # Mostrar estadísticas
        texto = "═══════════════════════════════════════════════════\n"
        texto += "           RESUMEN ESTADÍSTICO DE GASTOS\n"
        texto += "═══════════════════════════════════════════════════\n\n"
        
        if stats[0]:
            texto += f"💰 Total gastado:      ${stats[0]:,.0f}\n"
            texto += f"📊 Promedio por factura: ${stats[1]:,.0f}\n"
            texto += f"📉 Gasto mínimo:       ${stats[2]:,.0f}\n"
            texto += f"📈 Gasto máximo:       ${stats[3]:,.0f}\n\n"
            
            texto += "DISTRIBUCIÓN POR CATEGORÍA:\n"
            texto += "─────────────────────────────────────────────────\n"
            for cat, total in categorias:
                porcentaje = (total / stats[0]) * 100
                texto += f"  • {cat:20s}: ${total:>12,.0f} ({porcentaje:>5.1f}%)\n"
            
            texto += "\n📌 CONCLUSIONES:\n"
            texto += "─────────────────────────────────────────────────\n"
            
            # Categoría con más gasto
            cat_max = max(categorias, key=lambda x: x[1])
            texto += f"  • Mayor gasto: {cat_max[0]} (${cat_max[1]:,.0f})\n"
            
            # Categoría con menos gasto
            cat_min = min(categorias, key=lambda x: x[1])
            texto += f"  • Menor gasto: {cat_min[0]} (${cat_min[1]:,.0f})\n"
            
            # Análisis de rango
            rango = stats[3] - stats[2]
            texto += f"  • Rango de variación: ${rango:,.0f}\n"
            
            if stats[1] > 500000:
                texto += "  ⚠️  Promedio de factura alto, considere revisión\n"
        else:
            texto += "No hay datos disponibles para análisis.\n"
        
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0', texto)
        
        # Mostrar primera gráfica por defecto
        self.grafica_por_categoria()
    
    def grafica_por_categoria(self):
        """Crea gráfica de gastos por categoría"""
        # Limpiar canvas anterior
        for widget in self.graph_canvas_frame.winfo_children():
            widget.destroy()
        
        # Obtener datos
        self.cursor.execute('SELECT categoria, SUM(total) FROM facturas GROUP BY categoria')
        datos = self.cursor.fetchall()
        
        if not datos:
            return
        
        categorias = [d[0] for d in datos]
        totales = [d[1] for d in datos]
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(8, 5))
        colores = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        
        ax.bar(categorias, totales, color=colores[:len(categorias)])
        ax.set_xlabel('Categoría')
        ax.set_ylabel('Total ($)')
        ax.set_title('Gastos por Categoría')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Mostrar en canvas
        canvas = FigureCanvasTkAgg(fig, self.graph_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def grafica_tendencia(self):
        """Crea gráfica de tendencia mensual"""
        # Limpiar canvas anterior
        for widget in self.graph_canvas_frame.winfo_children():
            widget.destroy()
        
        # Obtener datos por mes
        self.cursor.execute('''
            SELECT strftime('%Y-%m', fecha) as mes, SUM(total)
            FROM facturas
            GROUP BY mes
            ORDER BY mes
        ''')
        datos = self.cursor.fetchall()
        
        if not datos:
            return
        
        meses = [d[0] for d in datos]
        totales = [d[1] for d in datos]
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(meses, totales, marker='o', linewidth=2, markersize=8, color='#4ECDC4')
        ax.fill_between(range(len(meses)), totales, alpha=0.3, color='#4ECDC4')
        ax.set_xlabel('Mes')
        ax.set_ylabel('Total ($)')
        ax.set_title('Tendencia de Gastos Mensuales')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Mostrar en canvas
        canvas = FigureCanvasTkAgg(fig, self.graph_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def crear_pestana_consultas(self):
        """Crea la pestaña de consultas y exploración"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔍 Consultas")
        
        # Frame de filtros
        filter_frame = ttk.LabelFrame(frame, text="Filtros de Búsqueda", padding=15)
        filter_frame.pack(fill='x', padx=10, pady=10)
        
        # Mes
        ttk.Label(filter_frame, text="Mes:").grid(row=0, column=0, sticky='w', pady=5)
        self.consulta_mes = ttk.Combobox(filter_frame, width=15, values=[
            'Todos', '01', '02', '03', '04', '05', '06', 
            '07', '08', '09', '10', '11', '12'
        ])
        self.consulta_mes.current(0)
        self.consulta_mes.grid(row=0, column=1, pady=5, padx=5)
        
        # Año
        ttk.Label(filter_frame, text="Año:").grid(row=0, column=2, sticky='w', pady=5, padx=(20, 0))
        self.consulta_anio = ttk.Combobox(filter_frame, width=10, values=['Todos', '2024', '2025'])
        self.consulta_anio.current(0)
        self.consulta_anio.grid(row=0, column=3, pady=5, padx=5)
        
        # Categoría
        ttk.Label(filter_frame, text="Categoría:").grid(row=1, column=0, sticky='w', pady=5)
        self.consulta_categoria = ttk.Combobox(filter_frame, width=20, values=[
            'Todas', 'Jornales', 'Agroquímicos', 'Concentrado', 'Dotaciones', 'Maquinaria'
        ])
        self.consulta_categoria.current(0)
        self.consulta_categoria.grid(row=1, column=1, pady=5, padx=5)
        
        # Botones
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.grid(row=1, column=2, columnspan=2, pady=5, padx=(20, 0))
        
        ttk.Button(btn_frame, text="🔍 Buscar", command=self.buscar_facturas).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Limpiar", command=self.limpiar_consulta).pack(side='left', padx=5)
        
        # Tabla de resultados
        result_frame = ttk.LabelFrame(frame, text="Resultados", padding=10)
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview para facturas
        self.consulta_tree = ttk.Treeview(result_frame, columns=(
            'ID', 'Fecha', 'Proveedor', 'Categoría', 'Producto', 'Cantidad', 'Subtotal', 'Retención', 'Total'
        ), show='headings', height=12)
        
        self.consulta_tree.heading('ID', text='ID')
        self.consulta_tree.heading('Fecha', text='Fecha')
        self.consulta_tree.heading('Proveedor', text='Proveedor')
        self.consulta_tree.heading('Categoría', text='Categoría')
        self.consulta_tree.heading('Producto', text='Producto')
        self.consulta_tree.heading('Cantidad', text='Cant.')
        self.consulta_tree.heading('Subtotal', text='Subtotal')
        self.consulta_tree.heading('Retención', text='Retención')
        self.consulta_tree.heading('Total', text='Total')
        
        self.consulta_tree.column('ID', width=40)
        self.consulta_tree.column('Fecha', width=90)
        self.consulta_tree.column('Proveedor', width=130)
        self.consulta_tree.column('Categoría', width=100)
        self.consulta_tree.column('Producto', width=130)
        self.consulta_tree.column('Cantidad', width=60)
        self.consulta_tree.column('Subtotal', width=90)
        self.consulta_tree.column('Retención', width=90)
        self.consulta_tree.column('Total', width=90)
        
        self.consulta_tree.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(result_frame, orient='vertical', command=self.consulta_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.consulta_tree.configure(yscrollcommand=scrollbar.set)
        
        # Resumen
        self.resumen_label = ttk.Label(result_frame, text="", font=('Arial', 10, 'bold'))
        self.resumen_label.pack(pady=10)
        
        # Cargar datos iniciales
        self.buscar_facturas()
    
    def buscar_facturas(self):
        """Busca facturas según los filtros"""
        # Limpiar tabla
        for item in self.consulta_tree.get_children():
            self.consulta_tree.delete(item)
        
        # Construir query
        query = 'SELECT id, fecha, proveedor, categoria, producto, cantidad, subtotal, retencion, total FROM facturas WHERE 1=1'
        params = []
        
        # Filtro de mes
        mes = self.consulta_mes.get()
        if mes != 'Todos':
            query += " AND strftime('%m', fecha) = ?"
            params.append(mes)
        
        # Filtro de año
        anio = self.consulta_anio.get()
        if anio != 'Todos':
            query += " AND strftime('%Y', fecha) = ?"
            params.append(anio)
        
        # Filtro de categoría
        categoria = self.consulta_categoria.get()
        if categoria != 'Todas':
            query += " AND categoria = ?"
            params.append(categoria)
        
        query += ' ORDER BY fecha DESC'
        
        # Ejecutar query
        self.cursor.execute(query, params)
        resultados = self.cursor.fetchall()
        
        # Mostrar resultados
        total_general = 0
        for row in resultados:
            # Formatear montos
            row_formatted = list(row)
            row_formatted[6] = f"${row[6]:,.0f}"  # Subtotal
            row_formatted[7] = f"${row[7]:,.0f}"  # Retención
            row_formatted[8] = f"${row[8]:,.0f}"  # Total
            
            self.consulta_tree.insert('', 'end', values=row_formatted)
            total_general += row[8]
        
        # Actualizar resumen
        self.resumen_label.config(
            text=f"📊 {len(resultados)} facturas encontradas | Total: ${total_general:,.0f}"
        )
    
    def limpiar_consulta(self):
        """Limpia los filtros de consulta"""
        self.consulta_mes.current(0)
        self.consulta_anio.current(0)
        self.consulta_categoria.current(0)
        self.buscar_facturas()


# Crear y ejecutar la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaContabilidadLechera(root)
    root.mainloop()