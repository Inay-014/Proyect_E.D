"""R2: autocompletar(prefijo, k): hasta k estaciones abiertas que empiezan por el
texto, en orden alfabetico.

Estructura: IndiceAbiertas (arreglo ordenado + Fenwick + lista enlazada de abiertas).
Algoritmo: busqueda binaria del prefijo (las que lo comparten quedan contiguas), saltar
a la primera ABIERTA y avanzar por la lista enlazada hasta k o hasta que el nombre
deje de empezar por el prefijo.
Alternativa descartada: trie (mas memoria y hay que llevar conteo de abiertas por
nodo); recorrer el arreglo saltando cerradas (O(n) en el peor caso).
O grande: O(log n + k). n = numero de estaciones; k = lo pedido.
"""


def autocompletar(indice, prefijo, k):
    resultado = []
    if k <= 0:
        return resultado
    i = indice.primera_abierta_desde(indice.cota_inferior(prefijo))
    while i < indice.n and len(resultado) < k:
        nombre = indice.nombres[i]
        if not nombre.startswith(prefijo):
            break
        resultado.append(nombre)
        i = indice.sig[i]
    return resultado
