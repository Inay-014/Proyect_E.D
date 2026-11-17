"""Prueba R5 (viaje) por separado: compara con una búsqueda de fuerza bruta."""
from _comun import *

# Casos a mano.
red = red_a_mano({"A": ["S1", "S2", "S3"], "B": ["S2", "S4"]})
v = red.viaje("S1", "S4")
assert v == [("A", "S1", "S2"), ("B", "S2", "S4")]
assert red.viaje("S1", "S3") == [("A", "S1", "S3")]
assert red.viaje("S4", "S1") is None, "las rutas van en un solo sentido"
assert red.viaje("S1", "S1") == []
assert red.viaje("S1", "NO") is None
red.cerrar("S2")
assert red.viaje("S1", "S4") is None, "no se puede transbordar en una cerrada"
assert red.viaje("S1", "S3") == [("A", "S1", "S3")], "una cerrada no cuenta como parada"
red.reabrir("S2"); red.cerrar("S1")
assert red.viaje("S1", "S3") is None, "nadie sube en una cerrada"

# Redes aleatorias con cierres al azar.
for semilla in range(300):
    red, mod = red_aleatoria(semilla)
    rng = random.Random(semilla)
    abiertas = set(mod["nombres"])
    for n in rng.sample(mod["nombres"], rng.randint(0, 4)):
        red.cerrar(n); abiertas.discard(n)
    for o in mod["nombres"]:
        for d in mod["nombres"]:
            esperado = mejor_bruto(mod["rutas"], abiertas, o, d)
            v = red.viaje(o, d)
            if esperado is None:
                assert v is None, (semilla, o, d, v)
            else:
                assert v is not None and paradas_viaje(v, mod["rutas"], abiertas) == esperado, (semilla, o, d, v, esperado)
                if o != d:
                    validar_viaje(v, mod["rutas"], abiertas, o, d)

# Red real: 150 pares al azar.
red = red_real()
rutas = {r: red.recorrido(r) for r in red.rutas.recorridos}
abiertas = set(f[0] for f in filas("estaciones.csv"))
rng = random.Random(4)
for _ in range(150):
    o, d = rng.choice(sorted(abiertas)), rng.choice(sorted(abiertas))
    esperado = mejor_bruto(rutas, abiertas, o, d)
    v = red.viaje(o, d)
    assert (v is None) == (esperado is None) and (v is None or paradas_viaje(v, rutas, abiertas) == esperado), (o, d)
    if v and o != d:
        validar_viaje(v, rutas, abiertas, o, d)
print("ok  R5 viaje: igual a fuerza bruta en 300 redes al azar y 150 pares reales; cerradas respetadas")
