"""Convierte un GTFS a los CSV del motor para una fecha de servicio.

Uso: python herramientas/gtfs_a_csv.py GTFS.zip --fecha 20210715
Por defecto escribe en datos_generados/ y app_datos_generados/, sin tocar datos/.
Una variante de recorrido y sentido recibe un identificador de ruta independiente.
"""
import argparse
import csv
import datetime as dt
import io
from collections import defaultdict
from pathlib import Path
import unicodedata
import zipfile


def normalizar(s):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD', s.upper())
                            if not unicodedata.combining(c)).split())


def hora(s):
    h, m, sec = map(int, s.split(':'))
    if h < 0 or not 0 <= m < 60 or not 0 <= sec < 60:
        raise ValueError('Hora GTFS invalida: ' + s)
    return f'{h:02d}:{m:02d}'


def convertir(archivo, fecha, salida, salida_app):
    fecha = dt.datetime.strptime(fecha, '%Y%m%d').date()
    dia = fecha.strftime('%Y%m%d')
    columna = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')[fecha.weekday()]
    with zipfile.ZipFile(archivo) as z:
        nombres = {Path(n).name: n for n in z.namelist() if not n.endswith('/')}

        def filas(nombre, opcional=False):
            if nombre not in nombres:
                if opcional:
                    return
                raise ValueError('Falta ' + nombre + ' en GTFS')
            with z.open(nombres[nombre]) as raw, io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as f:
                yield from csv.DictReader(f)

        activos = {r['service_id'] for r in filas('calendar.txt', True)
                   if r['start_date'] <= dia <= r['end_date'] and r[columna] == '1'}
        for r in filas('calendar_dates.txt', True):
            if r['date'] == dia:
                if r['exception_type'] == '1':
                    activos.add(r['service_id'])
                elif r['exception_type'] == '2':
                    activos.discard(r['service_id'])
        if not activos:
            raise ValueError('No se encontraron servicios activos en la fecha seleccionada.')
        stops = {r['stop_id']: r for r in filas('stops.txt')}
        rutas = {r['route_id']: (r.get('route_short_name') or r['route_id']).strip()
                 for r in filas('routes.txt')}
        viajes = {r['trip_id']: (r['route_id'], r.get('direction_id', ''))
                  for r in filas('trips.txt') if r['service_id'] in activos}
        por_viaje = defaultdict(list)
        coords = {}
        for r in filas('stop_times.txt'):
            v = r['trip_id']
            if v not in viajes:
                continue
            stop = stops[r['stop_id']]
            padre = stops.get(stop.get('parent_station'), stop)
            nombre = normalizar(padre['stop_name'] or stop['stop_name'])
            if not nombre:
                raise ValueError('Parada sin nombre: ' + r['stop_id'])
            if nombre not in coords:
                lat = padre.get('stop_lat') or stop.get('stop_lat')
                lon = padre.get('stop_lon') or stop.get('stop_lon')
                if lat and lon:
                    coords[nombre] = (float(lat), float(lon))
            tiempo = r.get('departure_time') or r.get('arrival_time')
            if not tiempo:
                raise ValueError('Horario sin hora; se requiere interpolacion GTFS: ' + v)
            por_viaje[v].append((int(r['stop_sequence']), nombre, hora(tiempo)))

    # Un bus por viaje; las paradas contiguas con el mismo nombre se unifican.
    patrones = defaultdict(list)
    estaciones = set()
    for v, paradas in por_viaje.items():
        secuencia = []
        vistos = set()
        for _, nom, h in sorted(paradas):
            if secuencia and secuencia[-1][0] == nom:
                secuencia[-1] = (nom, h)
                continue
            if nom in vistos:
                raise ValueError('Recorrido con estacion repetida, no compatible con el motor: ' + v + ' / ' + nom)
            vistos.add(nom)
            secuencia.append((nom, h))
        if secuencia:
            estaciones.update(vistos)
            patrones[(*viajes[v], tuple(n for n, _ in secuencia))].append(secuencia)
    if not patrones:
        raise ValueError('No se encontraron viajes con horarios.')
    salida, salida_app = Path(salida), Path(salida_app)
    salida.mkdir(parents=True, exist_ok=True)
    salida_app.mkdir(parents=True, exist_ok=True)
    def escribir(path, encabezado, datos):
        with path.open('w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(encabezado)
            w.writerows(datos)
    escribir(salida / 'estaciones.csv', ['nombre'], ((n,) for n in sorted(estaciones)))
    usados, contador = set(), defaultdict(int)
    ids = {}
    for clave in sorted(patrones):
        route_id, direccion, _ = clave
        base = rutas.get(route_id, route_id) or route_id
        contador[base] += 1
        nombre = base if contador[base] == 1 else f'{base}-{contador[base]}'
        while nombre in usados:
            contador[base] += 1
            nombre = f'{base}-{contador[base]}'
        usados.add(nombre)
        ids[clave] = nombre
    escribir(salida / 'rutas.csv', ['ruta', 'orden', 'estacion'],
             ((ids[c], i, n) for c in sorted(patrones) for i, n in enumerate(c[2], 1)))
    escribir(salida / 'horarios.csv', ['ruta', 'estacion', 'hora'],
             ((ids[c], n, h) for c in sorted(patrones) for viaje in patrones[c] for n, h in viaje))
    escribir(salida_app / 'coordenadas.csv', ['nombre', 'lat', 'lon'],
             ((n, *coords[n]) for n in sorted(estaciones) if n in coords))
    print(f'Conversion: {len(estaciones)} estaciones, {len(patrones)} recorridos, fecha {dia}.')
    print(f'CSV: {salida}; coordenadas: {salida_app}.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('gtfs', help='Archivo ZIP con el GTFS')
    p.add_argument('--fecha', required=True, help='Fecha del servicio YYYYMMDD')
    p.add_argument('--salida', default='datos_generados')
    p.add_argument('--salida-app', default='app_datos_generados')
    a = p.parse_args()
    convertir(a.gtfs, a.fecha, a.salida, a.salida_app)
