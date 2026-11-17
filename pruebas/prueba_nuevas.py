"""TablaHash propia (contra un dict de Python, que aqui SI se puede usar: es una prueba) y los
extras nuevos del motor: camino(), rutas_en(), todas(). Corre: python pruebas/prueba_nuevas.py"""
import random

from _comun import red_real, filas, mins
from motor.tabla_hash import TablaHash

rng = random.Random(7)
t, d = TablaHash(), {}
for paso in range(40000):
    k = "E%d" % rng.randint(0, 600)
    op = rng.random()
    if op < .55:
        v = rng.randint(0, 9); t[k] = v; d[k] = v
    elif op < .8:
        assert (k in t) == (k in d) and t.get(k) == d.get(k)
    elif k in d:
        del t[k]; del d[k]
    else:
        try:
            del t[k]; raise AssertionError("debia fallar")
        except KeyError:
            pass
    if paso % 997 == 0:
        assert len(t) == len(d) and list(t) == list(d) and t.values() == list(d.values())   # mismo orden de insercion

red = red_real()
estaciones = [f[0] for f in filas("estaciones.csv")]
assert red.todas() == [(n, True) for n in sorted(estaciones)]
horas = {}
for ruta, est, h in filas("horarios.csv"):
    horas.setdefault((est, ruta), []).append(mins(h))
for est in rng.sample(estaciones, 40):
    esperado = sorted((r, min(v), max(v), len(v)) for (e, r), v in horas.items() if e == est and red.rutas.pasa(e, r))
    obtenido = [(r, mins(a), mins(b), n) for r, a, b, n in red.rutas_en(est) if n]
    assert obtenido == esperado, est
# camino(): contra un BFS de fuerza bruta escrito con dict y deque (aqui si se puede).
from collections import deque
def minimo(o, f, cerradas=()):
    grafo = {}
    for ruta in {r for r, _, _ in filas("rutas.csv")}:
        paradas = [e for e in red.recorrido(ruta) if e not in cerradas]
        for a, b in zip(paradas, paradas[1:]):
            grafo.setdefault(a, set()).add(b)
    dist, cola = {o: 0}, deque([o])
    while cola:
        x = cola.popleft()
        for y in grafo.get(x, ()):
            if y not in dist:
                dist[y] = dist[x] + 1; cola.append(y)
    return dist.get(f)
for _ in range(300):
    o, f = rng.sample(estaciones, 2)
    v, c, m = red.viaje(o, f), red.camino(o, f), minimo(o, f)
    assert (c is None) == (m is None)
    if c:
        assert c[0][0] == o and c[-1][0] == f and len(c) - 1 == m and all(a for _, a, _ in c)
        if v is not None:
            paradas_r5 = 0
            for ruta, desde, hasta in v:
                rec = red.recorrido(ruta)
                i, j = rec.index(desde), rec.index(hasta)
                paradas_r5 += sum(1 for n in rec[i + 1:j + 1] if red.estado(n) == "ABIERTA")
            assert m <= paradas_r5                # nunca peor que el viaje de R5
        for (a, _, _), (b, _, r) in zip(c, c[1:]):      # cada salto es una parada real de esa ruta
            rec = red.recorrido(r); assert rec[rec.index(a) + 1] == b
red.cerrar("CALLE 72")
assert red.rutas_en("CALLE 72") == [] and ("CALLE 72", False) in red.todas()
c = red.camino("PORTAL NORTE", "AV. JIMENEZ")
assert c and all(n != "CALLE 72" or not a for n, a, _ in c)
assert sum(1 for _, a, _ in c if a) - 1 == minimo("PORTAL NORTE", "AV. JIMENEZ", ("CALLE 72",))
assert red.camino("CALLE 72", "AV. JIMENEZ") is None and red.camino("AGUAS", "AGUAS") == [("AGUAS", True, None)]
print("ok  TablaHash = dict en 40.000 operaciones (orden incluido); camino (minimo de estaciones), rutas_en y todas correctos")
