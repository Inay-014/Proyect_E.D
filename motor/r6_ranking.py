"""R6: ranking(k) de estaciones abiertas por buses diarios.

Estructura: lista ordenada en cache.
La cache se invalida cuando una estacion cambia.

Complejidades:
- Invalidar o actualizar: O(1).
- Consultar con cache valida: O(k).
- Reconstruir la cache: O(n log n).

n = estaciones; k = resultados solicitados.
Empates: nombre alfabetico.
"""
from .ordenar import merge_sort
from .tabla_hash import TablaHash


def _clave(par):
    return (-par[1], par[0])


class Ranking:
    def __init__(self, nombres_ordenados, rutas, tabla):
        self.nombres = nombres_ordenados
        self.rutas = rutas
        self.tabla = tabla
        self.sucio = True
        self.lista = []
        self.posiciones = TablaHash()

    def invalidar(self):
        self.sucio = True

    def actualizar(self, nombre):
        """Invalida el cache del ranking. O(1)."""
        self.sucio = True

    def top(self, k):
        if k <= 0:
            return []
        if self.sucio:
            self._recalcular()
        return self.lista[:k]

    def _recalcular(self):
        totales = self.rutas.total
        abiertas = []
        for nombre in self.nombres:
            if self.tabla.esta_abierta(nombre):
                abiertas.append((nombre, totales.get(nombre, 0)))
        self.lista = merge_sort(abiertas, _clave)
        self.posiciones = TablaHash()
        for par in self.lista:
            self.posiciones[par[0]] = par
        self.sucio = False
