"""MOTOR DE DEMOSTRACION: solo sirve para ver la interfaz funcionando.

NO ES TU MOTOR y NO SE ENTREGA como motor/. Usa sorted, index, collections y otras
cosas PROHIBIDAS dentro de motor/. Se activa con:  python app.py --demo
Respeta las mismas firmas del contrato para que la interfaz no note la diferencia.
"""
import csv
from collections import deque


def _filas(ruta):
    with open(ruta, newline="", encoding="utf-8-sig") as f:
        lector = csv.reader(f)
        next(lector)
        return [x for x in lector if x]


def _min(h):
    a, b = h.split(":")
    return int(a) * 60 + int(b)


def _hhmm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


class RedDemo:
    def __init__(self, carpeta):
        base = carpeta.rstrip("/\\")
        self.abierta = {r[0].strip(): True for r in _filas(base + "/estaciones.csv")}
        por_ruta = {}
        for r in _filas(base + "/rutas.csv"):
            por_ruta.setdefault(r[0], []).append((int(r[1]), r[2]))
        self.rutas = {k: [e for _, e in sorted(v)] for k, v in por_ruta.items()}
        self.horas = {}
        self.cuenta = {}
        for r in _filas(base + "/horarios.csv"):
            self.horas.setdefault((r[1], r[0]), []).append(_min(r[2]))
            self.cuenta[r[1]] = self.cuenta.get(r[1], 0) + 1
        for v in self.horas.values():
            v.sort()
        self.hist = []
        self.rehacer_ = []

    # --- consultas ---
    def estado(self, nombre):
        return (nombre in self.abierta, self.abierta.get(nombre, False))

    def autocompletar(self, prefijo, k):
        return [n for n in sorted(self.abierta) if self.abierta[n] and n.startswith(prefijo)][:k]

    def rango(self, desde, hasta):
        return [n for n in sorted(self.abierta) if self.abierta[n] and desde <= n <= hasta]

    def proximo_bus(self, estacion, ruta, hora):
        if not self.abierta.get(estacion):
            return None
        m = _min(hora) if isinstance(hora, str) else hora
        for t in self.horas.get((estacion, ruta), []):
            if t >= m:
                return _hhmm(t)
        return None

    def ranking(self, k):
        orden = sorted(((n, c) for n, c in self.cuenta.items() if self.abierta.get(n)),
                       key=lambda x: (-x[1], x[0]))
        return orden[:k]

    def recorrido(self, ruta, al_reves=False, solo_abiertas=False):
        lista = [e for e in self.rutas[ruta] if self.abierta.get(e) or not solo_abiertas]
        return lista[::-1] if al_reves else lista

    def cerradas(self):
        return sorted(n for n, a in self.abierta.items() if not a)

    def proximos_buses(self, estacion, ruta, hora, n=5):
        if not self.abierta.get(estacion) or estacion not in self.rutas.get(ruta, []):
            return []
        m = _min(hora) if isinstance(hora, str) else hora
        return [_hhmm(t) for t in self.horas.get((estacion, ruta), []) if t >= m][:n]

    def servicios_en(self, estacion, hora, n=5):
        if not self.abierta.get(estacion):
            return []
        sv = [(r, self.proximos_buses(estacion, r, hora, n)) for r, l in self.rutas.items() if estacion in l]
        return sorted((x for x in sv if x[1]), key=lambda x: (x[1][0], x[0]))

    def viaje(self, origen, destino):
        for n in (origen, destino):
            if not self.abierta.get(n):
                raise ValueError("Estación cerrada o inexistente: " + str(n))
        mejor = None
        for r, l in self.rutas.items():
            if origen in l and destino in l:
                i, j = l.index(origen), l.index(destino)
                if i < j and (mejor is None or j - i < mejor["paradas"]):
                    mejor = {"tipo": "directo", "paradas": j - i, "transbordo": None,
                             "tramos": [{"ruta": r, "desde": origen, "hasta": destino, "paradas": j - i}]}
        if mejor:
            return mejor
        A = [(r, l.index(origen), l) for r, l in self.rutas.items() if origen in l]
        B = [(r, l.index(destino), l, set(l)) for r, l in self.rutas.items() if destino in l]
        for ra, ia, la in A:
            for rb, ib, lb, sb in B:
                if ra == rb:
                    continue
                for ja in range(ia + 1, len(la)):
                    t = la[ja]
                    if self.abierta[t] and t in sb:
                        jb = lb.index(t)
                        costo = (ja - ia) + (ib - jb)
                        if jb < ib and (mejor is None or costo < mejor["paradas"]):
                            mejor = {"tipo": "transbordo", "paradas": costo, "transbordo": t,
                                     "tramos": [{"ruta": ra, "desde": origen, "hasta": t, "paradas": ja - ia},
                                                {"ruta": rb, "desde": t, "hasta": destino, "paradas": ib - jb}]}
        return mejor

    # --- operacion ---
    def _ejecutar(self, op):
        t = op[0]
        if t == "cerrar":
            self.abierta[op[1]] = False
        elif t == "reabrir":
            self.abierta[op[1]] = True
        elif t == "agregar":
            _, ruta, nueva, despues = op
            l = self.rutas[ruta]
            l.insert(0 if despues is None else l.index(despues) + 1, nueva)
        elif t == "quitar":
            self.rutas[op[1]].remove(op[2])

    @staticmethod
    def _inverso(op):
        t = op[0]
        if t == "cerrar":
            return ("reabrir", op[1])
        if t == "reabrir":
            return ("cerrar", op[1])
        if t == "agregar":
            return ("quitar", op[1], op[2], op[3])
        return ("agregar", op[1], op[2], op[3])

    def _nuevo(self, op):
        self._ejecutar(op)
        self.hist.append(op)
        self.rehacer_.clear()

    def _verificar(self, nombre):
        if nombre not in self.abierta:
            raise ValueError("No existe la estación: " + str(nombre))

    def cerrar(self, nombre):
        self._verificar(nombre)
        self._nuevo(("cerrar", nombre))

    def reabrir(self, nombre):
        self._verificar(nombre)
        self._nuevo(("reabrir", nombre))

    def agregar_parada(self, ruta, nueva, despues_de):
        if ruta not in self.rutas or despues_de not in self.rutas[ruta]:
            raise ValueError("Ruta o parada de referencia inexistente")
        self._verificar(nueva)
        self._nuevo(("agregar", ruta, nueva, despues_de))

    def quitar_parada(self, ruta, estacion):
        l = self.rutas.get(ruta)
        if l is None or estacion not in l:
            raise ValueError("La ruta no tiene esa parada")
        i = l.index(estacion)
        self._nuevo(("quitar", ruta, estacion, l[i - 1] if i > 0 else None))

    def deshacer(self):
        if not self.hist:
            raise ValueError("No hay nada que deshacer")
        op = self.hist.pop()
        self._ejecutar(self._inverso(op))
        self.rehacer_.append(op)

    def rehacer(self):
        if not self.rehacer_:
            raise ValueError("No hay nada que rehacer")
        op = self.rehacer_.pop()
        self._ejecutar(op)
        self.hist.append(op)


def simular_fila(llegadas, frecuencia, capacidad):
    fila, i, t, n = deque(), 0, 0, len(llegadas)
    total = maxima = buses = 0
    while i < n or fila:
        while i < n and llegadas[i] <= t:
            fila.append(llegadas[i])
            i += 1
        buses += 1
        for _ in range(min(capacidad, len(fila))):
            w = t - fila.popleft()
            total += w
            maxima = max(maxima, w)
        t += frecuencia
    return {"pasajeros": n, "buses": buses,
            "espera_promedio": round(total / n, 2) if n else 0,
            "espera_maxima": maxima, "ultimo_bus": t - frecuencia}
