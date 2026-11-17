"""Red: el 'main' del motor. Junta los requisitos R1 a R10, cada uno en su propio archivo.

  R1 r1_estado.py       R6 r6_ranking.py
  R2 r2_autocompletar.py  R7 r7_rutas.py
  R3 r3_rango.py        R8 r8_cierres.py
  R4 r4_proximo_bus.py  R9 r9_historial.py
  R5 r5_viaje.py        R10 r10_fila.py (funcion suelta, fuera de esta clase)
Esta clase solo carga los datos, conecta las piezas y expone el contrato.
"""
from .indice_abiertas import IndiceAbiertas
from .lectura import leer_estaciones, leer_rutas, leer_horarios
from .ordenar import merge_sort
from .tiempo import hora_a_minutos, minutos_a_hora
from .r1_estado import TablaEstaciones
from .r2_autocompletar import autocompletar as _autocompletar
from .r3_rango import rango as _rango
from .r4_proximo_bus import Horarios
from .r5_viaje import planear, estaciones_del_viaje
from .camino import camino_minimo
from .r6_ranking import Ranking
from .r7_rutas import Rutas
from .r8_cierres import cerrar_estacion, abrir_estacion
from .r9_historial import Historial


def _por_orden(par):
    return par[0]


def _por_primera_salida(servicio):
    """Clave para ordenar servicios: (primera salida, nombre de la ruta)."""
    return (servicio[0], servicio[1])


class Red:
    def __init__(self, carpeta):
        base = carpeta.rstrip("/\\")
        nombres = leer_estaciones(base + "/estaciones.csv")
        rutas_crudas = leer_rutas(base + "/rutas.csv")
        self.horarios = Horarios(leer_horarios(base + "/horarios.csv"))

        self.tabla = TablaEstaciones()
        for nombre in nombres:
            self.tabla.agregar(nombre)

        self.rutas = Rutas()
        for ruta in rutas_crudas:
            self.rutas.crear(ruta)
            for par in merge_sort(rutas_crudas[ruta], _por_orden):
                est = par[1]
                self.tabla.agregar(est)  # defensa: estacion de una ruta que no estaba en estaciones.csv
                self.rutas.cargar_parada(ruta, est, self.horarios.cantidad(est, ruta))

        todas = []
        for nombre in self.tabla.datos:
            todas.append(nombre)
        ordenadas = merge_sort(todas)
        self.indice = IndiceAbiertas(ordenadas)
        self._ranking = Ranking(ordenadas, self.rutas, self.tabla)
        self.historial = Historial()

    # ---- consultas ----
    def estado(self, nombre):                      # R1
        return self.tabla.estado(nombre)

    def autocompletar(self, prefijo, k):           # R2
        return _autocompletar(self.indice, prefijo, k)

    def rango(self, desde, hasta):                 # R3
        return _rango(self.indice, desde, hasta)

    def proximo_bus(self, estacion, ruta, hora):   # R4
        """hora: 'HH:MM' o minutos. Devuelve 'HH:MM' o None."""
        minutos = hora_a_minutos(hora) if isinstance(hora, str) else hora
        if not self.tabla.esta_abierta(estacion) or not self.rutas.pasa(estacion, ruta):
            return None
        salida = self.horarios.siguiente(estacion, ruta, minutos)
        return None if salida is None else minutos_a_hora(salida)

    def proximos_buses(self, estacion, ruta, hora, n=5):
        """Extra de R4: hasta n horas 'HH:MM' de la ruta en la estacion, desde 'hora'
        (inclusive), en orden. Menos de n (o []) si ya no quedan buses ese dia, la
        estacion esta cerrada o la ruta no pasa por ella. O(log h + n)."""
        minutos = hora_a_minutos(hora) if isinstance(hora, str) else hora
        if not self.tabla.esta_abierta(estacion) or not self.rutas.pasa(estacion, ruta):
            return []
        salidas = self.horarios.siguientes(estacion, ruta, minutos, n)
        resultado = []
        for m in salidas:
            resultado.append(minutos_a_hora(m))
        return resultado

    def servicios_en(self, estacion, hora, n=5):
        """Extra de R4: las rutas que SI paran en la estacion con buses desde 'hora'.
        Devuelve [(ruta, [horas HH:MM])] ordenado por la primera salida (empate: nombre
        de ruta). Una estacion cerrada no tiene servicios. O(r log r + r log h + r n),
        r = rutas que pasan por la estacion."""
        if not self.tabla.esta_abierta(estacion):
            return []
        minutos = hora_a_minutos(hora) if isinstance(hora, str) else hora
        rutas_aqui = self.rutas.pasan.get(estacion)
        if rutas_aqui is None:
            return []
        servicios = []
        for ruta in rutas_aqui:
            salidas = self.horarios.siguientes(estacion, ruta, minutos, n)
            if len(salidas) > 0:
                servicios.append((salidas[0], ruta, salidas))
        servicios = merge_sort(servicios, _por_primera_salida)
        resultado = []
        for _, ruta, salidas in servicios:
            horas = []
            for m in salidas:
                horas.append(minutos_a_hora(m))
            resultado.append((ruta, horas))
        return resultado

    def viaje(self, origen, destino):              # R5
        return planear(self.rutas, self.tabla, origen, destino)

    def camino(self, origen, destino):
        """Extra (lo usa la tarjeta 'Estaciones abiertas' de la app): el recorrido con la MENOR
        cantidad de estaciones entre origen y destino, sin limite de transbordos (BFS, ver
        camino.py). Devuelve lista de (estacion, abierta, ruta) o None si no hay. O(V + E)."""
        minimo = camino_minimo(self.rutas, self.tabla, origen, destino)
        if minimo is None or len(minimo) < 2:
            return minimo
        # Empate: si el viaje de R5 (maximo un transbordo) usa las mismas estaciones, se
        # prefiere ese, que cambia menos de bus.
        abiertas = 0
        for _, abierta, _ in minimo:
            if abierta:
                abiertas += 1
        viaje = planear(self.rutas, self.tabla, origen, destino)
        if viaje:
            estaciones = estaciones_del_viaje(self.rutas, self.tabla, viaje)
            paradas = 0
            for _, abierta, ruta in estaciones:
                if ruta is not None and abierta:
                    paradas += 1
            if paradas == abiertas - 1:
                return estaciones
        return minimo

    def rutas_en(self, estacion):
        """Extra de R4 (lo usa el mapa): rutas que pasan por la estacion, cada una con su
        primer y ultimo bus del dia y cuantos buses pasan. Devuelve lista de
        (ruta, 'HH:MM' primero, 'HH:MM' ultimo, buses) en orden de nombre de ruta.
        Una estacion cerrada o inexistente devuelve []. O(r log r), r = rutas que pasan."""
        if not self.tabla.esta_abierta(estacion):
            return []
        rutas_aqui = self.rutas.pasan.get(estacion)
        if rutas_aqui is None:
            return []
        nombres = []
        for ruta in rutas_aqui:
            nombres.append(ruta)
        resultado = []
        for ruta in merge_sort(nombres):
            ext = self.horarios.extremos(estacion, ruta)
            if ext is None:
                resultado.append((ruta, None, None, 0))
            else:
                resultado.append((ruta, minutos_a_hora(ext[0]), minutos_a_hora(ext[1]), ext[2]))
        return resultado

    def todas(self):
        """Extra para el mapa: todas las estaciones como (nombre, abierta), en orden
        alfabetico. O(n)."""
        resultado = []
        for i in range(self.indice.n):
            resultado.append((self.indice.nombres[i], self.indice.abierta[i]))
        return resultado

    def ranking(self, k):                          # R6
        return self._ranking.top(k)

    def recorrido(self, ruta, al_reves=False, solo_abiertas=False):     # R7 (consulta)
        """Paradas en el orden en que la ruta pasa. Por defecto salen TODAS (contrato);
        con solo_abiertas=True se saltan las estaciones cerradas. O(p)."""
        filtro = self.tabla.esta_abierta if solo_abiertas else None
        try:
            return self.rutas.recorrido(ruta, al_reves, filtro)
        except ValueError:
            return []

    def cerradas(self):
        """Extra de R8: nombres de las estaciones cerradas, en orden alfabetico. O(n)."""
        resultado = []
        for i in range(self.indice.n):
            if not self.indice.abierta[i]:
                resultado.append(self.indice.nombres[i])
        return resultado

    # ---- cambios (todos se pueden deshacer, R9) ----
    def _aplicar(self, op):
        tipo = op[0]
        if tipo == "cerrar":
            cerrar_estacion(self.tabla, self.indice, self._ranking, op[1])
        elif tipo == "reabrir":
            abrir_estacion(self.tabla, self.indice, self._ranking, op[1])
        elif tipo == "agregar":
            self.rutas.agregar(op[1], op[2], op[3], op[4])
            self._ranking.actualizar(op[2])
        else:
            self.rutas.quitar(op[1], op[2])
            self._ranking.actualizar(op[2])

    def _invertir(self, op):
        tipo = op[0]
        if tipo == "cerrar":
            abrir_estacion(self.tabla, self.indice, self._ranking, op[1])
        elif tipo == "reabrir":
            cerrar_estacion(self.tabla, self.indice, self._ranking, op[1])
        elif tipo == "agregar":
            self.rutas.quitar(op[1], op[2])
            self._ranking.actualizar(op[2])
        else:
            self.rutas.agregar(op[1], op[2], op[3], op[4])
            self._ranking.actualizar(op[2])

    def cerrar(self, nombre):                      # R8
        cambio = cerrar_estacion(self.tabla, self.indice, self._ranking, nombre)
        if cambio:
            self.historial.registrar(("cerrar", nombre))
        return cambio

    def reabrir(self, nombre):                     # R8
        cambio = abrir_estacion(self.tabla, self.indice, self._ranking, nombre)
        if cambio:
            self.historial.registrar(("reabrir", nombre))
        return cambio

    def agregar_parada(self, ruta, nueva, despues_de):   # R7
        if not self.tabla.existe(nueva):
            return False
        try:
            cantidad = self.horarios.cantidad(nueva, ruta)
            aporte = self.rutas.agregar(
            ruta, nueva, despues_de, cantidad if cantidad > 0 else None)
        except (ValueError, KeyError):
            return False
        self._ranking.actualizar(nueva)
        self.historial.registrar(("agregar", ruta, nueva, despues_de, aporte))
        return True

    def quitar_parada(self, ruta, estacion):             # R7
        try:
            anterior, aporte = self.rutas.quitar(ruta, estacion)
        except (ValueError, KeyError):
            return False
        self._ranking.actualizar(estacion)
        self.historial.registrar(("quitar", ruta, estacion, anterior, aporte))
        return True

    def deshacer(self):                            # R9
        op = self.historial.tomar_para_deshacer()
        if op is None:
            return False
        self._invertir(op)
        return True

    def rehacer(self):                             # R9
        op = self.historial.tomar_para_rehacer()
        if op is None:
            return False
        self._aplicar(op)
        return True

    # ---- guardar y restaurar los cambios (la app lo usa al cerrar y al abrir) ----
    def exportar_cambios(self):
        """(hechos, deshechos): los cambios aplicados (del mas viejo al mas nuevo) y la pila
        de rehacer (el ultimo deshecho al final). Son listas de listas simples."""
        hechos = []
        for op in self.historial.pila_deshacer:
            hechos.append(list(op))
        deshechos = []
        for op in self.historial.pila_rehacer:
            deshechos.append(list(op))
        return hechos, deshechos

    def _repetir(self, op):
        """Vuelve a ejecutar un cambio guardado con la API publica (queda en el historial)."""
        tipo = op[0]
        if tipo == "cerrar":
            self.cerrar(op[1])
        elif tipo == "reabrir":
            self.reabrir(op[1])
        elif tipo == "agregar":
            self.agregar_parada(op[1], op[2], op[3])
        elif tipo == "quitar":
            self.quitar_parada(op[1], op[2])
        else:
            raise ValueError("Cambio desconocido: " + str(tipo))

    def restaurar_cambios(self, hechos, deshechos):
        """Reaplica lo que devolvio exportar_cambios() sobre una red recien cargada y deja
        las pilas de deshacer y rehacer como estaban. Un cambio que ya no encaje con los CSV
        se omite. Devuelve cuantos cambios omitio. O(c * costo de cada cambio)."""
        omitidos = 0
        for op in hechos:
            try:
                self._repetir(op)
            except (ValueError, KeyError, IndexError):
                omitidos += 1
        aplicados = 0
        i = len(deshechos) - 1
        while i >= 0:          # la pila de rehacer guarda primero el ultimo cambio en el tiempo
            try:
                self._repetir(deshechos[i])
                aplicados += 1
            except (ValueError, KeyError, IndexError):
                omitidos += 1
            i -= 1
        for _ in range(aplicados):
            self.deshacer()
        return omitidos
