"""Prueba R8 (cerrar y reabrir) por separado: la estación cerrada desaparece de TODO."""
from _comun import *

red = red_real()
n = "CALLE 26"
assert red.cerrar(n) is True and red.cerrar(n) is False, "cerrar dos veces no cambia nada"
assert n not in red.autocompletar("CALLE 2", 50)
assert n not in red.rango("CALLE 2", "CALLE 3")
assert n not in [x for x, _ in red.ranking(147)]
assert red.estado(n) == "CERRADA"
assert red.viaje(n, "PORTAL SUR") is None and red.viaje("PORTAL SUR", n) is None
ruta = next(r for r in red.rutas.recorridos if n in red.recorrido(r))
assert red.proximo_bus(n, ruta, "00:00") is None
for o in ("PORTAL NORTE", "PORTAL SUR", "UNIVERSIDADES"):
    for d in ("PORTAL SUR", "AV. CHILE", "RICAURTE"):
        v = red.viaje(o, d)
        if v:
            assert all(t[1] != n and t[2] != n for t in v)
assert red.reabrir(n) is True and red.reabrir(n) is False
assert n in red.autocompletar("CALLE 2", 50) and n in red.rango("CALLE 2", "CALLE 3")
assert n in [x for x, _ in red.ranking(147)] and red.proximo_bus(n, ruta, "00:00") is not None
assert red.cerrar("NO EXISTE") is False
print("ok  R8 cierres: la cerrada desaparece de búsquedas, rangos, ranking, horarios y viajes; reabrir la devuelve")
