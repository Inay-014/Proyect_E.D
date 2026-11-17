"""Ordenamiento propio del motor: merge sort.

Por que merge sort: es O(n log n) en el peor caso (no depende de como vengan
los datos) y es estable (los empates conservan su orden original). Las pruebas
del profesor usan una red mucho mas grande, asi que un peor caso cuadratico
seria peligroso.
"""


def _mezclar(izq, der, clave):
    """Mezcla dos listas ya ordenadas en una sola. O(len(izq) + len(der))."""
    resultado = []
    i = 0
    j = 0
    n_izq = len(izq)
    n_der = len(der)
    if clave is None:
        while i < n_izq and j < n_der:
            # Solo toma de la derecha si es estrictamente menor: asi es estable.
            if der[j] < izq[i]:
                resultado.append(der[j])
                j += 1
            else:
                resultado.append(izq[i])
                i += 1
    else:
        while i < n_izq and j < n_der:
            if clave(der[j]) < clave(izq[i]):
                resultado.append(der[j])
                j += 1
            else:
                resultado.append(izq[i])
                i += 1
    while i < n_izq:
        resultado.append(izq[i])
        i += 1
    while j < n_der:
        resultado.append(der[j])
        j += 1
    return resultado


def merge_sort(lista, clave=None):
    """Devuelve una lista NUEVA ordenada de menor a mayor. No modifica la original.

    clave: funcion opcional que, dado un elemento, devuelve el valor por el que
    se compara. Tiempo O(n log n), memoria O(n), n = len(lista).
    """
    n = len(lista)
    if n <= 1:
        return lista[:]
    medio = n // 2
    izq = merge_sort(lista[:medio], clave)
    der = merge_sort(lista[medio:], clave)
    return _mezclar(izq, der, clave)
