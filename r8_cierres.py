"""R8: cerrar y reabrir estaciones.

Una estacion cerrada no aparece en busquedas, autocompletado, rangos ni ranking, y nadie
sube, baja ni transborda ahi. No se borra nada: se cambia una bandera y se avisa a las
estructuras que dependen de ella:
  tabla (R1): bandera; indice (R2/R3): se quita o se vuelve a poner en la lista de abiertas;
  ranking (R6): se invalida el cache; viaje (R5) y proximo_bus (R4) consultan la bandera.
Alternativa descartada: borrar la estacion de todas las estructuras (reabrir seria
reconstruir todo y perderia su lugar).
O grande: O(log n) por el indice (Fenwick). n = numero de estaciones.
Devuelven True si hubo cambio, False si ya estaba asi.
"""


def cerrar_estacion(tabla, indice, ranking, nombre):
    if not tabla.existe(nombre):
        return False
    if not tabla.esta_abierta(nombre):
        return False
    tabla.fijar_abierta(nombre, False)
    indice.cerrar(nombre)
    ranking.actualizar(nombre)
    return True


def abrir_estacion(tabla, indice, ranking, nombre):
    if not tabla.existe(nombre):
        return False
    if tabla.esta_abierta(nombre):
        return False
    tabla.fijar_abierta(nombre, True)
    indice.abrir(nombre)
    ranking.actualizar(nombre)
    return True
