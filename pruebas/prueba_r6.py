"""Prueba R6 (ranking) por separado."""
from _comun import *

def esperado(totales, abiertas, k):
    lista = sorted(abiertas, key=lambda n: (-totales.get(n, 0), n))
    return [(n, totales.get(n, 0)) for n in lista][:k]

red = red_real()
totales, por_par = {}, {}
for r, e, h in filas("horarios.csv"):
    totales[e] = totales.get(e, 0) + 1
    por_par[(e, r)] = por_par.get((e, r), 0) + 1
abiertas = set(f[0] for f in filas("estaciones.csv"))
for k in (1, 5, 10, 147, 500):
    assert red.ranking(k) == esperado(totales, abiertas, k)
assert red.ranking(0) == []
# Cierres y reaperturas.
top = red.ranking(3)[0][0]
red.cerrar(top); abiertas.discard(top)
assert red.ranking(10) == esperado(totales, abiertas, 10) and top not in [n for n, _ in red.ranking(147)]
red.deshacer(); abiertas.add(top)
assert red.ranking(10) == esperado(totales, abiertas, 10)
# Editar una ruta cambia los buses de esa estación.
r = "1-1"; e = red.recorrido(r)[1]
red.quitar_parada(r, e); totales[e] -= por_par[(e, r)]
assert red.ranking(147) == esperado(totales, abiertas, 147)
red.deshacer(); totales[e] += por_par[(e, r)]
assert red.ranking(147) == esperado(totales, abiertas, 147)
print("ok  R6 ranking: igual a ordenar todo (k varios), con cierres, deshacer y edición de ruta")
