"""R5: viaje(origen, destino): viaje directo o con UN solo transbordo, el que pase por
menos paradas: que ruta tomar, donde bajarse y donde cambiar.

Estructura: los recorridos enlazados (R7) + el indice 'pasan' (que rutas pasan por
cada estacion) + tabla hash propia de alcance.
Algoritmo (dos barridos, sin recorrer toda la red):
  1) Desde el origen, por cada ruta que pasa por el, avanzar por la lista enlazada y
     anotar en una tabla hash, para cada estacion abierta alcanzada, cuantas paradas cuesta
     llegar (y con que ruta). Si aparece el destino, es un viaje directo candidato.
  2) Desde el destino, por cada ruta que pasa por el, retroceder; cada estacion que
     ya este en la tabla es un transbordo candidato (total = ida + vuelta, rutas distintas).
  Gana el de menos paradas; en empate, el directo.
Se cuenta como parada cada estacion ABIERTA en la que el bus se detiene (llegada incluida);
las cerradas se pasan de largo y en ellas nadie sube, baja ni transborda. (SUPUESTO.)
Alternativa descartada: BFS sobre un grafo de estaciones (no distingue la ruta, y para
este problema el transbordo unico no lo necesita); probar todos los pares de rutas (O(R^2)).
O grande: O(L), L = suma de paradas de las rutas que pasan por origen y destino.
Retorna None si no hay viaje; si origen == destino, retorna [] (viaje sin tramos); en otro
caso retorna una lista de tramos (ruta, sube_en, baja_en).
"""


from .tabla_hash import TablaHash


def planear(rutas, tabla, origen, destino):
    if not tabla.esta_abierta(origen) or not tabla.esta_abierta(destino):
        return None
    if origen == destino:
        return []

    # 1) Hacia adelante desde el origen.
    alcance = TablaHash()
    mejor_directo = None
    desde_origen = rutas.pasan.get(origen)
    if desde_origen is not None:
        for ruta in desde_origen:
            nodo = rutas.recorridos[ruta].nodos[origen].sig
            paradas = 0
            while nodo is not None:
                est = nodo.estacion
                if tabla.esta_abierta(est):
                    paradas += 1
                    if est == destino:
                        if mejor_directo is None or paradas < mejor_directo[0]:
                            mejor_directo = (paradas, ruta)
                    elif est not in alcance or paradas < alcance[est][0]:
                        alcance[est] = (paradas, ruta)
                nodo = nodo.sig

    # 2) Hacia atras desde el destino, buscando donde cambiar.
    mejor = None
    hacia_destino = rutas.pasan.get(destino)
    if hacia_destino is not None:
        for ruta2 in hacia_destino:
            nodo = rutas.recorridos[ruta2].nodos[destino].ant
            paradas2 = 1
            while nodo is not None:
                est = nodo.estacion
                if tabla.esta_abierta(est):
                    if est in alcance and alcance[est][1] != ruta2:
                        total = alcance[est][0] + paradas2
                        if mejor is None or total < mejor[0]:
                            mejor = (total, est, alcance[est][1], alcance[est][0], ruta2, paradas2)
                    paradas2 += 1
                nodo = nodo.ant

    if mejor_directo is not None and (mejor is None or mejor_directo[0] <= mejor[0]):
        paradas, ruta = mejor_directo
        return [(ruta, origen, destino)]
    if mejor is not None:
        total, t, r1, p1, r2, p2 = mejor
        return [(r1, origen, t), (r2, t, destino)]
    return None


def estaciones_del_viaje(rutas, tabla, viaje):
    """Extra para la app: TODAS las estaciones por las que pasa un viaje ya planeado, en
    orden, cada una con su estado. Devuelve lista de (estacion, abierta, ruta); 'ruta' es
    la ruta en la que se LLEGA a esa estacion (None para el origen).
    Las cerradas tambien salen (el bus pasa de largo por ellas): por eso se camina la lista
    enlazada de cada tramo desde 'desde' hasta 'hasta'. O(p), p = paradas recorridas.
    """
    resultado = []
    if viaje is None:
        return resultado
    tramos = viaje
    if len(tramos) == 0:
        return resultado
    origen = tramos[0][1]
    resultado.append((origen, tabla.esta_abierta(origen), None))
    for tramo in tramos:
        ruta, desde, hasta = tramo
        nodo = rutas.recorridos[ruta].nodos[desde].sig
        while nodo is not None:
            est = nodo.estacion
            resultado.append((est, tabla.esta_abierta(est), ruta))
            if est == hasta:
                break
            nodo = nodo.sig
    return resultado
