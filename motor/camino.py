"""Extra para la app (tarjeta 'Estaciones abiertas'): el recorrido con la MENOR cantidad de
estaciones entre dos estaciones, sin limite de transbordos. No es parte del contrato; R5
(viaje, maximo un transbordo) queda intacto en r5_viaje.py.

Modelo: un grafo dirigido. Nodos = estaciones abiertas. Hay arista X -> Y si alguna ruta
para en X y su siguiente parada ABIERTA es Y (en una cerrada el bus pasa de largo, asi que
no cuenta como estacion del recorrido). El grafo no se construye aparte: los vecinos de X
se sacan del indice 'pasan' (rutas que paran en X) y de la lista enlazada de cada ruta.
Estructuras: cola (una lista + un indice 'cabeza': sacar es avanzar el indice, O(1), nunca
pop(0)) y una TablaHash propia estacion -> (de donde vine, en que ruta).
Algoritmo: busqueda en anchura (BFS). Como todas las aristas valen 1, la primera vez que
BFS llega a una estacion lo hace por el camino con menos estaciones; al llegar al destino
se para y se reconstruye el camino hacia atras con la tabla.
Detalle: al expandir una estacion se prueba primero la ruta en la que se llego, para no
cambiar de bus sin necesidad cuando hay empate.
Alternativas descartadas: Dijkstra (todas las aristas pesan lo mismo; ademas necesita un
heap); busqueda en profundidad (encuentra UN camino, no el mas corto).
O grande: O(V + E). V = estaciones, E = suma de (rutas que paran en cada estacion).
"""
from .tabla_hash import TablaHash


def _siguiente_abierta(nodo, tabla):
    """Siguiente nodo de la ruta cuya estacion esta abierta (None si se acaba la ruta)."""
    nodo = nodo.sig
    while nodo is not None and not tabla.esta_abierta(nodo.estacion):
        nodo = nodo.sig
    return nodo


def camino_minimo(rutas, tabla, origen, destino):
    """Lista de (estacion, abierta, ruta) del origen al destino con la menor cantidad de
    estaciones; 'ruta' es la ruta en la que se LLEGA (None en el origen). Las cerradas por
    las que el bus pasa de largo van incluidas con abierta=False. None si no hay camino."""
    if not tabla.esta_abierta(origen) or not tabla.esta_abierta(destino):
        return None
    if origen == destino:
        return [(origen, True, None)]
    previo = TablaHash()                  # estacion -> (estacion anterior, ruta usada)
    previo[origen] = (None, None)
    cola = [origen]
    cabeza = 0
    while cabeza < len(cola) and destino not in previo:
        actual = cola[cabeza]
        cabeza += 1
        rutas_aqui = rutas.pasan.get(actual)
        if rutas_aqui is None:
            continue
        orden = []                        # primero la ruta en la que se llego
        llegue_en = previo[actual][1]
        if llegue_en is not None and llegue_en in rutas_aqui:
            orden.append(llegue_en)
        for ruta in rutas_aqui:
            if ruta != llegue_en:
                orden.append(ruta)
        for ruta in orden:
            nodo = _siguiente_abierta(rutas.recorridos[ruta].nodos[actual], tabla)
            if nodo is not None and nodo.estacion not in previo:
                previo[nodo.estacion] = (actual, ruta)
                cola.append(nodo.estacion)
    if destino not in previo:
        return None
    # Reconstruir de atras hacia adelante y luego invertir a mano.
    saltos = []
    est = destino
    while est != origen:
        anterior, ruta = previo[est]
        saltos.append((anterior, est, ruta))
        est = anterior
    resultado = [(origen, True, None)]
    for i in range(len(saltos) - 1, -1, -1):
        desde, hasta, ruta = saltos[i]
        nodo = rutas.recorridos[ruta].nodos[desde].sig
        while nodo is not None:           # incluye las cerradas que el bus pasa de largo
            resultado.append((nodo.estacion, tabla.esta_abierta(nodo.estacion), ruta))
            if nodo.estacion == hasta:
                break
            nodo = nodo.sig
    return resultado
