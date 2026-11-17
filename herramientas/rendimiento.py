"""Panel de rendimiento (R11): duplica la red, corre cada operacion y mide.

Esto vive FUERA de motor/ (es parte de la app), asi que puede usar cualquier libreria.
Para cada factor f crea una red de f copias de la red real (nombres con sufijo ' Zi')
en una carpeta temporal, la carga con el motor y cronometra cada operacion.
"""
import csv
import os
import random
import shutil
import tempfile
import time

OPERACIONES = [
    ("R1", "estado"), ("R2", "autocompletar"), ("R3", "rango"), ("R4", "proximo_bus"),
    ("R6", "ranking con cache valida"), ("R6F", "ranking tras un cambio"), ("R7", "quitar + agregar parada"), ("R8", "cerrar + reabrir"),
    ("R9", "cerrar + deshacer + rehacer + deshacer"), ("R10", "simular_fila"),
]


def _leer(origen, nombre):
    with open(os.path.join(origen, nombre), newline="", encoding="utf-8-sig") as f:
        lector = csv.reader(f)
        enc = next(lector)
        return enc, [x for x in lector if x]


def _sufijo(i):
    return "" if i == 0 else " Z%d" % i


def generar_red(origen, destino, factor):
    os.makedirs(destino, exist_ok=True)
    if factor >= 64:
        # Misma densidad y topologia en todos los tamanos sinteticos.
        # Cada copia conserva el numero de estaciones de la red original.
        _, estaciones = _leer(origen, "estaciones.csv")
        with open(os.path.join(destino, "estaciones.csv"), "w", newline="", encoding="utf-8") as fe, \
             open(os.path.join(destino, "rutas.csv"), "w", newline="", encoding="utf-8") as fr, \
             open(os.path.join(destino, "horarios.csv"), "w", newline="", encoding="utf-8") as fh:
            we, wr, wh = csv.writer(fe), csv.writer(fr), csv.writer(fh)
            we.writerow(["nombre"])
            wr.writerow(["ruta", "orden", "estacion"])
            wh.writerow(["ruta", "estacion", "hora"])
            for i in range(factor):
                for j, fila in enumerate(estaciones):
                    nombre = fila[0] + _sufijo(i)
                    ruta = "SINT-%d-%d" % (i, j // 20)
                    we.writerow([nombre])
                    wr.writerow([ruta, j % 20 + 1, nombre])
                    for hora in ("06:00", "09:00", "12:00", "15:00"):
                        wh.writerow([ruta, nombre, hora])
        return
    for nombre, columnas in (("estaciones.csv", [0]), ("rutas.csv", [0, 2]), ("horarios.csv", [0, 1])):
        enc, filas = _leer(origen, nombre)
        with open(os.path.join(destino, nombre), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(enc)
            for i in range(factor):
                for fila in filas:
                    nueva = list(fila)
                    for c in columnas:
                        nueva[c] = fila[c] + _sufijo(i)
                    w.writerow(nueva)


def _cronometrar(fn):
    """Microsegundos por llamada (mejor de 3 lotes). Lanza lo que lance la operacion."""
    fn()
    t = time.perf_counter()
    fn()
    dt = time.perf_counter() - t
    reps = max(1, min(2000, int(0.012 / max(dt, 1e-7))))
    mejor = None
    for _ in range(3):
        t = time.perf_counter()
        for _ in range(reps):
            fn()
        d = (time.perf_counter() - t) / reps
        if mejor is None or d < mejor:
            mejor = d
    return mejor * 1e6


def _operaciones(red, origen, factor, simular_fila):
    _, est = _leer(origen, "estaciones.csv")
    todas = sorted(e[0] for e in est)
    _, rf = _leer(origen, "rutas.csv")
    ruta, e1, e2 = rf[0][0], rf[0][2], rf[1][2]
    x = todas[len(todas) // 2]
    desde, hasta = todas[len(todas) // 4], todas[3 * len(todas) // 4]
    prefijo = todas[len(todas) // 3][:2]
    rng = random.Random(5)
    llegadas = sorted(rng.randint(0, 180) for _ in range(2000 * factor))

    def r6_frio():
        red.cerrar(x)
        red.reabrir(x)
        return red.ranking(10)

    def r7():
        red.quitar_parada(ruta, e2)
        red.agregar_parada(ruta, e2, e1)

    def r8():
        red.cerrar(x)
        red.reabrir(x)

    def r9():
        red.cerrar(x)
        red.deshacer()
        red.rehacer()
        red.deshacer()

    return {
        "R1": lambda: red.estado(x),
        "R2": lambda: red.autocompletar(prefijo, 5),
        "R3": lambda: red.rango(desde, hasta),
        "R4": lambda: red.proximo_bus(e1, ruta, "12:00"),
        "R6": lambda: red.ranking(10), "R6F": r6_frio,
        "R7": r7, "R8": r8, "R9": r9,
        "R10": lambda: simular_fila(llegadas, 3, 160),
    }


def medir(origen, factores, clase_red, simular_fila):
    tiempos = {op: [] for op, _ in OPERACIONES}
    avisos = {}
    tamanos, cargas = [], []
    n_base = len(_leer(origen, "estaciones.csv")[1])
    for f in factores:
        tmp = tempfile.mkdtemp(prefix="tm_red_")
        try:
            generar_red(origen, tmp, f)
            t0 = time.perf_counter()
            red = clase_red(tmp)
            cargas.append(round(time.perf_counter() - t0, 3))
            tamanos.append(n_base * f)
            ops = _operaciones(red, tmp, f, simular_fila)
            for op, _ in OPERACIONES:
                if op in avisos:
                    tiempos[op].append(None)
                    continue
                try:
                    tiempos[op].append(round(_cronometrar(ops[op]), 3))
                except NotImplementedError as e:
                    avisos[op] = "Pendiente en el motor: %s" % e
                    tiempos[op].append(None)
                except Exception as e:
                    avisos[op] = "%s: %s" % (type(e).__name__, e)
                    tiempos[op].append(None)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return {
        "factores": factores, "tamanos": tamanos, "carga_s": cargas,
        "operaciones": [{"id": op, "nombre": nombre, "tiempos_us": tiempos[op],
                         "aviso": avisos.get(op)} for op, nombre in OPERACIONES],
    }
