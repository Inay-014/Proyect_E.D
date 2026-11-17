# Planeador de viajes TransMilenio

## Arrancar la app (un solo comando)

```bash
python app.py
```

Abre `http://127.0.0.1:8000`. Solo usa la librería estándar de Python (3.9 o superior). Para ver los mapas de fondo se necesita internet; sin internet el mapa muestra las troncales dibujadas.

Otros comandos: `python main.py` (demostración por consola), `python pruebas/correr\_todas.py` (pruebas) y `python revisar\_prohibidos.py` (busca lo prohibido dentro de `motor/`).

## Estructura

|Carpeta|Contenido|
|-|-|
|`motor/`|Toda la lógica. Contrato: `from motor import Red, simular\_fila`. Un archivo por requisito (`r1\_estado.py` … `r10\_fila.py`).|
|`datos/`|`estaciones.csv`, `rutas.csv`, `horarios.csv`. El motor solo lee estos tres.|
|`app\_datos/`|Datos que usa solo la app: ubicación de las estaciones para el mapa.|
|`front/` + `app.py`|La app web. Solo llama al motor.|
|`herramientas/`|Medición del panel de rendimiento (R11) y motor de demostración.|
|`pruebas/`|Una prueba por requisito, contra fuerza bruta.|

## Reglas del motor

Dentro de `motor/` no se usa `dict`, `set`, `sorted`, `.sort()`, `min`/`max` sobre colecciones, `x in lista`, `.index()`, `.count()` ni librerías fuera de `csv`. Lo que hace sus veces:

* **`tabla\_hash.py` — `TablaHash`**: tabla hash propia con encadenamiento, hash polinomial, duplicación al 75 % de carga y recorrido en orden de inserción. Reemplaza a `dict` y `set` en todo el motor.
* **`ordenar.py` — `merge\_sort`**: O(n log n) en el peor caso y estable.
* **`indice\_abiertas.py`**: arreglo ordenado + búsqueda binaria + árbol de Fenwick + lista enlazada de abiertas.

## Decisiones (R12)

|Req|Estructura|Algoritmo|Alternativa descartada|O grande|Qué es n|
|-|-|-|-|-|-|
|R1 `estado`|`TablaHash` nombre → estación|Hash del nombre y búsqueda en la cubeta|Lista secuencial, O(n); arreglo ordenado, O(log n)|O(1) promedio|estaciones|
|R2 `autocompletar`|Arreglo ordenado + Fenwick + lista enlazada de abiertas|Búsqueda binaria del prefijo, salto a la primera abierta y avance de k pasos|Trie (más memoria y conteos por nodo); saltar cerradas una a una, O(n)|O(log n + k)|estaciones; k = pedidas|
|R3 `rango`|La misma de R2|Búsqueda binaria de `desde` y avance hasta pasar `hasta`|Filtrar todas cada vez, O(n)|O(log n + m)|estaciones; m = las del rango|
|R4 `proximo\_bus`|`TablaHash` estación → ruta → arreglo de minutos ordenado|Búsqueda binaria de la primera salida ≥ hora|Recorrer los horarios, O(h)|O(log h)|h = buses de esa ruta en esa estación|
|R5 `viaje`|Recorridos enlazados + índice de rutas por estación + `TablaHash` de alcance|Barrido hacia adelante desde el origen y hacia atrás desde el destino; gana el de menos paradas|BFS sobre estaciones (no distingue la ruta); todos los pares de rutas, O(R²)|O(L)|L = paradas de las rutas que tocan origen y destino|
|R6 `ranking`|Lista ya ordenada en caché, con bandera de "sucio"|Merge sort estable por buses al día; se rehace solo tras un cambio|Reordenar en cada consulta, O(n log n)|O(k) consulta; O(n log n) tras un cambio|estaciones|
|R7 rutas|Lista doblemente enlazada por ruta + `TablaHash` estación → nodo|Hallar el nodo por hash y enlazar o soltar|Arreglo por ruta, O(p) por desplazar|O(1) agregar y quitar; O(p) recorrido|p = paradas de la ruta|
|R8 cierres|Bandera en la estación + índice de abiertas|Cambiar la bandera, actualizar Fenwick y lista, invalidar ranking|Borrar la estación de todas las estructuras|O(log n)|estaciones|
|R9 historial|Dos pilas (listas usadas solo por el final)|Guardar la operación, no una copia de la red; un cambio nuevo vacía rehacer|Copiar la red en cada cambio, O(n)|O(1) + costo de invertir|—|
|R10 `simular\_fila`|Lista ordenada + índice del primero en fila|Avanzar bus por bus; cuántos suben con búsqueda binaria; espera total = Σ salidas − Σ llegadas|Cola con `pop(0)`, O(n²); subir pasajero por pasajero|O(n + b log c); O(n log n) si llegan desordenados|pasajeros; b = buses, c = cupo|

### Horas como 25:10

No se envuelven: 25:10 se guarda como 1510 minutos. Así el servicio de madrugada sigue en orden dentro del mismo día de servicio y se compara con `<`.

## Panel de rendimiento (R11)

Pestaña **Rendimiento**: crea redes ×1, ×2, ×4… con copias de los CSV, mide cada operación y dibuja el tiempo junto a la curva esperada. Cada tarjeta trae la explicación de por qué crece así. R5 no se mide.

## La app

* **Viaje**: buscador y mapa de estaciones. Al tocar una estación: punto de origen, punto de destino o consultar rutas.
* **Estaciones**: buscar, ranking, el recorrido con la menor cantidad de estaciones entre dos (con el estado de cada una) y cerradas.
* **Próximo bus**, **Rutas** (editar, deshacer y rehacer), **Hora pico** y **Rendimiento**.

Extras del motor que usa la app (no son parte del contrato): `camino` (búsqueda en anchura con cola y tabla hash propias, O(V + E), en `motor/camino.py`), `rutas\_en`, `todas`, `proximos\_buses`, `servicios\_en`, `cerradas`.

## 

## 

