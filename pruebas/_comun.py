"""Utilidades compartidas por las pruebas. Fuera de motor/ SI se puede usar cualquier libreria."""
import csv
import os
import random
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from motor import Red, simular_fila  # noqa: E402

CARPETA = os.path.join(RAIZ, "datos")


def red_real():
    return Red(CARPETA)


def filas(nombre):
    with open(os.path.join(CARPETA, nombre), newline="", encoding="utf-8-sig") as f:
        lector = csv.reader(f)
        next(lector)
        return [x for x in lector if x]


def mins(h):
    a, b = h.split(":")
    return int(a) * 60 + int(b)


def hhmm(m):
    return "%02d:%02d" % (m // 60, m % 60)


def red_aleatoria(semilla, n_est=12, n_rutas=6):
    """Red pequena al azar escrita en una carpeta temporal. Horarios SIN ordenar (a proposito)."""
    rng = random.Random(semilla)
    nombres = ["E%02d" % i for i in range(n_est)]
    rutas, horas = {}, {}
    for r in range(n_rutas):
        rutas["R%d" % r] = rng.sample(nombres, rng.randint(2, min(7, n_est)))
    tmp = tempfile.mkdtemp(prefix="tm_prueba_")
    with open(os.path.join(tmp, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["nombre"])
        for n in nombres:
            w.writerow([n])
    with open(os.path.join(tmp, "rutas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ruta", "orden", "estacion"])
        filas_r = [(r, i + 1, e) for r, lista in rutas.items() for i, e in enumerate(lista)]
        rng.shuffle(filas_r)
        for fila in filas_r:
            w.writerow(fila)
    with open(os.path.join(tmp, "horarios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ruta", "estacion", "hora"])
        todas = []
        for r, lista in rutas.items():
            for e in lista:
                horas[(e, r)] = [rng.randint(300, 1560) for _ in range(rng.randint(1, 6))]
                todas.extend((r, e, hhmm(m)) for m in horas[(e, r)])
        rng.shuffle(todas)
        for fila in todas:
            w.writerow(fila)
    return Red(tmp), {"nombres": nombres, "rutas": rutas, "horas": horas}


def red_a_mano(rutas):
    """rutas: dict ruta -> lista de estaciones. Horarios: un bus a las 08:00 en cada parada."""
    nombres = []
    for lista in rutas.values():
        for e in lista:
            if e not in nombres:
                nombres.append(e)
    tmp = tempfile.mkdtemp(prefix="tm_prueba_")
    with open(os.path.join(tmp, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["nombre"])
        for n in nombres:
            w.writerow([n])
    with open(os.path.join(tmp, "rutas.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ruta", "orden", "estacion"])
        for r, lista in rutas.items():
            for i, e in enumerate(lista):
                w.writerow([r, i + 1, e])
    with open(os.path.join(tmp, "horarios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ruta", "estacion", "hora"])
        for r, lista in rutas.items():
            for e in lista:
                w.writerow([r, e, "08:00"])
    return Red(tmp)


# ---- ayudas para viajes (fuerza bruta) ----
def abiertas_entre(lista, i, j, abiertas):
    """Cuantas estaciones abiertas hay en lista[i+1 .. j]."""
    return sum(1 for e in lista[i + 1:j + 1] if e in abiertas)


def mejor_bruto(rutas, abiertas, o, d):
    if o not in abiertas or d not in abiertas:
        return None
    if o == d:
        return 0
    mejor = None
    for r1, l1 in rutas.items():
        if o not in l1:
            continue
        i = l1.index(o)
        if d in l1 and l1.index(d) > i:
            c = abiertas_entre(l1, i, l1.index(d), abiertas)
            mejor = c if mejor is None or c < mejor else mejor
        for r2, l2 in rutas.items():
            if r2 == r1 or d not in l2:
                continue
            jd = l2.index(d)
            for pos in range(i + 1, len(l1)):
                t = l1[pos]
                if t in abiertas and t != d and t in l2 and l2.index(t) < jd:
                    c = abiertas_entre(l1, i, pos, abiertas) + abiertas_entre(l2, l2.index(t), jd, abiertas)
                    mejor = c if mejor is None or c < mejor else mejor
    return mejor


def validar_viaje(v, rutas, abiertas, o, d):
    """El viaje devuelto es real: las rutas existen, el orden es correcto y las cuentas cuadran."""
    tramos = v
    assert tramos[0][1] == o and tramos[-1][2] == d
    for k, t in enumerate(tramos):
        ruta, desde, hasta = t
        l = rutas[ruta]
        i, j = l.index(desde), l.index(hasta)
        assert i < j, "orden incorrecto"
        assert hasta in abiertas and desde in abiertas
        if k + 1 < len(tramos):
            assert tramos[k + 1][1] == hasta and tramos[k + 1][0] != ruta


def paradas_viaje(v, rutas, abiertas):
    total = 0
    for ruta, desde, hasta in v:
        l = rutas[ruta]
        i, j = l.index(desde), l.index(hasta)
        total += abiertas_entre(l, i, j, abiertas)
    return total
