"""main.py: junta y demuestra los requisitos R1 a R10 del motor sobre la red real.

Cada requisito vive en su propio archivo dentro de motor/ (r1_estado.py ... r10_fila.py) y
tiene su propia prueba en pruebas/. Aquí solo se usan todos juntos, por el contrato:
    from motor import Red, simular_fila
Uso:  python main.py
"""
import random

from motor import Red, simular_fila


def titulo(texto):
    print("\n" + "=" * 8, texto, "=" * 8)


red = Red("datos")

titulo('R1 estado(nombre) -> "ABIERTA" | "CERRADA" | "NO EXISTE"')
print("CALLE 26      ->", red.estado("CALLE 26"))
print("NO EXISTE     ->", red.estado("NO EXISTE"))

titulo("R2 autocompletar('CAL', 5)")
print(red.autocompletar("CAL", 5))

titulo("R3 rango('CALLE 26', 'CALLE 45')")
print(red.rango("CALLE 26", "CALLE 45"))

titulo("R4 proximo_bus('UNIVERSIDADES', '1-1', '10:00')")
print(red.proximo_bus("UNIVERSIDADES", "1-1", "10:00"))

titulo("R5 viaje('PORTAL NORTE', 'PORTAL SUR')")
v = red.viaje("PORTAL NORTE", "PORTAL SUR")
for ruta, sube, baja in v:
    print("  ruta", ruta, ":", sube, "->", baja)

titulo("R6 ranking(3)")
print(red.ranking(3))

titulo("R7 recorrido y edición de la ruta 1-1")
print("ida   :", red.recorrido("1-1"))
print("vuelta:", red.recorrido("1-1", al_reves=True))
red.quitar_parada("1-1", "RECINTO FERIAL")
print("sin RECINTO FERIAL:", red.recorrido("1-1"))

titulo("R8 cerrar('CALLE 26')")
red.cerrar("CALLE 26")
print("estado:", red.estado("CALLE 26"), "| en autocompletar('CALLE 2', 50):", "CALLE 26" in red.autocompletar("CALLE 2", 50))

titulo("R9 deshacer() x2 y rehacer()")
print("deshacer:", red.deshacer(), "| CALLE 26 ->", red.estado("CALLE 26"))
print("deshacer:", red.deshacer(), "| ruta 1-1 ->", red.recorrido("1-1"))
print("rehacer :", red.rehacer(), "| ruta 1-1 ->", red.recorrido("1-1"))

titulo("R10 simular_fila(llegadas, frecuencia=2, capacidad=160) con 100.000 pasajeros")
llegadas = [int(min(max(random.gauss(60, 20), 0), 120)) for _ in range(100_000)]
print(simular_fila(llegadas, 2, 160))
