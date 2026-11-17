"""Prueba R3 (rango) por separado."""
from _comun import *

red = red_real()
nombres = [f[0] for f in filas("estaciones.csv")]
assert red.rango("CALLE 26", "CALLE 80") == [x for x in sorted(nombres) if "CALLE 26" <= x <= "CALLE 80"]
assert red.rango("CALLE 80", "CALLE 26") == []
rng = random.Random(5)
abiertas = {n: True for n in nombres}
for _ in range(500):
    n = rng.choice(nombres)
    if rng.random() < .55:
        red.cerrar(n); abiertas[n] = False
    else:
        red.reabrir(n); abiertas[n] = True
    a = rng.choice(nombres + ["", "ZZZZ", "CALLE 2", "0"]); b = rng.choice(nombres + ["", "ZZZZ", "CALLE 9", "0"])
    esperado = [x for x in sorted(nombres) if abiertas[x] and a <= x <= b]
    assert red.rango(a, b) == esperado, (a, b)
print("ok  R3 rango: igual a fuerza bruta (extremos inexistentes, desde>hasta, cierres al azar)")
