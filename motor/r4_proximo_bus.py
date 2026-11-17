"""R4: proximo_bus(estacion, ruta, hora): hora a la que pasa el siguiente bus de esa ruta.

Estructura: TablaHash propia estacion -> TablaHash ruta -> arreglo de minutos ORDENADO.
Algoritmo: busqueda binaria de la primera salida >= hora (si pasa justo a esa hora,
ese es el siguiente). Si ya no hay mas buses ese dia, None.
El arreglo se ordena al cargar con merge sort propio, pero solo si hace falta (se
verifica en una pasada O(h) si ya viene ordenado).
Alternativa descartada: recorrer los horarios uno por uno (O(h)); con cientos de
buses al dia por estacion es lo que el enunciado pide evitar.
O grande: O(log h) por consulta; h = buses al dia de esa ruta en esa estacion.
Extra para la app: siguientes() devuelve hasta n salidas seguidas (busqueda binaria + un
corte de la lista): O(log h + n).
Carga: O(N) si ya vienen ordenados, O(N log h) si no; N = filas de horarios.csv.
Horas como 25:10 se guardan como 1510 minutos (ver tiempo.py).
"""
from .ordenar import merge_sort


def _esta_ordenada(lista):
    for i in range(1, len(lista)):
        if lista[i] < lista[i - 1]:
            return False
    return True


class Horarios:
    def __init__(self, datos):
        """datos: TablaHash estacion -> TablaHash ruta -> lista de minutos (en cualquier orden)."""
        self.datos = datos
        for estacion in datos:
            por_ruta = datos[estacion]
            for ruta in por_ruta:
                lista = por_ruta[ruta]
                if not _esta_ordenada(lista):
                    por_ruta[ruta] = merge_sort(lista)

    def cantidad(self, estacion, ruta):
        """Cuantos buses de la ruta pasan por la estacion en el dia. O(1)."""
        por_ruta = self.datos.get(estacion)
        if por_ruta is None:
            return 0
        lista = por_ruta.get(ruta)
        return 0 if lista is None else len(lista)

    def total_filas(self):
        total = 0
        for estacion in self.datos:
            for ruta in self.datos[estacion]:
                total += len(self.datos[estacion][ruta])
        return total

    def _primera_desde(self, estacion, ruta, minutos):
        """(lista, posicion de la primera salida >= minutos) o (None, 0). O(log h)."""
        por_ruta = self.datos.get(estacion)
        if por_ruta is None:
            return None, 0
        lista = por_ruta.get(ruta)
        if lista is None:
            return None, 0
        lo = 0
        hi = len(lista)
        while lo < hi:
            medio = (lo + hi) // 2
            if lista[medio] < minutos:
                lo = medio + 1
            else:
                hi = medio
        return lista, lo

    def siguiente(self, estacion, ruta, minutos):
        """Minutos de la primera salida >= 'minutos', o None. O(log h)."""
        lista, lo = self._primera_desde(estacion, ruta, minutos)
        if lista is None:
            return None
        return lista[lo] if lo < len(lista) else None

    def siguientes(self, estacion, ruta, minutos, n):
        """Hasta n salidas (en minutos) a partir de 'minutos', en orden. Menos si ya no
        quedan buses ese dia. O(log h + n)."""
        lista, lo = self._primera_desde(estacion, ruta, minutos)
        if lista is None or n <= 0:
            return []
        return lista[lo:lo + n]

    def extremos(self, estacion, ruta):
        """(primera salida, ultima salida, cantidad) de la ruta en la estacion, en minutos;
        None si no hay horarios. El arreglo esta ordenado: son sus dos puntas. O(1)."""
        por_ruta = self.datos.get(estacion)
        if por_ruta is None:
            return None
        lista = por_ruta.get(ruta)
        if lista is None or len(lista) == 0:
            return None
        return lista[0], lista[len(lista) - 1], len(lista)
