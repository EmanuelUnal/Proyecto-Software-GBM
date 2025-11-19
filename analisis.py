import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

def hace_un_mes(fecha_str:str):
    fechae = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    fecha = datetime.today().date()
    diferencia = fecha - timedelta(days=30)
    return fechae >= diferencia

def recomendacion():
    tabla = Path(__file__).with_name("contabilidad_lechera.db")

    conexion = sqlite3.connect(tabla)
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM facturas")
    filas = cursor.fetchall()
    prov_bar = filas[0][1]
    for fila in filas:
        if hace_un_mes(fila[2]) and True:
            break
            
    conexion.close()

recomendacion()