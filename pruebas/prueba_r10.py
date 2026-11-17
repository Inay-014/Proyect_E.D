"""Prueba R10 (simular_fila) por separado."""
from _comun import *
import time
from collections import deque

def bruto(llegadas, f, c):
    """Simulación ingenua con una cola, bus por bus (sin saltos)."""
    a = sorted((llegada, i) for i, llegada in enumerate(llegadas))
    resultado, cola, i, n, salida = [None] * len(a), deque(), 0, len(a), f
    while i < n or cola:
        while i < n and a[i][0] <= salida:
            cola.append(a[i]); i += 1
        for _ in range(min(c, len(cola))):
            llegada, posicion = cola.popleft()
            resultado[posicion] = salida
        salida += f
    return resultado

assert simular_fila([], 3, 10) == []
assert simular_fila([30, 5, 5, 70], 60, 2) == [120, 60, 60, 120]
for bad in ((0, 5), (3, 0)):
    try:
        simular_fila([1], *bad); assert False
    except ValueError:
        pass
rng = random.Random(2)
for _ in range(300):
    n = rng.randint(0, 80)
    llegadas = [rng.randint(0, 120) for _ in range(n)]   # sin ordenar a propósito
    f, c = rng.randint(1, 7), rng.randint(1, 12)
    assert simular_fila(llegadas, f, c) == bruto(llegadas, f, c), (llegadas, f, c)
grande = sorted(int(min(max(rng.gauss(90, 25), 0), 180)) for _ in range(400_000))
t0 = time.perf_counter(); r = simular_fila(grande, 2, 160); dt = time.perf_counter() - t0
assert len(r) == 400_000 and dt < 3, dt
print(f"ok  R10 fila: igual a simulación ingenua (300 casos); 400.000 pasajeros en {dt:.2f} s")
