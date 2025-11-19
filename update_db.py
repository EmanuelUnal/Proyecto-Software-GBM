import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("contabilidad_lechera.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Backup opcional (simple copia de archivo)
    # from shutil import copyfile
    # copyfile(DB_PATH, DB_PATH.with_suffix(".db.bak"))

    # Multiplica valoru por 1000 para todos los registros
    cur.execute("UPDATE facturas SET valoru = valoru * 1000")
    conn.commit()

    # Recalcula subtotal, valort y total usando valores actualizados
    # subtotal = cantidad * valoru
    # valort = subtotal * (1 + iva/100) - retencion
    # total = valort
    cur.execute("SELECT id, cantidad, valoru, iva, retencion FROM facturas")
    rows = cur.fetchall()
    for id_, cantidad, valoru, iva, retencion in rows:
        try:
            subtotal = round(cantidad * valoru, 2)
            valort = round(subtotal * (1 + (iva or 0) / 100.0), 2)
            total = valort
            retencion_nueva = retencion
            if retencion >= 15:
                retencion_nueva = 2.0
            cur.execute("UPDATE facturas SET subtotal = ?, valort = ?, retencion = ?, total = ? WHERE id = ?",
                        (subtotal, valort, retencion_nueva, total, id_))
        except Exception as e:
            print(f"Error al recalcular id={id_}: {e}")
    conn.commit()
    conn.close()
    print("Actualización completada: valoru*1000 y recalculados subtotal/valort/total.")

if __name__ == "__main__":
    main()