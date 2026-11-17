#!/usr/bin/env python3
"""App web del Planeador TransMilenio (el 'front').

Un solo comando:   python app.py            (usa tu motor/)
Ver la interfaz:   python app.py --demo     (usa un motor de mentira, solo para mirar)
Sin dependencias: solo libreria estandar. La app SOLO llama al motor: no tiene reglas del sistema.

Formatos de retorno del motor que se SUPONEN (ajusta solo las funciones norm_* de abajo
cuando confirmes el enunciado):
  estado -> (existe, abierta) | dict | texto      autocompletar/rango -> lista de nombres
  proximo_bus -> 'HH:MM' | minutos | None         ranking -> lista de (nombre, cantidad)
  recorrido -> lista de nombres                   viaje -> dict con 'tramos' | None
Datos solo de la app (el motor no los lee): app_datos/coordenadas.csv (mapa) y app_datos/dias.csv (opcional).
Estado: los cierres y las ediciones de ruta se guardan en estado_red.json (tras cada cambio y al
cerrar) y se restauran al arrancar. Para volver a la red original basta borrar ese archivo.
"""
import argparse
import atexit
import csv
import json
import math
import mimetypes
import os
import random
import signal
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)
FRONT = os.path.join(RAIZ, "front")
DATOS = os.path.join(RAIZ, "datos")
APP_DATOS = os.path.join(RAIZ, "app_datos")      # datos SOLO de la app (coordenadas del mapa, dias de operacion)
ESTADO = os.path.join(RAIZ, "estado_red.json")   # cierres y ediciones guardados (ver guardar_estado)


class Ctx:
    red = None
    clase_red = None
    simular_fila = None
    demo = False
    version = 0
    candado = threading.Lock()


CTX = Ctx()


# ---------- normalizadores (UNICO lugar que depende del formato del motor) ----------
def norm_estado(r, nombre):
    existe = abierta = False
    if isinstance(r, dict):
        existe = bool(r.get("existe", r.get("existe_estacion", False)))
        abierta = bool(r.get("abierta", False))
    elif isinstance(r, (tuple, list)) and len(r) == 2:
        existe, abierta = bool(r[0]), bool(r[1])
    elif isinstance(r, str):
        t = r.lower()
        existe = "no existe" not in t and "inexist" not in t
        abierta = existe and "cerrad" not in t and "abiert" in t
    elif isinstance(r, bool):
        existe = abierta = r
    return {"nombre": nombre, "existe": existe, "abierta": abierta}


def norm_lista(r):
    return [x[0] if isinstance(x, (tuple, list)) else x for x in (r or [])]


def norm_ranking(r):
    salida = []
    for x in r or []:
        if isinstance(x, (tuple, list)):
            salida.append({"nombre": x[0], "cantidad": x[1] if len(x) > 1 else None})
        elif isinstance(x, dict):
            salida.append({"nombre": x.get("nombre", x.get("estacion")),
                           "cantidad": x.get("cantidad", x.get("buses"))})
        else:
            salida.append({"nombre": x, "cantidad": None})
    return salida


def norm_hora(r):
    if r is None:
        return None
    if isinstance(r, int):
        return "%02d:%02d" % (r // 60, r % 60)
    return str(r)


def norm_viaje(r, red=None):
    if r is None:
        return None
    if isinstance(r, dict) and "tramos" in r:
        return r
    if isinstance(r, list):
        tramos = []
        total = 0
        for ruta, desde, hasta in r:
            cuenta = 0
            contando = False
            if red is not None:
                for nombre in red.recorrido(ruta):
                    if not contando:
                        if nombre == desde:
                            contando = True
                        continue
                    estado = red.estado(nombre)
                    if estado == "ABIERTA":
                        cuenta += 1
                    if nombre == hasta:
                        break
            tramos.append({"ruta": ruta, "desde": desde, "hasta": hasta, "paradas": cuenta})
            total += cuenta
        return {"tipo": "directo" if len(tramos) < 2 else "transbordo",
                "paradas": total, "transbordo": tramos[0]["hasta"] if len(tramos) == 2 else None,
                "tramos": tramos}
    return {"crudo": r}


# ---------- guardar y restaurar el estado de la red ----------
def guardar_estado():
    """Escribe los cambios de la red (cierres, reaperturas, ediciones de ruta y las pilas de
    deshacer/rehacer) en estado_red.json. Se llama tras cada cambio y al cerrar la app.
    Escritura atomica: se escribe un temporal y se reemplaza, asi nunca queda a medias."""
    if CTX.demo or CTX.red is None or not hasattr(CTX.red, "exportar_cambios"):
        return
    hechos, deshechos = CTX.red.exportar_cambios()
    tmp = ESTADO + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "hechos": hechos, "deshechos": deshechos}, f, ensure_ascii=False)
    os.replace(tmp, ESTADO)


def cargar_estado():
    """Reaplica el estado guardado sobre la red recien cargada. Devuelve un texto para la consola."""
    if CTX.demo or not os.path.isfile(ESTADO) or not hasattr(CTX.red, "restaurar_cambios"):
        return ""
    try:
        with open(ESTADO, encoding="utf-8") as f:
            d = json.load(f)
        omitidos = CTX.red.restaurar_cambios(d.get("hechos", []), d.get("deshechos", []))
    except (OSError, ValueError) as e:
        return "No se pudo leer %s (%s); se empieza con la red original." % (os.path.basename(ESTADO), e)
    n = len(d.get("hechos", [])) + len(d.get("deshechos", []))
    return "Estado restaurado: %d cambio(s)%s." % (n - omitidos, " (%d omitido(s))" % omitidos if omitidos else "")


def cerrar_app(*_):
    with CTX.candado:
        guardar_estado()


# ---------- manejadores ----------
def h_info(q, c):
    rutas = {}
    with open(os.path.join(DATOS, "rutas.csv"), newline="", encoding="utf-8-sig") as f:
        lector = csv.reader(f)
        next(lector)
        for fila in lector:
            if fila:
                rutas[fila[0]] = 1
    with open(os.path.join(DATOS, "estaciones.csv"), newline="", encoding="utf-8-sig") as f:
        n = sum(1 for fila in f) - 1
    return {"demo": CTX.demo, "estaciones": n, "rutas": list(rutas)}


def h_estado(q, c):
    return norm_estado(CTX.red.estado(q["nombre"]), q["nombre"])


def h_auto(q, c):
    return {"items": norm_lista(CTX.red.autocompletar(q.get("prefijo", ""), int(q.get("k", 8))))}


def h_rango(q, c):
    return {"items": norm_lista(CTX.red.rango(q["desde"], q["hasta"]))}


def h_proximo(q, c):
    return {"hora": norm_hora(CTX.red.proximo_bus(q["estacion"], q["ruta"], q["hora"]))}


def h_ranking(q, c):
    return {"items": norm_ranking(CTX.red.ranking(int(q.get("k", 10))))}


def h_recorrido(q, c):
    # Las estaciones cerradas se saltan: la ruta mostrada es la que de verdad se puede usar.
    return {"paradas": norm_lista(CTX.red.recorrido(q["ruta"], q.get("reves") == "1", solo_abiertas=True))}


def h_viaje(q, c):
    for nombre in (q["origen"], q["destino"]):
        e = norm_estado(CTX.red.estado(nombre), nombre)
        if not e["existe"]:
            raise ValueError("La estación %s no existe." % nombre)
        if not e["abierta"]:
            raise ValueError("La estación %s está cerrada: nadie sube, baja ni transborda ahí." % nombre)
    return {"viaje": norm_viaje(CTX.red.viaje(q["origen"], q["destino"]), CTX.red)}


def h_proximos(q, c):
    """Proximo bus + los siguientes. Con ruta: solo esa ruta. Sin ruta: todas las que paran ahi."""
    est, hora, ruta = q["estacion"], q["hora"], q.get("ruta", "").strip()
    n = int(q.get("n", 6))
    e = norm_estado(CTX.red.estado(est), est)
    if not e["existe"]:
        return {"existe": False, "servicios": []}
    if not e["abierta"]:
        return {"existe": True, "cerrada": True, "servicios": []}
    if ruta:
        horas = CTX.red.proximos_buses(est, ruta, hora, n)
        servicios = [{"ruta": ruta, "horas": horas}] if horas else []
    else:
        servicios = [{"ruta": r, "horas": h} for r, h in CTX.red.servicios_en(est, hora, n)]
    return {"existe": True, "cerrada": False, "servicios": servicios}


def _leer_app(nombre):
    """Filas (sin encabezado) de un CSV de app_datos/, o [] si no existe. Se lee una sola vez."""
    if nombre not in _CACHE_APP:
        filas = []
        ruta = os.path.join(APP_DATOS, nombre)
        if os.path.isfile(ruta):
            with open(ruta, newline="", encoding="utf-8-sig") as f:
                lector = csv.reader(f)
                next(lector, None)
                filas = [x for x in lector if x]
        _CACHE_APP[nombre] = filas
    return _CACHE_APP[nombre]


_CACHE_APP = {}


def h_mapa(q, c):
    """Estaciones con su ubicacion (app_datos/coordenadas.csv) y su estado (lo dice el motor)."""
    coords = {f[0]: (float(f[1]), float(f[2])) for f in _leer_app("coordenadas.csv") if len(f) >= 3}
    if hasattr(CTX.red, "todas"):
        estaciones = CTX.red.todas()
    else:
        estaciones = [(n, norm_estado(CTX.red.estado(n), n)["abierta"]) for n in coords]
    return {"estaciones": [{"nombre": n, "abierta": bool(a), "lat": coords[n][0], "lon": coords[n][1]}
                           for n, a in estaciones if n in coords],
            "sin_ubicacion": sum(1 for n, _ in estaciones if n not in coords),
            "aproximado": os.path.isfile(os.path.join(APP_DATOS, "LEEME.txt")) and "APROXIMADAS" in
                          open(os.path.join(APP_DATOS, "LEEME.txt"), encoding="utf-8").read(),
            "tramos": _tramos(coords)}


def _tramos(coords):
    """Lineas de las troncales para el mapa: pares de paradas CONSECUTIVAS de alguna ruta que
    esten a menos de 1,3 km (asi los saltos de las rutas expresas no cruzan el mapa). Se calcula
    una vez con los recorridos que da el motor."""
    if "tramos" not in _CACHE_APP:
        pares = {}
        with open(os.path.join(DATOS, "rutas.csv"), newline="", encoding="utf-8-sig") as f:
            lector = csv.reader(f)
            next(lector, None)
            rutas = list(dict.fromkeys(fila[0] for fila in lector if fila))
        for ruta in rutas:
            try:
                paradas = norm_lista(CTX.red.recorrido(ruta))
            except Exception:
                continue
            for x, y in zip(paradas, paradas[1:]):
                if x in coords and y in coords and (y, x) not in pares:
                    (la1, lo1), (la2, lo2) = coords[x], coords[y]
                    km = math.hypot((la1 - la2) * 111.0, (lo1 - lo2) * 111.0 * math.cos(math.radians(la1)))
                    if km < 1.3:
                        pares[(x, y)] = 1
        _CACHE_APP["tramos"] = [list(p) for p in pares]
    return _CACHE_APP["tramos"]


def h_rutas_estacion(q, c):
    """'Consultar rutas' del mapa: rutas que pasan por la estacion y su horario de operacion.
    El horario sale del motor (primer y ultimo bus segun horarios.csv). Si existe
    app_datos/dias.csv se agregan las columnas lunes-viernes y sabados-domingos-festivos."""
    nombre = q["nombre"]
    e = norm_estado(CTX.red.estado(nombre), nombre)
    if not e["existe"]:
        return {"existe": False, "rutas": []}
    if not e["abierta"]:
        return {"existe": True, "cerrada": True, "rutas": []}
    if not hasattr(CTX.red, "rutas_en"):
        raise NotImplementedError("rutas_en(estacion)")
    dias = {}
    for f in _leer_app("dias.csv"):
        if len(f) >= 4:
            dias.setdefault(f[0], {})[f[1].upper()] = [f[2], f[3]]
    rutas = [{"ruta": r, "primero": p, "ultimo": u, "buses": n, "lv": dias.get(r, {}).get("LV"),
              "sdf": dias.get(r, {}).get("SDF")} for r, p, u, n in CTX.red.rutas_en(nombre)]
    return {"existe": True, "cerrada": False, "por_dias": bool(dias), "rutas": rutas}


def h_camino(q, c):
    """Tarjeta 'Estaciones abiertas': estaciones del mejor viaje entre dos, con su estado."""
    for nombre in (q["origen"], q["destino"]):
        e = norm_estado(CTX.red.estado(nombre), nombre)
        if not e["existe"]:
            raise ValueError("La estación %s no existe." % nombre)
        if not e["abierta"]:
            raise ValueError("La estación %s está cerrada: nadie sube ni baja ahí." % nombre)
    if not hasattr(CTX.red, "camino"):
        raise NotImplementedError("camino(origen, destino)")
    r = CTX.red.camino(q["origen"], q["destino"])
    if r is None:
        return {"paradas": None}
    return {"paradas": [{"nombre": n, "abierta": bool(a), "ruta": ruta} for n, a, ruta in r]}


def h_cerradas(q, c):
    return {"items": norm_lista(CTX.red.cerradas())}


def mutacion(fn):
    def envoltura(q, c):
        if fn(c) is False:
            raise ValueError("Ese cambio no modificó nada (ya estaba así, o no hay historial)")
        CTX.version += 1
        guardar_estado()
        return {"ok": True, "version": CTX.version}
    return envoltura


def llegadas_hora_pico(n, ventana, rng):
    """n minutos de llegada en [0, ventana], YA ORDENADOS, con forma de campana (el pico en
    la mitad). En vez de sortear pasajero por pasajero y ordenar (lento con millones), se
    calcula cuantos llegan en cada minuto y se arma la lista minuto a minuto: O(n + ventana)."""
    mu, sd = ventana / 2, max(ventana / 5, 1e-9)
    pesos = [math.exp(-((m - mu) / sd) ** 2 / 2) * rng.uniform(0.9, 1.1) for m in range(ventana + 1)]
    total = sum(pesos)
    exactos = [n * p / total for p in pesos]
    cuantos = [int(x) for x in exactos]
    faltan = n - sum(cuantos)
    for m in sorted(range(ventana + 1), key=lambda m: exactos[m] - cuantos[m], reverse=True)[:faltan]:
        cuantos[m] += 1
    llegadas = []
    for m, k in enumerate(cuantos):
        llegadas.extend([m] * k)
    return llegadas


def h_fila(q, c):
    import time
    n = int(c.get("pasajeros", 5000))
    ventana = int(c.get("ventana", 120))
    if n < 1 or ventana < 1:
        raise ValueError("Pasajeros y ventana deben ser al menos 1.")
    llegadas = llegadas_hora_pico(n, ventana, random.Random())
    frecuencia = float(c["frecuencia"]) if "." in str(c["frecuencia"]) else int(c["frecuencia"])
    t0 = time.perf_counter()
    r = CTX.simular_fila(llegadas, frecuencia, int(c["capacidad"]))
    # El motor real devuelve una salida por pasajero. Agruparla aquí evita enviar
    # miles de valores sin contexto y permite mostrar el mismo resumen que en demo.
    if isinstance(r, list):
        grupos = {}
        espera_total = espera_maxima = 0
        for llegada, salida in zip(llegadas, r):
            grupos[salida] = grupos.get(salida, 0) + 1
            espera = salida - llegada
            espera_total += espera
            espera_maxima = max(espera_maxima, espera)
        resultado = {
            "pasajeros": n,
            "buses": len(grupos),
            "espera_promedio": round(espera_total / n, 2) if n else 0,
            "espera_maxima": espera_maxima,
            "ultimo_bus": max(grupos) if grupos else 0,
        }
    else:
        resultado = r
    return {"pasajeros": n, "resultado": resultado, "ms": round((time.perf_counter() - t0) * 1000, 1)}


_CACHE_REND = {}
_CANDADO_REND = threading.Lock()


def h_rendimiento(q, c):
    """Mide UN tamano de red (factor). La app pide los tamanos de uno en uno y va pintando,
    asi la primera grafica aparece en menos de un segundo. Cada tamano se mide una sola vez
    por sesion (la medicion usa copias de los CSV originales, no depende de los cierres)."""
    from herramientas.rendimiento import medir
    f = int(c.get("factor", 1))
    if f < 1 or f > 32:
        raise ValueError("Factor fuera de rango.")
    with _CANDADO_REND:                      # una medicion a la vez: dos juntas se estorban y miden mal
        if c.get("forzar") or f not in _CACHE_REND:
            _CACHE_REND[f] = medir(DATOS, [f], CTX.clase_red, CTX.simular_fila)
            return dict(_CACHE_REND[f], guardada=False)
        return dict(_CACHE_REND[f], guardada=True)


GET = {"info": h_info, "estado": h_estado, "autocompletar": h_auto, "rango": h_rango,
       "proximo": h_proximo, "proximos": h_proximos, "cerradas": h_cerradas, "ranking": h_ranking, "recorrido": h_recorrido, "viaje": h_viaje,
       "mapa": h_mapa, "rutas_estacion": h_rutas_estacion, "camino": h_camino}
POST = {
    "cerrar": mutacion(lambda c: CTX.red.cerrar(c["nombre"])),
    "reabrir": mutacion(lambda c: CTX.red.reabrir(c["nombre"])),
    "agregar": mutacion(lambda c: CTX.red.agregar_parada(c["ruta"], c["nueva"], c["despues_de"])),
    "quitar": mutacion(lambda c: CTX.red.quitar_parada(c["ruta"], c["estacion"])),
    "deshacer": mutacion(lambda c: CTX.red.deshacer()),
    "rehacer": mutacion(lambda c: CTX.red.rehacer()),
    "fila": h_fila, "rendimiento": h_rendimiento,
}


def ejecutar(fn, q, c):
    try:
        if fn is h_rendimiento:
            return fn(q, c)
        with CTX.candado:
            return fn(q, c)
    except NotImplementedError as e:
        return {"pendiente": "Pendiente en el motor: %s" % e}
    except KeyError as e:
        return {"error": "Falta el dato %s" % e}
    except (ValueError, TypeError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, e)}


class Manejador(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, datos):
        cuerpo = json.dumps(datos, default=str).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path.startswith("/api/"):
            fn = GET.get(u.path[5:])
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            return self._json(ejecutar(fn, q, {}) if fn else {"error": "Ruta desconocida"})
        ruta = "index.html" if u.path == "/" else u.path.lstrip("/")
        archivo = os.path.realpath(os.path.join(FRONT, ruta))
        if not archivo.startswith(os.path.realpath(FRONT)) or not os.path.isfile(archivo):
            self.send_error(404)
            return
        with open(archivo, "rb") as f:
            datos = f.read()
        self.send_response(200)
        self.send_header("Content-Type", (mimetypes.guess_type(archivo)[0] or "text/plain") + "; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(datos)

    def do_POST(self):
        u = urlparse(self.path)
        fn = POST.get(u.path[5:]) if u.path.startswith("/api/") else None
        largo = int(self.headers.get("Content-Length", 0))
        try:
            c = json.loads(self.rfile.read(largo) or b"{}")
        except ValueError:
            c = {}
        self._json(ejecutar(fn, {}, c) if fn else {"error": "Ruta desconocida"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="usa un motor simulado (solo para ver la interfaz)")
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--sin-navegador", action="store_true")
    a = ap.parse_args()
    CTX.demo = a.demo
    if a.demo:
        from herramientas.motor_demo import RedDemo as clase, simular_fila
    else:
        from motor import Red as clase, simular_fila
    CTX.clase_red, CTX.simular_fila = clase, simular_fila
    CTX.red = clase(DATOS)
    mensaje = cargar_estado()
    if mensaje:
        print(mensaje)
    atexit.register(cerrar_app)
    for senal in ("SIGTERM", "SIGBREAK", "SIGHUP"):      # cerrar la terminal o matar el proceso tambien guarda
        if hasattr(signal, senal):
            signal.signal(getattr(signal, senal), lambda *_: sys.exit(0))
    servidor = ThreadingHTTPServer(("127.0.0.1", a.puerto), Manejador)
    url = "http://127.0.0.1:%d" % a.puerto
    print("Planeador TransMilenio en", url, "(MODO DEMO)" if a.demo else "")
    if not a.sin_navegador:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        print("\nGuardando cambios… hasta luego.")
    finally:
        servidor.server_close()
        cerrar_app()


if __name__ == "__main__":
    main()
