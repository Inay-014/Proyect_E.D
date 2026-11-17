"""Estructuras base del motor (implementadas a mano).

Estacion: nombre + bandera abierta/cerrada.
Recorrido: lista doblemente enlazada con indice (TablaHash propia) de las paradas de UNA ruta.
"""


from .tabla_hash import TablaHash
class Estacion:
    """Una estacion y su estado. Cerrar o reabrir es cambiar una bandera."""
    __slots__ = ("nombre", "abierta")

    def __init__(self, nombre):
        self.nombre = nombre
        self.abierta = True


class Nodo:
    """Una parada dentro de un recorrido: apunta a la anterior y a la siguiente."""
    __slots__ = ("estacion", "ant", "sig")

    def __init__(self, estacion):
        self.estacion = estacion
        self.ant = None
        self.sig = None


class Recorrido:
    """Paradas de UNA ruta (un solo sentido) como lista doblemente enlazada.

    Por que enlazada y no un arreglo: R7 inserta y quita paradas todo el tiempo.
    En un arreglo cada cambio desplaza hasta p elementos, O(p); aqui, con el nodo
    en la mano, enlazar o desenlazar es O(1). La tabla hash 'nodos' (estacion -> Nodo)
    evita recorrer la lista para ENCONTRAR el nodo (busqueda O(1)).
    Por que doble: recorrer al reves y quitar un nodo sin buscar a su anterior.
    Supuesto: una ruta no repite estacion.
    """
    __slots__ = ("nombre", "cabeza", "cola", "tam", "nodos")

    def __init__(self, nombre):
        self.nombre = nombre
        self.cabeza = None
        self.cola = None
        self.tam = 0
        self.nodos = TablaHash()

    def __len__(self):
        return self.tam

    def agregar_al_final(self, estacion):
        """O(1)."""
        nodo = Nodo(estacion)
        if self.cola is None:
            self.cabeza = nodo
            self.cola = nodo
        else:
            nodo.ant = self.cola
            self.cola.sig = nodo
            self.cola = nodo
        if estacion not in self.nodos:
            self.nodos[estacion] = nodo
        self.tam += 1

    def insertar_despues(self, referencia, estacion):
        """Inserta 'estacion' justo despues de 'referencia'. O(1)."""
        ref = self.nodos[referencia]
        nodo = Nodo(estacion)
        siguiente = ref.sig
        nodo.ant = ref
        nodo.sig = siguiente
        ref.sig = nodo
        if siguiente is None:
            self.cola = nodo
        else:
            siguiente.ant = nodo
        self.nodos[estacion] = nodo
        self.tam += 1

    def insertar_al_inicio(self, estacion):
        """Inserta al principio (lo usa deshacer cuando se quito la primera parada). O(1)."""
        nodo = Nodo(estacion)
        nodo.sig = self.cabeza
        if self.cabeza is None:
            self.cola = nodo
        else:
            self.cabeza.ant = nodo
        self.cabeza = nodo
        self.nodos[estacion] = nodo
        self.tam += 1

    def quitar(self, estacion):
        """Quita la parada y devuelve el nombre de la anterior (o None). O(1)."""
        nodo = self.nodos[estacion]
        anterior = nodo.ant
        siguiente = nodo.sig
        if anterior is None:
            self.cabeza = siguiente
        else:
            anterior.sig = siguiente
        if siguiente is None:
            self.cola = anterior
        else:
            siguiente.ant = anterior
        del self.nodos[estacion]
        self.tam -= 1
        return None if anterior is None else anterior.estacion

    def a_lista(self, al_reves=False, filtro=None):
        """Nombres de las estaciones en orden de recorrido (o invertido). O(p).

        filtro: funcion opcional estacion -> bool; si se da, solo salen las que la cumplen
        (la usa Red.recorrido para saltar las estaciones cerradas). p = paradas de la ruta.
        """
        resultado = []
        if al_reves:
            actual = self.cola
            while actual is not None:
                if filtro is None or filtro(actual.estacion):
                    resultado.append(actual.estacion)
                actual = actual.ant
        else:
            actual = self.cabeza
            while actual is not None:
                if filtro is None or filtro(actual.estacion):
                    resultado.append(actual.estacion)
                actual = actual.sig
        return resultado
