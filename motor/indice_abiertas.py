"""Indice ordenado de estaciones ABIERTAS. Lo usan R2 (autocompletar), R3 (rango) y R8.

El conjunto de estaciones no cambia (solo se abren y cierran), asi que:
  * 'nombres': arreglo ordenado alfabeticamente UNA vez (merge sort propio).
  * Busqueda binaria sobre ese arreglo para ubicar un texto: O(log n).
  * Arbol de Fenwick con 1 por cada estacion abierta: cuenta cuantas hay antes de una
    posicion y encuentra la k-esima abierta, ambas en O(log n); cerrar o abrir = O(log n).
  * Lista doblemente enlazada (arreglos sig/ant) SOLO entre las abiertas: despues de
    ubicar la primera, recorrer las siguientes cuesta O(1) cada una, sin saltar cerradas.
Por que no un arbol balanceado (AVL): aqui las claves son fijas; un AVL traeria
rotaciones y borrados complejos para lo mismo. Por que no solo arreglo + saltar
cerradas: si hay muchas cerradas seguidas, una consulta puede costar O(n).
"""


from .tabla_hash import TablaHash
class IndiceAbiertas:
    def __init__(self, nombres_ordenados):
        n = len(nombres_ordenados)
        self.nombres = nombres_ordenados
        self.n = n
        self.pos = TablaHash()
        for i in range(n):
            self.pos[nombres_ordenados[i]] = i
        self.abierta = [True] * n
        self.total = n
        # Fenwick (posiciones 1..n): con todo abierto, el nodo i guarda lowbit(i).
        self.arbol = [0] * (n + 1)
        for i in range(1, n + 1):
            self.arbol[i] = i & (-i)
        self.pot = 1
        while self.pot * 2 <= n:
            self.pot *= 2
        # Lista enlazada de abiertas: n significa "no hay siguiente", -1 "no hay anterior".
        self.sig = [i + 1 for i in range(n)]
        self.ant = [i - 1 for i in range(n)]

    # ---- Fenwick ----
    def _contar_antes(self, i):
        """Cuantas abiertas hay en las posiciones [0, i). O(log n)."""
        suma = 0
        while i > 0:
            suma += self.arbol[i]
            i -= i & (-i)
        return suma

    def _actualizar(self, i, delta):
        i += 1
        while i <= self.n:
            self.arbol[i] += delta
            i += i & (-i)

    def _seleccionar(self, k):
        """Posicion (desde 0) de la k-esima abierta, k desde 1. O(log n)."""
        pos = 0
        paso = self.pot
        while paso > 0:
            if pos + paso <= self.n and self.arbol[pos + paso] < k:
                pos += paso
                k -= self.arbol[pos]
            paso //= 2
        return pos

    # ---- consultas ----
    def cota_inferior(self, texto):
        """Primera posicion cuyo nombre es >= texto (n si ninguna). O(log n)."""
        lo = 0
        hi = self.n
        while lo < hi:
            medio = (lo + hi) // 2
            if self.nombres[medio] < texto:
                lo = medio + 1
            else:
                hi = medio
        return lo

    def primera_abierta_desde(self, i):
        """Posicion de la primera abierta en [i, n), o n si no hay. O(log n)."""
        antes = self._contar_antes(i)
        if antes < self.total:
            return self._seleccionar(antes + 1)
        return self.n

    # ---- cambios ----
    def cerrar(self, nombre):
        """Devuelve True si cambio algo. O(log n)."""
        i = self.pos[nombre]
        if not self.abierta[i]:
            return False
        p = self.ant[i]
        q = self.sig[i]
        if p >= 0:
            self.sig[p] = q
        if q < self.n:
            self.ant[q] = p
        self._actualizar(i, -1)
        self.abierta[i] = False
        self.total -= 1
        return True

    def abrir(self, nombre):
        """Devuelve True si cambio algo. O(log n)."""
        i = self.pos[nombre]
        if self.abierta[i]:
            return False
        antes = self._contar_antes(i)
        p = self._seleccionar(antes) if antes > 0 else -1
        q = self._seleccionar(antes + 1) if antes < self.total else self.n
        self.ant[i] = p
        self.sig[i] = q
        if p >= 0:
            self.sig[p] = i
        if q < self.n:
            self.ant[q] = i
        self._actualizar(i, 1)
        self.abierta[i] = True
        self.total += 1
        return True
