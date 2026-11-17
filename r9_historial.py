"""R9: deshacer y rehacer cierres, reaperturas y ediciones de ruta.

Estructura: dos pilas (listas usadas solo por el final: append y pop).
  pila de deshacer: cambios hechos, el ultimo arriba.
  pila de rehacer:  cambios deshechos, el ultimo deshecho arriba.
Por que pilas: el ultimo cambio es el primero que se deshace (orden LIFO).
Un cambio nuevo vacia la pila de rehacer.
Alternativa descartada: guardar una copia de toda la red por cada cambio (O(n) de
memoria y tiempo por cambio); aqui se guarda solo la operacion (O(1)).
O grande: registrar, deshacer y rehacer cuestan O(1) de historial + lo que cueste la
operacion invertida (O(log n) o O(1)).

Una operacion es una tupla:
  ("cerrar", nombre) | ("reabrir", nombre)
  ("agregar", ruta, estacion, despues_de, aporte) | ("quitar", ruta, estacion, anterior, aporte)
"""


class Historial:
    def __init__(self):
        self.pila_deshacer = []
        self.pila_rehacer = []

    def registrar(self, operacion):
        self.pila_deshacer.append(operacion)
        self.pila_rehacer = []

    def tomar_para_deshacer(self):
        if len(self.pila_deshacer) == 0:
            return None
        operacion = self.pila_deshacer.pop()
        self.pila_rehacer.append(operacion)
        return operacion

    def tomar_para_rehacer(self):
        if len(self.pila_rehacer) == 0:
            return None
        operacion = self.pila_rehacer.pop()
        self.pila_deshacer.append(operacion)
        return operacion
