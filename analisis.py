import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
#(1, 'AgroSupply', '2025-10-01', 'Fertilizante A', 10, 'Agroquímico', 25.0, 19.0, 0.0, 297.5, 'FE0001', 'PD001', 250.0, 297.5)
def hace_un_mes(fecha_str:str):
    fechae = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    fecha = datetime.today().date()
    diferencia = fecha - timedelta(days=30)
    return fechae >= diferencia

def hace_tres_meses(fecha_str:str):
    fechae = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    fecha = datetime.today().date()
    diferencia = fecha - timedelta(days=90)
    return fechae >= diferencia

def hace_seis_meses(fecha_str:str):
    fechae = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    fecha = datetime.today().date()
    diferencia = fecha - timedelta(days=183)
    return fechae >= diferencia


def fecha_reciente(f1:tuple, f2:tuple):
    fecha1 = datetime.strptime(f1[2], '%Y-%m-%d').date()
    fecha2 = datetime.strptime(f2[2], '%Y-%m-%d').date()
    if fecha1 > fecha2:
        return f1
    else:
        return f2

def fecha_lejana(f1:tuple, f2:tuple):
    fecha1 = datetime.strptime(f1[2], '%Y-%m-%d').date()
    fecha2 = datetime.strptime(f2[2], '%Y-%m-%d').date()

    if fecha1 > fecha2:
        return f2
    else:
        return f1

def diferencial(V1: tuple, V2:tuple):
    lejos = V2[1]
    recien = V1[1]
    return (V1[0], recien - lejos)


def recomendacion():
    tabla = Path(__file__).with_name("contabilidad_lechera.db")

    conexion = sqlite3.connect(tabla)
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM facturas")
    filas = cursor.fetchall()
    llamados = {}
    prov_bar = {}
    precios = {}
    precios_viejos = {}
    for fila in filas:
        if hace_un_mes(fila[2]):
            if fila[1] in llamados:
                llamados[fila[1]] += 1
            else:
                llamados[fila[1]] = 1
            if fila[1] in prov_bar:
                prov_bar[fila[1]] = fecha_reciente(prov_bar[fila[1]], (fila[1], fila[6], fila[2]))
            else:
                prov_bar[fila[1]] = (fila[1], fila[6], fila[2])
            if fila[1] in precios:
                precios[fila[1]] = fecha_reciente(prov_bar[fila[1]], (fila[1], fila[6], fila[2]))
            else:
                precios[fila[1]] = (fila[1], fila[6], fila[2])

    for fila in filas:
        if hace_tres_meses(fila[2]):
            if fila[1] in precios and fila[1] not in precios_viejos:
                precios_viejos[fila[1]] = (fila[1], fila[6], fila[2])
            elif fila[1] in precios_viejos:
                precios_viejos[fila[1]] = fecha_lejana(precios_viejos[fila[1]], (fila[1], fila[6], fila[2]))

    mas_llamada = ("", 0)
    mas_barata = ("", 0)
    menos_creciente = ("", "None")
    for empresa in llamados:
        if llamados[empresa] > mas_llamada[1]:
            mas_llamada = (empresa, llamados[empresa])
    for empresa in prov_bar:
        if prov_bar[empresa][1] < mas_barata[1] or mas_barata[1] == 0:
            mas_barata = (empresa, prov_bar[empresa][1])
    for empresa in precios:
        print(precios[empresa])
        print(precios_viejos[empresa])
        dif = diferencial(precios[empresa], precios_viejos[empresa])
        if menos_creciente[1] == "None" or dif[1] < menos_creciente[1]:
            menos_creciente = dif
    
    conexion.close()

    return ("*La empresa más económica es:\n{} con ${}".format(mas_barata[0], mas_barata[1]),
        "*La empresa más confiable es:\n{} con {} llamados".format(mas_llamada[0], mas_llamada[1]),
        "*La empresa con menos aumento\nde precios es:\n{} con ${}".format(menos_creciente[0], menos_creciente[1]))


(a,b,c) = recomendacion()
print(a)
print(b)
print(c)