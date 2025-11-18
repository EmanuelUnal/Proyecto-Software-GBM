import sqlite3
from pathlib import Path

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

samples = [
    ("AgroSupply", "2025-10-01", "Fertilizante A", 10, "Agroquímico", 25.0, 19.0, 0.0, 297.5, "FE0001", "PD001", 250.0, 297.5),
    ("VetCorp", "2025-10-05", "Vacuna X", 5, "Medicamento", 40.0, 19.0, 2.0, 209.0, "FE0002", "PD002", 200.0, 209.0),
    ("MaquiRent", "2025-10-10", "Reparación", 1, "Maquinaria", 500.0, 0.0, 0.0, 500.0, "FE0003", "PD003", 500.0, 500.0)
]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.executescript(schema)

# Insert sample rows only if table empty
cur.execute("SELECT COUNT(1) FROM facturas")
if cur.fetchone()[0] == 0:
    cur.executemany(
        "INSERT INTO facturas (proveedor, fecha, producto, cantidad, concepto, valoru, iva, retencion, valort, codigo_factura, codigo_pedido, subtotal, total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        samples
    )
    conn.commit()

conn.close()
print("Base de datos creada/actualizada en:", DB_PATH)