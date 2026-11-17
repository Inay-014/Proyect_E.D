"""R3: rango(desde, hasta): todas las estaciones abiertas entre dos nombres
(ambos extremos incluidos, existan o no como estacion), en orden alfabetico.

Estructura: la misma de R2 (IndiceAbiertas).
Algoritmo: busqueda binaria de 'desde', salto a la primera abierta y recorrido por la
lista enlazada hasta pasar 'hasta'. Si desde > hasta, el resultado es vacio.
Alternativa descartada: filtrar todas las estaciones cada vez (O(n) aunque el rango
sea pequeno).
O grande: O(log n + m). n = numero de estaciones; m = estaciones en el rango.
"""


def rango(indice, desde, hasta):
    resultado = []
    i = indice.primera_abierta_desde(indice.cota_inferior(desde))
    while i < indice.n and indice.nombres[i] <= hasta:
        resultado.append(indice.nombres[i])
        i = indice.sig[i]
    return resultado
