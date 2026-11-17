"""Pruebas de la Fase 1. Corre con: python pruebas/prueba_fase1.py
(Fuera de motor/ SI se puede usar cualquier libreria, por eso aqui hay sorted, os, etc.)
"""
import csv
import os
import random
import shutil
import sys
import tempfile
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from motor import Red
from motor.ordenar import merge_sort
from motor.tiempo import hora_a_minutos, minutos_a_hora


def prueba_ordenar():
    random.seed(1)
    for n in (0, 1, 2, 3, 10, 1000):
        datos = [random.randint(0, 50) for _ in range(n)]
        copia = datos[:]
        assert merge_sort(datos) == sorted(datos)
        assert datos == copia, "no debe modificar la lista original"
    pares = [(random.randint(0, 5), i) for i in range(300)]
    assert merge_sort(pares, lambda p: p[0]) == sorted(pares, key=lambda p: p[0]), "estabilidad"
    textos = ["CALLE 26", "AV. 1 DE MAYO", "21 ANGELES", "ALCALA", "AGUAS"]
    assert merge_sort(textos) == sorted(textos)
    print("ok  merge_sort (vacio, 1, repetidos, estable, no muta)")


def prueba_tiempo():
    assert hora_a_minutos("00:01") == 1
    assert hora_a_minutos("23:59") == 1439
    assert hora_a_minutos("25:10") == 1510
    assert minutos_a_hora(1510) == "25:10"
    assert minutos_a_hora(5) == "00:05"
    for malo in ("abc", "10:75", "1010", ""):
        try:
            hora_a_minutos(malo)
            assert False, "debio fallar con " + malo
        except ValueError:
            pass
    print("ok  conversion de horas (incluye 25:10)")


def _esperado_rutas(carpeta):
    esperado = {}
    with open(os.path.join(carpeta, "rutas.csv"), newline="", encoding="utf-8-sig") as f:
        lector = csv.reader(f)
        next(lector)
        filas = [(r[0], int(r[1]), r[2]) for r in lector if r]
    for ruta, orden, est in sorted(filas, key=lambda t: (t[0], t[1])):
        esperado.setdefault(ruta, []).append(est)
    return esperado


def prueba_carga():
    carpeta = os.path.join(RAIZ, "datos")
    t0 = time.perf_counter()
    red = Red(carpeta)
    dt = time.perf_counter() - t0
    assert len(red.tabla.datos) == 147
    assert len(red.rutas.recorridos) == 181
    assert sum(len(r) for r in red.rutas.recorridos.values()) == 1927
    assert red.indice.nombres == sorted(red.tabla.datos)
    assert all(e.abierta for e in red.tabla.datos.values())
    total = red.horarios.total_filas()
    assert total == 140492
    esperado = _esperado_rutas(carpeta)
    for ruta, paradas in esperado.items():
        rec = red.rutas.recorridos[ruta]
        assert rec.a_lista() == paradas
        assert rec.a_lista(al_reves=True) == paradas[::-1]
        assert len(rec.nodos) == len(paradas)
    print(f"ok  carga real: 147 estaciones, 181 rutas, 1927 paradas, 140492 horarios ({dt:.2f} s)")


def prueba_desordenado():
    """Mismos datos con las filas de rutas.csv barajadas: debe dar el mismo resultado."""
    origen = os.path.join(RAIZ, "datos")
    tmp = tempfile.mkdtemp()
    try:
        shutil.copy(os.path.join(origen, "estaciones.csv"), tmp)
        shutil.copy(os.path.join(origen, "horarios.csv"), tmp)
        with open(os.path.join(origen, "rutas.csv"), newline="", encoding="utf-8-sig") as f:
            filas = list(csv.reader(f))
        encabezado, cuerpo = filas[0], filas[1:]
        random.seed(7)
        random.shuffle(cuerpo)
        with open(os.path.join(tmp, "rutas.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(encabezado)
            w.writerows(cuerpo)
        red = Red(tmp)
        esperado = _esperado_rutas(origen)
        for ruta, paradas in esperado.items():
            assert red.rutas.recorridos[ruta].a_lista() == paradas
    finally:
        shutil.rmtree(tmp)
    print("ok  rutas.csv desordenado produce las mismas rutas")


if __name__ == "__main__":
    prueba_ordenar()
    prueba_tiempo()
    prueba_carga()
    prueba_desordenado()
    print("FASE 1: TODO OK")
