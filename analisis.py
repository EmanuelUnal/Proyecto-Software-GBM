import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

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

def mes_exacto(fecha_str:str):
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    hoy = datetime.today().date()

    d = (hoy - fecha).days

    if d < 0: return 0
    elif d <= 30: return 1
    elif d <= 60: return 2
    elif d <= 90: return 3
    elif d <= 120: return 4
    elif d <= 150: return 5
    elif d <= 180: return 6
    else: return 0
    
def diferencial(V1: tuple, V2:tuple):
    lejos = V2[1]
    recien = V1[1]
    return (V1[0], recien - lejos)

def aumento(valor:float, recargo:float): return valor + valor * recargo / 100

def crece1(d:float):
    if d < 0: return "*El precio está decreciendo en\nuna tasa de ${} al mes".format(round(d,1))
    elif d == 0: return "*El precio se mantiene constante"
    else: return "*El precio ha aumentado en\nuna tasa de ${} al mes".format(round(d,1))

def crece2(d:float):
    if d < 0: return "*El crecimiento está decreciendo en\nuna tasa de ${} al mes,\nposiblemente el precio decrezca".format(round(d,1))
    elif d == 0: return "*El precio crece a un ritmo constante"
    else: return "*El crecimiento ha aumentado en\nuna tasa de ${} al mes,\nposiblemente el precio crezca más".format(round(d,1))

def promedio(dic):
    if not dic:
        return 0
    return sum(dic.values()) / len(dic)


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
        "*La empresa que menos aumentó\n" +
        "de precios es:\n{} con ${}".format(menos_creciente[0], menos_creciente[1]))

def general():
    tabla = Path(__file__).with_name("contabilidad_lechera.db")

    conexion = sqlite3.connect(tabla)
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM facturas")
    filas = cursor.fetchall()
    conexion.close()
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
    return ("*En los últimos tres meses\nse gastó en promedio un total de\n${}".format(round(promedio, 1)),
            "*En los últimos tres meses el\nproducto en el que más se ha\ninvertido, con un total de ${}\nes {}".format(mayor[1], mayor[0]),
            "*El aumento de gasto en los últimos\ntres meses ha sido de ${}".format(dif))

def productos(producto):
    tabla = Path(__file__).with_name("contabilidad_lechera.db")

    conexion = sqlite3.connect(tabla)
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM facturas WHERE producto = ?", (producto,))
    filas = cursor.fetchall()
    conexion.close()
    if not filas:
        return(0,0,0)
    precio6 = {}
    precio5 = {}
    precio4 = {}
    precio3 = {}
    precio2 = {}
    precio1 = {}
    for fila in filas:
        match mes_exacto(fila[2]):
            case 1:
                precio1[fila[1]] = fila[6]
            case 2:
                precio2[fila[1]] = fila[6]
            case 3:
                precio3[fila[1]] = fila[6]
            case 4:
                precio4[fila[1]] = fila[6]
            case 5:
                precio5[fila[1]] = fila[6]
            case 6:
                precio6[fila[1]] = fila[6]
            case _:
                pass
    val1 = promedio(precio1)
    val2 = promedio(precio2)
    val3 = promedio(precio3)
    val4 = promedio(precio4)
    val5 = promedio(precio5)
    val6 = promedio(precio6)
    if(val1 == 0 and
       val2 == 0 and
       val3 == 0 and
       val4 == 0 and
       val5 == 0 and
       val6 == 0): return (-1,-1,-1)
    
    lista = []
    derivada = []
    derivada2 = []
    dev1 = 0
    dev2 = 0
    text1 = ""
    text2 = ""
    if val6 > 0: lista.append(val6)
    if val5 > 0: lista.append(val5)
    if val4 > 0: lista.append(val4)
    if val3 > 0: lista.append(val3)
    if val2 > 0: lista.append(val2)
    if val1 > 0: lista.append(val1)
    if len(lista) < 3:
        if len(lista) < 2:
            text1 = "*No hay información suficiente\npara reportar un comportamiento"
        else:
            dev1 = lista[1] - lista[0]
            text1 = crece1(dev1)
            
        text2 = "*No hay información suficiente\npara predecir un comportamiento"
    else:
        for i in range(0, len(lista) - 1): 
            derivada.append(lista[i+1] - lista[i])
        for i in range(0, len(derivada) - 1):
            derivada2.append(derivada[i+1] - derivada[i])
        dev1 = sum(derivada) / len(derivada)
        dev2 = sum(derivada2) / len(derivada2)
        text1 = crece1(dev1)
        text2 = crece2(dev2)
    precio = "*El precio actual del producto\nestá en aproximadamente ${}".format(round(lista[-1],1))
    return (precio,text1,text2)