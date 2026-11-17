"""Prueba R4 (proximo_bus) por separado."""
from _comun import *

# Real: contra recorrer todo el CSV.
red = red_real()
modelo = {}
for r, e, h in filas("horarios.csv"):
    modelo.setdefault((e, r), []).append(mins(h))
rng = random.Random(9)
claves = list(modelo)
for _ in range(2000):
    e, r = rng.choice(claves)
    m = rng.randint(0, 1500)
    futuros = [x for x in modelo[(e, r)] if x >= m]
    esperado = hhmm(min(futuros)) if futuros else None
    assert red.proximo_bus(e, r, hhmm(m)) == esperado, (e, r, m)
    assert red.proximo_bus(e, r, m) == esperado, "también acepta minutos"
assert red.proximo_bus("UNIVERSIDADES", "NO-RUTA", "10:00") is None
assert red.proximo_bus("NO EXISTE", "1-1", "10:00") is None
assert red.proximo_bus("UNIVERSIDADES", "1-1", "23:59") in (None, "23:59")

# Sintetica: horarios desordenados y horas pasadas de 24 (25:10).
for semilla in range(30):
    red2, mod = red_aleatoria(semilla)
    for (e, r), lista in mod["horas"].items():
        for m in (0, 400, 900, 1500, 1561):
            fut = [x for x in lista if x >= m]
            assert red2.proximo_bus(e, r, m) == (hhmm(min(fut)) if fut else None)
# Estación cerrada o ruta que ya no pasa por ahí: None.
red.cerrar("UNIVERSIDADES"); assert red.proximo_bus("UNIVERSIDADES", "1-1", "00:00") is None
red.reabrir("UNIVERSIDADES"); assert red.proximo_bus("UNIVERSIDADES", "1-1", "00:00") is not None
red.quitar_parada("1-1", "UNIVERSIDADES"); assert red.proximo_bus("UNIVERSIDADES", "1-1", "00:00") is None
print("ok  R4 proximo_bus: igual a recorrer el CSV (2000 consultas), horarios desordenados, horas >24, cerrada/quitada")
