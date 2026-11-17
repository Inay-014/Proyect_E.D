"""R6: ranking(k): estaciones abiertas ordenadas por buses al dia (descendente).

Estructura: lista ordenada en cache y TablaHash nombre -> tupla actual de ranking.
Al cerrar/reabrir una estacion o editar una ruta, se quita y reinserta solo esa estacion.
La busqueda de posicion es binaria; el desplazamiento de la lista cuesta O(n). Se ordena
todo con merge sort O(n log n) solo al construir la cache por primera vez.
Alternativa descartada: invalidar y ordenar toda la lista tras cada cambio (O(n log n)), o
recalcular en cada consulta. Una lista enlazada evita desplazar elementos, pero encontrar
la posicion correcta cuesta O(n) y hace mas compleja la consulta del top k.
O grande: top(k) O(k); actualizar una estacion O(n); crear la cache O(n log n).
n = estaciones; k = resultados solicitados. Empates: nombre alfabetico.
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
        # Se conserva para cambios masivos; las operaciones normales usan actualizar().
        self.sucio = True

    def actualizar(self, nombre):
        """Reposiciona una estacion tras un cambio de estado o de buses. O(n)."""
        if self.sucio:
            return

        if nombre in self.posiciones:
            anterior = self.posiciones[nombre]
            i = self._buscar(_clave(anterior))
            if i < len(self.lista) and self.lista[i] == anterior:
                self.lista.pop(i)
            del self.posiciones[nombre]

        if self.tabla.esta_abierta(nombre):
            nuevo = (nombre, self.rutas.total.get(nombre, 0))
            i = self._buscar(_clave(nuevo))
            self.lista.insert(i, nuevo)
            self.posiciones[nombre] = nuevo

    def _buscar(self, clave):
        """Primera posicion cuyo par tiene clave >= clave. Busqueda O(log n)."""
        lo = 0
        hi = len(self.lista)
        while lo < hi:
            medio = (lo + hi) // 2
            if _clave(self.lista[medio]) < clave:
                lo = medio + 1
            else:
                hi = medio
        return lo

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
