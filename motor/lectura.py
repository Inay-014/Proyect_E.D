"""Lectura de los tres CSV. Solo usa el modulo csv (permitido en el motor).

No se asume que las filas vengan ordenadas ni agrupadas: la red de prueba del
profesor puede venir en cualquier orden.
"""
from .tabla_hash import TablaHash
import csv

from .tiempo import hora_a_minutos


def _filas(ruta_archivo):
    """Genera las filas de datos de un CSV, saltando el encabezado y las filas vacias.

    utf-8-sig tolera un BOM al inicio; newline='' deja que csv maneje \\r\\n.
    """
    with open(ruta_archivo, newline="", encoding="utf-8-sig") as archivo:
        lector = csv.reader(archivo)
        es_encabezado = True
        for fila in lector:
            if es_encabezado:
                es_encabezado = False
                continue
            if len(fila) == 0:
                continue
            yield fila


def leer_estaciones(ruta_archivo):
    """Lista de nombres de estacion, sin repetidos, en el orden en que aparecen. O(n)."""
    vistos = TablaHash()
    nombres = []
    for fila in _filas(ruta_archivo):
        nombre = fila[0].strip()
        if nombre == "" or nombre in vistos:
            continue
        vistos[nombre] = True
        nombres.append(nombre)
    return nombres


def leer_rutas(ruta_archivo):
    """TablaHash: ruta -> lista de (orden, estacion), SIN ordenar todavia. O(n)."""
    rutas = TablaHash()
    for fila in _filas(ruta_archivo):
        if len(fila) < 3:
            continue
        ruta = fila[0].strip()
        if ruta not in rutas:
            rutas[ruta] = []
        rutas[ruta].append((int(fila[1]), fila[2].strip()))
    return rutas


def leer_horarios(ruta_archivo):
    """TablaHash: estacion -> TablaHash(ruta -> lista de minutos), SIN ordenar todavia. O(n).

    Se indexa por estacion primero porque R4 (proximo_bus) y R6 (ranking)
    preguntan siempre desde una estacion.
    """
    horarios = TablaHash()
    for fila in _filas(ruta_archivo):
        if len(fila) < 3:
            continue
        ruta = fila[0].strip()
        estacion = fila[1].strip()
        minutos = hora_a_minutos(fila[2])
        if estacion not in horarios:
            horarios[estacion] = TablaHash()
        por_ruta = horarios[estacion]
        if ruta not in por_ruta:
            por_ruta[ruta] = []
        por_ruta[ruta].append(minutos)
    return horarios
