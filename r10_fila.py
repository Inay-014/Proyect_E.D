"""R10: simular_fila(llegadas, frecuencia, capacidad).

Recibe tiempos de llegada y frecuencia en segundos y devuelve una lista con el segundo
de salida asignado a cada persona, en el mismo orden de entrada. Los buses salen en
frecuencia, 2 * frecuencia, ... y embarcan hasta 'capacidad' personas en orden de llegada.
Una llegada exactamente a la hora de salida puede abordar ese bus si hay cupo.
Si las llegadas ya están ordenadas el costo es O(n + b log c); en otro caso ordenar
requiere O(n log n), más O(b log c) para asignar buses. n = pasajeros, b = buses usados,
c = capacidad.
"""
from .ordenar import merge_sort


def _por_llegada(persona):
    return persona[0]


def simular_fila(llegadas, frecuencia, capacidad):
    if frecuencia <= 0:
        raise ValueError("La frecuencia debe ser mayor que 0")
    if capacidad < 1:
        raise ValueError("La capacidad debe ser al menos 1")
    n = len(llegadas)
    if n == 0:
        return []

    personas = []
    ordenadas = True
    for i in range(n):
        personas.append((llegadas[i], i))
        if i > 0 and llegadas[i] < llegadas[i - 1]:
            ordenadas = False
    if not ordenadas:
        personas = merge_sort(personas, _por_llegada)

    salidas = [0] * n
    i = 0
    numero_bus = 1
    while i < n:
        salida = numero_bus * frecuencia
        if personas[i][0] > salida:
            numero_bus = int(personas[i][0] // frecuencia)
            if numero_bus * frecuencia < personas[i][0]:
                numero_bus += 1
            if numero_bus < 1:
                numero_bus = 1
            salida = numero_bus * frecuencia

        tope = i + capacidad
        if tope > n:
            tope = n
        lo = i + 1
        hi = tope
        while lo < hi:
            medio = (lo + hi) // 2
            if personas[medio][0] <= salida:
                lo = medio + 1
            else:
                hi = medio

        while i < lo:
            salidas[personas[i][1]] = salida
            i += 1
        numero_bus += 1

    return salidas
