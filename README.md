# Planeador de viajes TransMilenio

## Descripción del proyecto

El Planeador de viajes TransMilenio es una aplicación desarrollada en Python que permite consultar estaciones, buscar rutas, planear viajes y simular el abordaje de pasajeros utilizando información real de la red de TransMilenio.

El proyecto fue desarrollado para la asignatura **Estructuras de Datos y Algoritmos**. Su objetivo es aplicar estructuras de datos y algoritmos propios para resolver problemas de consulta, planificación y operación de una red de transporte.

La aplicación está dividida en tres componentes principales:

- **Motor:** contiene las estructuras de datos y algoritmos que resuelven los requisitos.
- **Datos:** contiene la información de estaciones, rutas y horarios en archivos CSV.
- **Interfaz:** permite al usuario interactuar con el motor mediante una aplicación web.

## 1. Requisitos del sistema

- Python 3.9 o superior.
- Navegador web actualizado.
- Conexión a internet para visualizar los mapas de fondo. Sin conexión, la aplicación muestra las troncales dibujadas.

## 2. Instalación y ejecución

Descargar o clonar el repositorio y abrir una terminal en la carpeta principal del proyecto.

Para iniciar la aplicación, ejecutar:

```bash
python app.py
```

Abrir en el navegador:

```text
http://127.0.0.1:8000
```

### Otros comandos

Ejecutar la demostración por consola:

```bash
python main.py
```

Ejecutar todas las pruebas:

```bash
python pruebas/correr_todas.py
```

Verificar las restricciones del motor:

```bash
python revisar_prohibidos.py
```

## 3. Estructura del proyecto

| Carpeta o archivo | Descripción |
|---|---|
| `motor/` | Contiene las estructuras de datos y los algoritmos de R1 a R10. |
| `datos/` | Contiene `estaciones.csv`, `rutas.csv` y `horarios.csv`. |
| `app_datos/` | Contiene información adicional utilizada por la aplicación, como las coordenadas de las estaciones. |
| `front/` | Contiene los archivos HTML, CSS, JavaScript y recursos gráficos de la interfaz. |
| `herramientas/` | Contiene las herramientas de demostración y medición del rendimiento. |
| `pruebas/` | Contiene las pruebas de los requisitos y las pruebas generales. |
| `app.py` | Inicia la aplicación web. |
| `main.py` | Ejecuta la demostración por consola. |
| `revisar_prohibidos.py` | Comprueba el uso de elementos restringidos dentro del motor. |
| `integrantes.md` | Registra los integrantes y sus responsabilidades. |

## 4. Funcionamiento del motor

El motor está implementado en Python y contiene la lógica principal del proyecto.

Su contrato de funcionamiento utiliza:

```python
from motor import Red, simular_fila
```

La clase `Red` permite consultar y modificar la red de transporte, mientras que `simular_fila` permite simular el abordaje de pasajeros.

### Requisitos implementados

| Requisito | Funcionalidad |
|---|---|
| R1 | Consultar el estado de una estación. |
| R2 | Autocompletar nombres de estaciones abiertas. |
| R3 | Consultar estaciones dentro de un rango alfabético. |
| R4 | Consultar el próximo bus de una ruta. |
| R5 | Planear viajes directos o con un transbordo. |
| R6 | Obtener el ranking de estaciones con más buses. |
| R7 | Agregar, quitar y consultar paradas de rutas. |
| R8 | Cerrar y reabrir estaciones. |
| R9 | Deshacer y rehacer modificaciones. |
| R10 | Simular una fila de abordaje de pasajeros. |
| R11 | Medir y visualizar el rendimiento de las operaciones. |
| R12 | Documentar y justificar las decisiones de estructuras y algoritmos. |

## 5. Estructuras de datos y algoritmos

El proyecto implementa estructuras propias para cumplir las restricciones del enunciado.

### Estructuras principales

- **Tabla hash (`tabla_hash.py`):** implementa una tabla hash propia con encadenamiento, hash polinomial y redimensionamiento al 75 % de carga.
- **Ordenamiento (`ordenar.py`):** implementa Merge Sort, con complejidad O(n log n) en el peor caso y comportamiento estable.
- **Índice de estaciones abiertas (`indice_abiertas.py`):** utiliza un arreglo ordenado, búsqueda binaria, árbol de Fenwick y lista enlazada de estaciones abiertas.
- **Recorridos (`camino.py`):** implementa búsqueda en anchura mediante una cola y una tabla hash propia.

### Decisiones de R12

| Req. | Estructura | Algoritmo | Alternativa descartada | Complejidad |
|---|---|---|---|---|
| R1 | Tabla hash | Búsqueda por nombre | Búsqueda secuencial O(n) | O(1) promedio |
| R2 | Arreglo ordenado, Fenwick y lista enlazada | Búsqueda binaria y recorrido de abiertas | Trie o recorrer cerradas una a una | O(log n + k) |
| R3 | Índice ordenado | Búsqueda binaria y recorrido del rango | Filtrar todas las estaciones | O(log n + m) |
| R4 | Tabla hash y arreglos ordenados | Búsqueda binaria del próximo horario | Recorrer todos los horarios | O(log h) |
| R5 | Recorridos enlazados y tablas hash | Barridos desde origen y destino | Evaluar todos los pares de rutas | O(L) |
| R6 | Lista ordenada en caché y tabla hash | Actualización de posiciones y Merge Sort inicial | Ordenar toda la red después de cada cambio | O(k) consulta; O(n) por cambio; O(n log n) al crear caché |
| R7 | Lista doblemente enlazada y tabla hash | Enlazar o retirar nodos | Desplazar elementos de un arreglo | O(1) agregar y quitar; O(p) recorrido |
| R8 | Bandera de estado e índice de abiertas | Actualización del estado y del índice | Eliminar la estación de todas las estructuras | O(log n) |
| R9 | Dos pilas | Guardar y recuperar operaciones | Copiar toda la red después de cada cambio | O(1) más el costo de invertir |
| R10 | Lista de llegadas y posiciones originales | Asignación ordenada de pasajeros a buses | Cola con `pop(0)` | O(n + b log c) si las llegadas están ordenadas; O(n log n + b log c) si no |

### Significado de las variables

- `n`: cantidad de estaciones o pasajeros, según la operación.
- `k`: cantidad de resultados solicitados.
- `m`: cantidad de estaciones dentro del rango.
- `h`: cantidad de buses de una ruta en una estación.
- `L`: cantidad de paradas de las rutas involucradas.
- `p`: cantidad de paradas de una ruta.
- `b`: cantidad de buses utilizados.
- `c`: capacidad de cada bus.

Las complejidades indicadas corresponden a las decisiones documentadas para las operaciones del motor.

## 6. Reglas y restricciones del motor

Dentro de `motor/` se deben respetar las prohibiciones establecidas en el enunciado.

### Elementos prohibidos

- `dict` y `set`.
- `sorted()` y `.sort()`.
- `min()` y `max()` sobre colecciones.
- `x in lista`.
- `.index()` y `.count()` para buscar elementos en listas.
- `bisect`, `heapq`, `collections`, `functools` y librerías externas.

### Elementos permitidos

- Listas como arreglos.
- Cadenas y sus métodos.
- Recorridos mediante `for`.
- Módulos `csv`, `time` y `random`.

Las estructuras de datos necesarias deben estar implementadas por el equipo.

## 7. Tratamiento de horarios

Los horarios superiores a las 24 horas, como `25:10`, no se convierten al día siguiente.

Se representan como minutos acumulados desde el inicio del día de servicio. Por ejemplo:

```text
25:10 = 1510 minutos
```

Esto permite mantener el orden de los servicios dentro del mismo día de operación.

## 8. Panel de rendimiento (R11)

La aplicación incluye una pestaña llamada **Rendimiento**, donde se mide el tiempo de ejecución de las operaciones utilizando redes de tamaños crecientes.

Se generan redes de tamaño:

- 1 vez el tamaño original.
- 2 veces el tamaño original.
- 4 veces el tamaño original.
- Y así sucesivamente.

Los resultados se representan mediante gráficas que comparan los tiempos medidos con el crecimiento esperado según la complejidad de cada algoritmo.

El requisito R5 no se mide en este panel.

## 9. Interfaz de la aplicación

La aplicación web permite acceder a las siguientes funcionalidades:

- **Viaje:** búsqueda y selección de estaciones mediante un mapa.
- **Estaciones:** búsqueda, ranking, consulta de recorridos y estaciones cerradas.
- **Próximo bus:** consulta del siguiente servicio disponible.
- **Rutas:** edición de recorridos, deshacer y rehacer modificaciones.
- **Hora pico:** simulación del abordaje de pasajeros.
- **Rendimiento:** visualización de las mediciones de los algoritmos.

## 10. Datos utilizados

El proyecto utiliza tres archivos CSV principales para el funcionamiento del motor:

- `estaciones.csv`
- `rutas.csv`
- `horarios.csv`

Adicionalmente, la aplicación utiliza información de coordenadas almacenada en `app_datos/`.

El motor debe trabajar con los archivos CSV y no depender exclusivamente de los datos de una red específica.

## 11. Pruebas y verificación

Para comprobar el funcionamiento del proyecto se dispone de pruebas individuales y generales dentro de `pruebas/`.

Ejecutar:

```bash
python pruebas/correr_todas.py
```

Para revisar las restricciones:

```bash
python revisar_prohibidos.py
```

La aplicación también debe probarse iniciando mediante:

```bash
python app.py
```

## 12. Consideraciones finales

El proyecto busca demostrar la aplicación práctica de estructuras de datos y algoritmos en un problema real de transporte público.

Las decisiones de implementación deben poder justificarse durante la sustentación, incluyendo las estructuras seleccionadas, los algoritmos utilizados, las alternativas consideradas y sus respectivas complejidades.

Para conocer la distribución de responsabilidades de los integrantes, consultar el archivo `integrantes.md`.
