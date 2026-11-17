"""Pruebas de lo que agrega la app sobre el contrato: proximos_buses, servicios_en,
recorrido(solo_abiertas), cerradas y guardar/restaurar cambios."""
from _comun import *
import glob
import json

# --- proximos_buses / servicios_en contra recorrer el CSV ---
red = red_real()
modelo = {}
for r, e, h in filas("horarios.csv"):
    modelo.setdefault((e, r), []).append(mins(h))
for v in modelo.values():
    v.sort()
rng = random.Random(3)
claves = list(modelo)
for _ in range(1500):
    e, r = rng.choice(claves)
    m = rng.randint(0, 1560)
    n = rng.randint(0, 8)
    esperado = [hhmm(x) for x in modelo[(e, r)] if x >= m][:n]
    assert red.proximos_buses(e, r, hhmm(m), n) == esperado, (e, r, m, n)
assert red.proximos_buses("NO EXISTE", "1-1", "10:00") == []
assert red.proximos_buses("UNIVERSIDADES", "NO-RUTA", "10:00") == []
for _ in range(200):
    e = rng.choice([k[0] for k in claves]); m = rng.randint(0, 1560)
    sv = red.servicios_en(e, hhmm(m), 5)
    primeras = [(hhmm(min(x for x in modelo[(e, r)] if x >= m)), r)
                for (ee, r) in claves if ee == e and any(x >= m for x in modelo[(e, r)])]
    assert [(h[0], r) for r, h in sv] == sorted(primeras), (e, m)      # ordenadas por primera salida
    for r, horas in sv:
        assert horas == [hhmm(x) for x in modelo[(e, r)] if x >= m][:5]
# Cerrada: sin servicios. Ruta quitada: ya no aparece.
e = "UNIVERSIDADES"
antes = [r for r, _ in red.servicios_en(e, "00:00")]
assert len(antes) > 0
red.cerrar(e); assert red.servicios_en(e, "00:00") == [] and red.proximos_buses(e, antes[0], "00:00") == []
red.reabrir(e)
red.quitar_parada(antes[0], e)
assert antes[0] not in [r for r, _ in red.servicios_en(e, "00:00")]
red.deshacer()
assert antes[0] in [r for r, _ in red.servicios_en(e, "00:00")]

# --- recorrido con solo_abiertas / cerradas ---
red = red_real()
r = "1-1"; todas = red.recorrido(r)
c1, c2 = todas[1], todas[-2]
red.cerrar(c1); red.cerrar(c2)
assert red.recorrido(r) == todas, "por contrato, recorrido() sigue devolviendo todas"
ab = red.recorrido(r, solo_abiertas=True)
assert ab == [x for x in todas if x not in (c1, c2)]
assert red.recorrido(r, al_reves=True, solo_abiertas=True) == ab[::-1]
assert red.cerradas() == sorted([c1, c2])
for otra in red.rutas.recorridos:
    assert c1 not in red.recorrido(otra, solo_abiertas=True)
red.reabrir(c1)
assert red.cerradas() == [c2] and c1 in red.recorrido(r, solo_abiertas=True)

# --- guardar y restaurar: mismo estado, mismas pilas de deshacer/rehacer ---
def foto(red):
    return (red.cerradas(), tuple((x, tuple(red.recorrido(x))) for x in sorted(red.rutas.recorridos)),
            tuple(red.ranking(147)))

for semilla in range(40):
    red, mod = red_aleatoria(semilla)
    rng = random.Random(semilla); nombres = mod["nombres"]
    for _ in range(20):
        a = rng.random(); rr = rng.choice(list(mod["rutas"])); lista = red.recorrido(rr)
        if a < .3: red.cerrar(rng.choice(nombres))
        elif a < .45: red.reabrir(rng.choice(nombres))
        elif a < .65 and len(lista) > 1: red.quitar_parada(rr, rng.choice(lista))
        elif a < .85:
            libres = [n for n in nombres if n not in lista]
            if libres and lista: red.agregar_parada(rr, rng.choice(libres), rng.choice(lista))
        else: red.deshacer()
    hechos, deshechos = red.exportar_cambios()
    guardado = json.loads(json.dumps([hechos, deshechos]))          # igual que el archivo en disco
    # Una red nueva con los mismos CSV: la de 'red' se creo en la carpeta mas reciente.
    carpeta = max(glob.glob(os.path.join(tempfile.gettempdir(), "tm_prueba_*")), key=os.path.getmtime)
    nueva = Red(carpeta)
    assert nueva.restaurar_cambios(*guardado) == 0
    assert foto(nueva) == foto(red), semilla
    assert nueva.exportar_cambios() == red.exportar_cambios(), semilla
    # Las pilas funcionan igual: deshacer todo / rehacer todo en ambas.
    for _ in range(40):
        assert nueva.deshacer() == red.deshacer(); assert foto(nueva) == foto(red)
    for _ in range(40):
        assert nueva.rehacer() == red.rehacer(); assert foto(nueva) == foto(red)
print("ok  extras: proximos_buses/servicios_en = CSV, recorrido solo_abiertas, cerradas, guardar/restaurar (40 redes)")
