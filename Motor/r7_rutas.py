"""R7: editar rutas (agregar / quitar parada) y ver el recorrido en los dos sentidos.

Estructura: TablaHash propia ruta -> Recorrido (lista doblemente enlazada con indice por estacion).
Ademas, dos indices que se mantienen en cada edicion:
  pasan[estacion][ruta] = buses por dia de esa ruta en esa estacion
  total[estacion]       = suma de lo anterior (la usa R6)
  y 'pasan' tambien responde "que rutas pasan por esta estacion" (la usa R5).
Alternativa descartada: arreglo por ruta (cada edicion O(p) por desplazar elementos).
O grande: agregar_parada y quitar_parada O(1); recorrido O(p).
p = paradas de la ruta.

SUPUESTO a confirmar: una parada nueva no trae horarios en horarios.csv; se asume que
la ruta pasa por ella tantas veces al dia como por la parada 'despues_de' (para R6).
"""
from .tabla_hash import TablaHash
from .estructuras import Recorrido


class Rutas:
    def __init__(self):
        self.recorridos = TablaHash()
        self.pasan = TablaHash()
        self.total = TablaHash()

    def crear(self, ruta):
        self.recorridos[ruta] = Recorrido(ruta)

    def _ruta(self, ruta):
        rec = self.recorridos.get(ruta)
        if rec is None:
            raise ValueError("No existe la ruta: " + str(ruta))
        return rec

    def pasa(self, estacion, ruta):
        d = self.pasan.get(estacion)
        return d is not None and ruta in d

    def _registrar(self, estacion, ruta, aporte):
        if estacion not in self.pasan:
            self.pasan[estacion] = TablaHash()
        self.pasan[estacion][ruta] = aporte
        self.total[estacion] = self.total.get(estacion, 0) + aporte

    def cargar_parada(self, ruta, estacion, aporte):
        """Usado al cargar los CSV: agrega al final. O(1)."""
        self.recorridos[ruta].agregar_al_final(estacion)
        if not self.pasa(estacion, ruta):
            self._registrar(estacion, ruta, aporte)

    def agregar(self, ruta, nueva, despues_de, aporte=None):
        """Agrega 'nueva' despues de 'despues_de' (None = al inicio, solo para deshacer).
        Devuelve el aporte (buses/dia) usado. O(1)."""
        rec = self._ruta(ruta)
        if nueva in rec.nodos:
            raise ValueError("La ruta " + str(ruta) + " ya pasa por " + str(nueva))
        if despues_de is None:
            rec.insertar_al_inicio(nueva)
            if aporte is None:
                aporte = 0
        else:
            if despues_de not in rec.nodos:
                raise ValueError("La ruta " + str(ruta) + " no pasa por " + str(despues_de))
            rec.insertar_despues(despues_de, nueva)
            if aporte is None:
                aporte = self.pasan[despues_de][ruta]
        self._registrar(nueva, ruta, aporte)
        return aporte

    def quitar(self, ruta, estacion):
        """Quita la parada. Devuelve (anterior, aporte) para poder deshacer. O(1)."""
        rec = self._ruta(ruta)
        if estacion not in rec.nodos:
            raise ValueError("La ruta " + str(ruta) + " no pasa por " + str(estacion))
        anterior = rec.quitar(estacion)
        aporte = self.pasan[estacion][ruta]
        del self.pasan[estacion][ruta]
        self.total[estacion] -= aporte
        return anterior, aporte

    def recorrido(self, ruta, al_reves=False, filtro=None):
        """Paradas en el orden en que la ruta pasa. 'filtro' (opcional) deja solo algunas."""
        return self._ruta(ruta).a_lista(al_reves, filtro)
