# Planeador de viajes TransMilenio

Las decisiones de estructura, alternativas y complejidad están resumidas abajo y documentadas
con más detalle en `motor/`. Cada integrante debe poder explicar las decisiones del grupo en la
sustentación, incluso si no implementó ese requisito.

## Arrancar la app (un solo comando)

```bash
python app.py
```

Abre `http://127.0.0.1:8000`. Solo usa la librería estándar de Python (3.9 o superior). Para ver los mapas de fondo se necesita internet; sin internet el mapa muestra las troncales dibujadas.

Otros comandos:

```bash
python main.py
python pruebas/correr_todas.py
python pruebas/prueba_reingreso.py
python revisar_prohibidos.py
```

La prueba de reingreso se ejecuta por separado porque no está incluida en `correr_todas.py`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `motor/` | Toda la lógica. Contrato: `from motor import Red, simular_fila`. Un archivo por requisito (`r1_estado.py` … `r10_fila.py`). |
| `datos/` | `estaciones.csv`, `rutas.csv`, `horarios.csv`. El motor solo lee estos tres. |
| `app_datos/` | Datos que usa solo la app: ubicación de las estaciones para el mapa. La app también admite `appdatos/` si `app_datos/` no existe. |
| `front/` + `app.py` | La app web; consulta y modifica la red mediante el motor, y sirve los archivos de interfaz. |
| `herramientas/` | Medición del panel de rendimiento (R11), motor de demostración y conversor GTFS. |
| `pruebas/` | Pruebas por requisito, casos adicionales y regresión de reingreso. |

## Reglas del motor

Dentro de `motor/` no se usa `dict`, `set`, `sorted`, `.sort()`, `min`/`max` sobre colecciones, `x in lista`, `.index()`, `.count()` ni las librerías prohibidas por el enunciado. Lo que hace sus veces:

- **`tabla_hash.py` — `TablaHash`**: tabla hash propia con encadenamiento, hash polinomial, duplicación al 75 % de carga y recorrido en orden de inserción. Reemplaza a `dict` y `set` en todo el motor.
- **`ordenar.py` — `merge_sort`**: O(n log n) en el peor caso y estable.
- **`indice_abiertas.py`**: arreglo ordenado + búsqueda binaria + árbol de Fenwick + lista enlazada de abiertas.

## Decisiones (R12)

Los costos de acceso por tabla hash se expresan en promedio, suponiendo longitud de clave acotada; las inserciones y eliminaciones incluyen costos amortizados de redimensionamiento o compactación. No son garantías de peor caso ante colisiones. Las operaciones de historial sobre el extremo de las listas también tienen costo amortizado.

| Req | Estructura | Algoritmo | Alternativa descartada | O grande | Qué representa cada variable |
|---|---|---|---|---|---|
| R1 `estado` | `TablaHash` nombre → estación | Hash del nombre y búsqueda en la cubeta; devuelve `"ABIERTA"`, `"CERRADA"` o `"NO EXISTE"` | Lista secuencial, O(n); arreglo ordenado, O(log n) | O(1) promedio | n = estaciones |
| R2 `autocompletar` | Arreglo ordenado + Fenwick + lista enlazada de abiertas | Búsqueda binaria del prefijo, salto a la primera abierta y avance de k pasos | Trie (más memoria y conteos por nodo); saltar cerradas una a una, O(n) | O(log n + k) | estaciones; k = pedidas |
| R3 `rango` | La misma de R2 | Búsqueda binaria de `desde` y avance hasta pasar `hasta` | Filtrar todas cada vez, O(n) | O(log n + m) | estaciones; m = las del rango |
| R4 `proximo_bus` | `TablaHash` estación → ruta → arreglo de minutos ordenado | Búsqueda binaria de la primera salida ≥ hora | Recorrer los horarios, O(h) | O(log h) | h = buses de esa ruta en esa estación |
| R5 `viaje` | Recorridos enlazados + índice de rutas por estación + `TablaHash` de alcance | Barrido hacia adelante desde el origen y hacia atrás desde el destino; gana el de menos paradas | BFS sobre estaciones (no distingue la ruta); todos los pares de rutas, O(R²) | O(L) | L = paradas de las rutas que tocan origen y destino |
| R6 `ranking` | Lista ordenada en caché | Cerrar, reabrir o editar invalida la caché; la próxima consulta positiva reconstruye con merge sort | Insertar o borrar en medio de la lista, O(n); ordenar tras cada cambio, O(n log n) | O(1) invalidación; O(k) con caché válida; O(n log n + k) reconstrucción y consulta (promedio respecto al hash) | n = estaciones; k = resultados devueltos |
| R7 rutas | Lista doblemente enlazada por ruta + `TablaHash` estación → nodo | Hallar el nodo por hash, enlazar o soltar, actualizar totales e invalidar ranking | Arreglo por ruta, O(p) por desplazar | O(1) promedio amortizado agregar y quitar; O(p) recorrido | p = paradas de la ruta |
| R8 cierres | Bandera en la estación + índice de abiertas | Cambiar la bandera, actualizar Fenwick y lista, invalidar ranking | Borrar la estación de todas las estructuras | O(log n) | estaciones |
| R9 historial | Dos pilas (listas usadas solo por el final) | Guardar la operación, no una copia de la red; un cambio nuevo vacía rehacer | Copiar la red en cada cambio, O(n) | O(1) amortizado de pilas + costo de aplicar o invertir; O(log n) para cierres y O(1) promedio amortizado para ediciones | n = estaciones; un cambio nuevo puede liberar la pila de rehacer |
| R10 `simular_fila` | Llegadas con posiciones originales + índice del primero en fila | Si ya vienen ordenadas evita ordenarlas; las llegadas justo a la hora de salida pueden abordar ese bus, hasta llenar el cupo | Cola con `pop(0)`, O(n²) | O(n + b log c) si ya están ordenadas; O(n log n + b log c) si no | n = pasajeros; b = buses usados; c = cupo |

### Consistencia de horarios y ranking

Al reincorporar una parada, R7 consulta el número original de horarios para esa estación y ruta. Si es positivo, usa ese valor para el ranking. Si no hay horarios registrados, conserva el supuesto de usar el número de buses de la parada anterior; esto no crea nuevas horas de salida para R4. Deshacer y rehacer conservan el aporte registrado.

### Horas como 25:10

No se envuelven: 25:10 se guarda como 1510 minutos. Así el servicio de madrugada sigue en orden dentro del mismo día de servicio y se compara con `<`.

### Contrato de salida

- R1 `estado` devuelve `"ABIERTA"`, `"CERRADA"` o `"NO EXISTE"`.
- R5 `viaje` devuelve `None` si no hay viaje, `[]` si origen y destino son la misma estación, o una lista de tramos `(ruta, sube_en, baja_en)`.
- R7 agregar y quitar devuelven `True` si cambian la ruta y `False` si no se puede; `recorrido` devuelve `[]` si la ruta no existe.
- R8 cerrar y reabrir devuelven `False` si la estación no existe o ya tiene ese estado.
- R10 devuelve, en el orden original de `llegadas`, los segundos de salida asignados a cada persona. Los buses salen en `frecuencia`, `2 * frecuencia`, …; una llegada justo a la hora de salida puede abordar ese bus si queda cupo.

Estos formatos describen el comportamiento implementado. Supuestos que deben confirmarse si el contrato del profesor establece otra regla: el viaje de una estación abierta a sí misma tiene cero tramos; las estaciones cerradas se pasan de largo y no cuentan como detenciones; no se admiten estaciones repetidas dentro de un recorrido; el ranking desempata por nombre alfabético.

## Panel de rendimiento (R11)

Pestaña **Rendimiento**: duplica el tamaño de la red, cronometra las operaciones y compara sus tiempos con el crecimiento teórico. R5 no se mide.

- Factores ×1 a ×32: copias de los CSV originales.
- Factores ×64, ×128, ×256 y ×512: redes sintéticas ligeras de topología y densidad comparables entre sí. Con 147 estaciones de base, corresponden a 9.408, 18.816, 37.632 y 75.264 estaciones. No se mezclan las dos familias en una medición.
- R6 mide por separado `ranking(10)` con caché válida y la consulta tras invalidar la caché mediante un cierre y una reapertura (R6F).
- Los tiempos se expresan en microsegundos por llamada; se toma el mejor promedio de tres lotes. Las mediciones son empíricas, no una demostración matemática del Big-O.

## Conversión de GTFS a CSV

El conversor está en `herramientas/gtfs_a_csv.py`. Recibe un ZIP GTFS y una fecha de servicio en formato AAAAMMDD. Ejemplo de uso (la fecha debe estar incluida en el calendario del archivo):

```bash
python herramientas/gtfs_a_csv.py GTFS.zip --fecha 20210715
```

Genera `estaciones.csv`, `rutas.csv` y `horarios.csv` en `datos_generados/`, además de `coordenadas.csv` en `app_datos_generados/`. No sobrescribe por defecto los datos actuales. Usa el calendario de servicio, normaliza los nombres y separa las variantes y sentidos de los recorridos. Si encuentra una estación repetida no consecutiva dentro de un recorrido, informa un error porque el motor no admite ese caso.

**Estado de los datos:** el conversor dispone de una prueba con un GTFS de ejemplo; queda pendiente verificar la conversión con el GTFS original de TransMilenio y validar los CSV obtenidos antes de sustituir los actuales. Las coordenadas actuales son aproximadas.

## La app

- **Viaje**: buscador y mapa de estaciones. Al tocar una estación: punto de origen, punto de destino o consultar rutas.
- **Estaciones**: buscar, ranking, el recorrido con la menor cantidad de estaciones entre dos (con el estado de cada una) y cerradas.
- **Próximo bus**, **Rutas** (editar, deshacer y rehacer), **Hora pico** y **Rendimiento**.

Extras del motor que usa la app (no son parte del contrato): `camino` (búsqueda en anchura con cola y tabla hash propias, O(V + E), en `motor/camino.py`), `rutas_en`, `todas`, `proximos_buses`, `servicios_en`, `cerradas`.

## Integrantes y verificación

La distribución de requisitos y aportes se encuentra en `integrantes.md`.

Antes de integrar cambios, ejecutar las pruebas, la regresión de reingreso y el verificador de restricciones; comprobar también la aplicación y el panel de rendimiento. Guardar los resultados obtenidos y no afirmar que se ha validado la conversión del GTFS original hasta realizar dicha comprobación.
