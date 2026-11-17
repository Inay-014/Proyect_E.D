"""Prueba R2 (autocompletar) por separado."""
from _comun import *

def comparar(red, nombres, semilla, cerrar_prob):
    rng = random.Random(semilla)
    abiertas = {n: True for n in nombres}
    for _ in range(400):
        n = rng.choice(nombres)
        if rng.random() < cerrar_prob:
            red.cerrar(n); abiertas[n] = False
        else:
            red.reabrir(n); abiertas[n] = True
        base = rng.choice(nombres)
        pref = base[:rng.randint(0, 5)] if rng.random() < .8 else rng.choice(["ZZ", "9", "CAL", "A"])
        k = rng.randint(0, 9)
        esperado = [x for x in sorted(nombres) if abiertas[x] and x.startswith(pref)][:k]
        assert red.autocompletar(pref, k) == esperado, (pref, k)

red = red_real()
nombres = [f[0] for f in filas("estaciones.csv")]
assert red.autocompletar("CAL", 3) == [x for x in sorted(nombres) if x.startswith("CAL")][:3]
assert red.autocompletar("CAL", 0) == [] and red.autocompletar("QQQ", 5) == []
assert red.autocompletar("", 2) == sorted(nombres)[:2]
comparar(red, nombres, 1, .5)
comparar(red_real(), nombres, 2, .9)   # casi todo cerrado: el caso malo para "saltar cerradas"
print("ok  R2 autocompletar: igual a fuerza bruta con 800 cambios al azar (incluye casi todo cerrado)")
