"""Prueba R1 (estado) por separado: python pruebas/prueba_r1.py"""
from _comun import *

red = red_real()
nombres = [f[0] for f in filas("estaciones.csv")]
assert len(nombres) == 147
for n in nombres:
    assert red.estado(n) == "ABIERTA", n
assert red.estado("NO EXISTE") == "NO EXISTE"
assert red.estado("calle 26") == "NO EXISTE", "el nombre debe ser EXACTO"
assert red.estado("") == "NO EXISTE"
red.cerrar("CALLE 26")
assert red.estado("CALLE 26") == "CERRADA"
red.reabrir("CALLE 26")
assert red.estado("CALLE 26") == "ABIERTA"
print("ok  R1 estado: 147 reales, inexistente, mayúsculas exactas, cerrada y reabierta")
