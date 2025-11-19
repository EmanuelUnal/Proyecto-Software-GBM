import sqlite3
from pathlib import Path
from datetime import date, timedelta

DB_PATH = Path(__file__).with_name("contabilidad_lechera.db")

schema = """
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
);
"""

# Proveedores reales (Colombia) y productos con concepto consistente
PROVEEDORES = [
    "Alpina S.A.", "Colanta", "Alquería", "Nestlé Colombia", "Grupo Nutresa",
    "Agroferrero S.A.S.", "Distribuciones Lecheras SAS", "Veterinaria Santa Fe",
    "Maquinaria Agrícola Colombia", "Insumos Pecuarios Ltda.", "Laboratorios VetCol",
"Transportes Frigoríficos SAS"
]

# Productos y mapeo consistente: (proveedor, concepto_base, precio_base, iva%)
PRODUCTS = [
    ("Leche en polvo", "Compra Leche en polvo", "Alpina S.A.", 120.0, 19.0),
    ("Concentrado para terneros", "Compra concentrado terneros", "Colanta", 95.0, 19.0),
    ("Fertilizante NPK", "Compra fertilizante NPK", "Agroferrero S.A.S.", 350.0, 19.0),
    ("Vacuna contra brucelosis", "Compra vacuna brucelosis", "Laboratorios VetCol", 45.0, 0.0),
    ("Aceite vegetal", "Compra aceite vegetal", "Nestlé Colombia", 12.5, 19.0),
    ("Repuestos maquinaria", "Compra repuestos maquinaria", "Maquinaria Agrícola Colombia", 520.0, 19.0),
    ("Servicio reparación bomba", "Servicio reparación bomba", "Maquinaria Agrícola Colombia", 200.0, 0.0),
    ("Bolsa forraje 25kg", "Compra forraje 25kg", "Distribuciones Lecheras SAS", 28.0, 19.0),
    ("Suplemento mineral", "Compra suplemento mineral", "Insumos Pecuarios Ltda.", 65.0, 19.0),
    ("Lubricante motor", "Compra lubricante motor", "Transportes Frigoríficos SAS", 18.0, 19.0),
    ("Producto de limpieza", "Compra producto limpieza", "Grupo Nutresa", 9.5, 19.0),
    ("Envases plásticos", "Compra envases plásticos", "Distribuciones Lecheras SAS", 3.0, 19.0),
]

def make_row(idx, start_date):
    # determinista: elegir producto por índice
    prod_idx = idx % len(PRODUCTS)
    producto, concepto_base, proveedor_default, precio_base, iva = PRODUCTS[prod_idx]

    # proveedor coherente (usar el proveedor del mapping)
    proveedor = proveedor_default

    # fecha: secuencial desde start_date
    fecha = (start_date + timedelta(days=idx)).isoformat()

    # cantidad: determinista según índice, 1..50
    cantidad = (idx % 20) + 1

    # ajustar precio ligeramente según índice para variedad pero determinista
    # ahora valoru en pesos colombianos -> multiplicar la base por 1000
    valoru = round((precio_base + ((idx * 13) % 37) * 0.5) * 1000.0, 2)

    # retención: aplicar retención en pocos casos (determinista)
    retencion = 0.0
    if (idx % 11) == 0:  # cada 11º factura tiene retención pequeña
        retencion = round( (valoru * cantidad) * 0.02, 2 )

    subtotal = round(cantidad * valoru, 2)
    valort = round(subtotal * (1 + iva / 100.0) - retencion, 2)
    total = valort

    codigo_factura = f"FE{10000 + idx}"
    codigo_pedido = f"PD{5000 + idx}"

    concepto = concepto_base

    return (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_factura, codigo_pedido, subtotal, total)

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(schema)

    cur.execute("SELECT COUNT(1) FROM facturas")
    existing = cur.fetchone()[0]

    target = 50
    to_add = target - existing
    if to_add <= 0:
        print(f"Ya hay {existing} registros en {DB_PATH}. No se añadirán filas.")
        conn.close()
        return

    # start date fijo determinista
    start_date = date(2024, 1, 1)

    rows = []
    for i in range(existing, existing + to_add):
        rows.append(make_row(i, start_date))

    cur.executemany(
        "INSERT INTO facturas (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_factura, codigo_pedido, subtotal, total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows
    )
    conn.commit()
    conn.close()
    print(f"Se añadieron {to_add} registros a {DB_PATH} (total ahora: {target}).")

if __name__ == "__main__":
    main()