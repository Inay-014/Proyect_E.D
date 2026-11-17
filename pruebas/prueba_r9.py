"""Prueba R9 (deshacer y rehacer) por separado, con operaciones al azar."""
from _comun import *

def foto(red, nombres):
    return (tuple(n for n in nombres if red.estado(n) == "CERRADA"),
            tuple((r, tuple(red.recorrido(r))) for r in sorted(red.rutas.recorridos)),
            tuple(red.ranking(len(nombres))), tuple(red.rango("", "~")))

red = red_a_mano({"A": ["S1", "S2"]})
assert red.deshacer() is False and red.rehacer() is False, "sin historial no hace nada"

for semilla in range(60):
    red, mod = red_aleatoria(semilla)
    nombres, rng = mod["nombres"], random.Random(semilla)
    fotos = [foto(red, nombres)]
    for _ in range(25):
        a = rng.random()
        r = rng.choice(list(mod["rutas"]))
        lista = red.recorrido(r)
        if a < .3:
            red.cerrar(rng.choice(nombres))
        elif a < .5:
            red.reabrir(rng.choice(nombres))
        elif a < .75 and len(lista) > 1:
            red.quitar_parada(r, rng.choice(lista))
        else:
            libres = [n for n in nombres if n not in lista]
            if libres and lista:
                red.agregar_parada(r, rng.choice(libres), rng.choice(lista))
        if foto(red, nombres) != fotos[-1]:
            fotos.append(foto(red, nombres))
    # Deshacer todo en orden inverso: cada paso vuelve a la foto anterior.
    for i in range(len(fotos) - 1, 0, -1):
        assert foto(red, nombres) == fotos[i]
        assert red.deshacer() is True
    assert foto(red, nombres) == fotos[0] and red.deshacer() is False
    # Rehacer todo: vuelve a las fotos en orden.
    for i in range(1, len(fotos)):
        assert red.rehacer() is True and foto(red, nombres) == fotos[i]
    assert red.rehacer() is False
    # Un cambio nuevo borra lo que había para rehacer.
    if len(fotos) > 2:
        red.deshacer(); red.deshacer()
        red.cerrar(nombres[0]) if red.estado(nombres[0]) == "ABIERTA" else red.reabrir(nombres[0])
        assert red.rehacer() is False
print("ok  R9 historial: deshacer/rehacer en orden con 60 secuencias al azar; un cambio nuevo borra rehacer")
