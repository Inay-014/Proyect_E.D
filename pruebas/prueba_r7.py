"""Prueba R7 (editar rutas y recorrido) por separado."""
from _comun import *

red = red_a_mano({"A": ["S1", "S2", "S3"], "B": ["S2", "S4"]})
assert red.recorrido("A") == ["S1", "S2", "S3"] and red.recorrido("A", al_reves=True) == ["S3", "S2", "S1"]
red.agregar_parada("A", "S4", "S2")
assert red.recorrido("A") == ["S1", "S2", "S4", "S3"]
red.quitar_parada("A", "S1")
assert red.recorrido("A") == ["S2", "S4", "S3"] and red.recorrido("A", True) == ["S3", "S4", "S2"]
assert red.agregar_parada("A", "S4", "S2") is False       # ya pasa por ahí
assert red.agregar_parada("A", "NO", "S2") is False       # estación inexistente
assert red.agregar_parada("A", "S1", "S9") is False       # referencia no presente
assert red.agregar_parada("ZZ", "S1", "S2") is False      # ruta inexistente
assert red.quitar_parada("A", "S1") is False               # ya no está
assert red.recorrido("ZZ") == []

# Contra un modelo (lista de Python) con operaciones al azar.
for semilla in range(100):
    red, mod = red_aleatoria(semilla)
    rng = random.Random(semilla)
    modelo = {r: list(l) for r, l in mod["rutas"].items()}
    for _ in range(60):
        r = rng.choice(list(modelo))
        if rng.random() < .5 and len(modelo[r]) > 1:
            e = rng.choice(modelo[r]); red.quitar_parada(r, e); modelo[r].remove(e)
        else:
            libres = [n for n in mod["nombres"] if n not in modelo[r]]
            if libres and modelo[r]:
                n, ref = rng.choice(libres), rng.choice(modelo[r])
                red.agregar_parada(r, n, ref); modelo[r].insert(modelo[r].index(ref) + 1, n)
        for rr in modelo:
            assert red.recorrido(rr) == modelo[rr]
            assert red.recorrido(rr, al_reves=True) == modelo[rr][::-1]
print("ok  R7 rutas: agregar/quitar/recorrido iguales a un modelo con listas (100 redes), errores validados")
