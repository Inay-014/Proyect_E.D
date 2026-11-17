"""Tabla hash propia: reemplaza a dict y set, que estan PROHIBIDOS dentro de motor/.

Estructura (todo sobre 'list', que si esta permitida):
  * 'cubetas': arreglo de tamano potencia de 2. Cada cubeta es None o una lista corta de
    entradas (encadenamiento: las claves que chocan comparten cubeta).
  * 'orden': arreglo con TODAS las entradas en el orden en que se insertaron. Sirve para
    recorrer la tabla en orden de insercion, igual que un dict. Asi los resultados no
    dependen del azar del hash y las pruebas son repetibles.
  * Una entrada es una lista de 3 casillas: [clave, valor, viva].
Funcion hash: polinomial (h = h*31 + byte) sobre los bytes del texto; el indice de la
cubeta es h & (capacidad - 1). El peso distinto de cada posicion hace que 'ROMA' y
'AMOR' caigan en cubetas diferentes.
Factor de carga: al pasar de 0.75 entradas por cubeta la tabla se duplica y se
reinsertan todas (hay que reinsertar porque el indice depende de la capacidad).
Borrado: la entrada sale de su cubeta y se marca muerta en 'orden'; cuando las muertas
son mas de la mitad, 'orden' se compacta.

O grande (n = claves guardadas, L = largo de la clave):
  buscar / insertar / borrar / 'clave in tabla': O(L) del hash + O(1) promedio.
  Peor caso O(n) si todas chocan; el factor de carga lo hace improbable.
  duplicar: O(n), pero pasa cada vez que n se duplica -> O(1) amortizado por insercion.
  recorrer: O(n).
Alternativas descartadas: direccionamiento abierto (el borrado necesita lapidas y es mas
dificil de explicar); arbol binario de busqueda (O(log n) y degenera si las claves
llegan ordenadas, como en estaciones.csv).

Se usa con la sintaxis de corchetes (t[clave], clave in t, del t[clave], for clave
in t), pero cada una de esas operaciones ejecuta el codigo de esta clase.
"""

_MASCARA = 0xFFFFFFFF


class TablaHash:
    __slots__ = ("_cubetas", "_capacidad", "_orden", "_n")

    def __init__(self, capacidad=8):
        self._capacidad = capacidad
        self._cubetas = [None] * capacidad
        self._orden = []
        self._n = 0

    # ---- interno ----
    def _indice(self, clave):
        """Cubeta que le toca a la clave. O(L)."""
        h = 0
        for b in str(clave).encode("utf-8"):
            h = (h * 31 + b) & _MASCARA
        return h & (self._capacidad - 1)

    def _entrada(self, clave):
        """La entrada [clave, valor, viva] de la clave, o None. O(1) promedio."""
        cubeta = self._cubetas[self._indice(clave)]
        if cubeta is not None:
            for entrada in cubeta:
                if entrada[0] == clave:
                    return entrada
        return None

    def _redimensionar(self):
        """Duplica las cubetas y reinserta las entradas vivas. O(n)."""
        vivas = []
        for entrada in self._orden:
            if entrada[2]:
                vivas.append(entrada)
        self._orden = vivas
        self._capacidad *= 2
        self._cubetas = [None] * self._capacidad
        for entrada in vivas:
            i = self._indice(entrada[0])
            if self._cubetas[i] is None:
                self._cubetas[i] = [entrada]
            else:
                self._cubetas[i].append(entrada)

    # ---- operaciones ----
    def poner(self, clave, valor):
        """Inserta la clave o cambia su valor. O(1) promedio (amortizado)."""
        i = self._indice(clave)
        cubeta = self._cubetas[i]
        if cubeta is None:
            cubeta = []
            self._cubetas[i] = cubeta
        else:
            for entrada in cubeta:
                if entrada[0] == clave:
                    entrada[1] = valor
                    return
        entrada = [clave, valor, True]
        cubeta.append(entrada)
        self._orden.append(entrada)
        self._n += 1
        if self._n * 4 > self._capacidad * 3:
            self._redimensionar()

    def get(self, clave, por_defecto=None):
        """Valor de la clave, o 'por_defecto' si no esta. O(1) promedio."""
        entrada = self._entrada(clave)
        return por_defecto if entrada is None else entrada[1]

    def quitar(self, clave):
        """Borra la clave. Lanza KeyError si no esta. O(1) promedio."""
        i = self._indice(clave)
        cubeta = self._cubetas[i]
        if cubeta is not None:
            for j in range(len(cubeta)):
                entrada = cubeta[j]
                if entrada[0] == clave:
                    cubeta[j] = cubeta[len(cubeta) - 1]     # tapa el hueco con la ultima
                    cubeta.pop()
                    entrada[2] = False
                    self._n -= 1
                    if len(self._orden) > 16 and self._n * 2 < len(self._orden):
                        self._compactar()
                    return
        raise KeyError(clave)

    def _compactar(self):
        vivas = []
        for entrada in self._orden:
            if entrada[2]:
                vivas.append(entrada)
        self._orden = vivas

    def claves(self):
        """Lista de claves en orden de insercion. O(n)."""
        resultado = []
        for entrada in self._orden:
            if entrada[2]:
                resultado.append(entrada[0])
        return resultado

    def values(self):
        """Lista de valores en orden de insercion. O(n)."""
        resultado = []
        for entrada in self._orden:
            if entrada[2]:
                resultado.append(entrada[1])
        return resultado

    # ---- misma sintaxis que un dict ----
    def __len__(self):
        return self._n

    def __contains__(self, clave):
        return self._entrada(clave) is not None

    def __getitem__(self, clave):
        entrada = self._entrada(clave)
        if entrada is None:
            raise KeyError(clave)
        return entrada[1]

    def __setitem__(self, clave, valor):
        self.poner(clave, valor)

    def __delitem__(self, clave):
        self.quitar(clave)

    def __iter__(self):
        for entrada in self._orden:
            if entrada[2]:
                yield entrada[0]
