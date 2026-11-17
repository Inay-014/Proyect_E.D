"""R1: buscar una estacion (existe? esta abierta?).

Estructura: TablaHash propia (tabla_hash.py) nombre -> Estacion.
Por que: es la consulta mas frecuente y pide un nombre EXACTO; con hash la busqueda
es O(1) promedio sin importar cuantas estaciones haya.
Alternativa descartada: lista con busqueda secuencial (O(n)); arreglo ordenado con
busqueda binaria (O(log n), y ademas habria que mantenerlo ordenado).
O grande: estado() es O(1) promedio. n = numero de estaciones.

Formato de retorno (SUPUESTO, confirmar con el enunciado): tupla (existe, abierta).
"""
from .tabla_hash import TablaHash
from .estructuras import Estacion


class TablaEstaciones:
    def __init__(self):
        self.datos = TablaHash()

    def agregar(self, nombre):
        if nombre not in self.datos:
            self.datos[nombre] = Estacion(nombre)

    def existe(self, nombre):
        return nombre in self.datos

    def esta_abierta(self, nombre):
        est = self.datos.get(nombre)
        return est is not None and est.abierta

    def fijar_abierta(self, nombre, valor):
        self.datos[nombre].abierta = valor

    def estado(self, nombre):
        """Devuelve ABIERTA, CERRADA o NO EXISTE para el nombre exacto."""
        est = self.datos.get(nombre)
        if est is None:
            return "NO EXISTE"
        return "ABIERTA" if est.abierta else "CERRADA"
