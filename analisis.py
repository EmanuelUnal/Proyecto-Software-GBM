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

def aumento(valor:float, recargo:float): return valor + valor * recargo / 100

def recomendacion(producto: str):
    tabla = Path(__file__).with_name("contabilidad_lechera.db")

    conexion = sqlite3.connect(tabla)
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM facturas WHERE producto = ?", (producto,))
    filas = cursor.fetchall()
    if not filas:
        return(0,0,0)
    conexion.close()
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
    if len(llamados) < 1 or len(prov_bar) < 1 or len(precios) < 1:
        return(-1,-1,-1)

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

    return ("*La empresa más económica es:\n" +
            "{} con ${}".format(mas_barata[0], mas_barata[1]),
        "*La empresa más confiable es:\n" +
        "{} con {} llamados".format(mas_llamada[0], mas_llamada[1]),
        "*La empresa con menos aumento\n" +
        "de precios es:\n{} con ${}".format(menos_creciente[0], menos_creciente[1]))

def general():
    tabla = Path(__file__).with_name("contabilidad_lechera.db")

    conexion = sqlite3.connect(tabla)
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM facturas")
    filas = cursor.fetchall()
    en_tres = {}
    en_uno = {}
    for fila in filas:
        if fila[1] in en_tres:
            en_tres[fila[1]] += aumento(fila[6] * fila[4], fila[7])
        elif hace_tres_meses(fila[2]):
            en_tres[fila[1]] = aumento(fila[6] * fila[4], fila[7])
    
    for fila in filas:
        if fila[1] in en_uno:
            en_uno[fila[1]] += aumento(fila[6] * fila[4], fila[7])
        elif hace_un_mes(fila[2]):
            en_uno[fila[1]] = aumento(fila[6] * fila[4], fila[7])

    if len(en_tres) < 1: return (-1, -1, -1)
    promedio = 0
    mayor = ("", 0)
    for elemento in en_tres:
        promedio += en_tres[elemento]
        if en_tres[elemento] > mayor[1]:
            mayor = (elemento, en_tres[elemento])
    dif = sum(en_tres.values()) - sum(en_uno.values())
    promedio /= 3
    return ("*En los últimos tres meses\nse gastó en promedio un total de\n${}".format(dif),
            "*En los últimos tres meses el\nproducto en el que más se ha\ninvertido es {} con un\ntotal de ${}".format(mayor[0], mayor[1]),
            "El aumento de gasto en los últimos\ntres meses ha sido de ${}".format(dif))


(a,b,c) = general()
print(a)
print(b)
print(c)