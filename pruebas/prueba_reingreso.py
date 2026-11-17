"""Regresion: quitar/agregar una parada no altera el conteo original de buses."""
from _comun import red_real

red = red_real()
ruta = '5-3'
paradas = red.recorrido(ruta)
estacion, anterior = paradas[1], paradas[0]
antes = red.ranking(147)
assert red.quitar_parada(ruta, estacion)
assert red.agregar_parada(ruta, estacion, anterior)
assert red.ranking(147) == antes
assert red.deshacer() and red.deshacer()
assert red.ranking(147) == antes
assert red.rehacer() and red.rehacer()
assert red.ranking(147) == antes
print('OK: reingreso, deshacer y rehacer preservan el ranking')
