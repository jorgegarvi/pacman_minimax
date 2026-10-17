"""
logica/mapa.py
--------------
Parte ESTÁTICA del juego: lo que nunca cambia durante la partida
(muros y posiciones iniciales).

Se carga una sola vez desde el fichero .txt. Todos los estados guardan una
referencia al MISMO objeto Mapa, así que los muros no se copian en cada nodo
del árbol de Minimax.

Convención de coordenadas: una casilla es una tupla (fila, columna),
igual que al acceder a una matriz: matriz[fila][columna].
"""

from logica.distancias import calcular_distancias

# ---------------------------------------------------------------------------
# Símbolos del fichero de mapa
# ---------------------------------------------------------------------------
MURO = "#"
PUNTO = "."              # pasillo con bolita
PILDORA = "o"            # pasillo con píldora de poder
VACIO = " "              # pasillo sin bolita
INICIO_PACMAN = "P"      # pasillo sin bolita donde empieza Pac-Man
# Salidas de fantasmas: "1", "2", "3", "4" (pasillo con bolita).
# Con N fantasmas se usan las salidas 1..N, así el número de fantasmas
# se puede cambiar sin tocar el mapa.
SALIDAS_FANTASMAS = "1234"

# ---------------------------------------------------------------------------
# Direcciones: (incremento de fila, incremento de columna)
# Son también las "jugadas" que usa Minimax.
# ---------------------------------------------------------------------------
ARRIBA = (-1, 0)
ABAJO = (1, 0)
IZQUIERDA = (0, -1)
DERECHA = (0, 1)
QUIETO = (0, 0)          # solo se usa si un agente no tiene ninguna salida

# El orden importa: es el orden en que Minimax explorará las jugadas
# y, en caso de empate, se queda con la primera.
DIRECCIONES = (ARRIBA, ABAJO, IZQUIERDA, DERECHA)


def sumar(casilla, direccion):
    """Casilla a la que se llega desde 'casilla' moviéndose en 'direccion'."""
    return (casilla[0] + direccion[0], casilla[1] + direccion[1])


class Mapa:
    """Muros y posiciones iniciales del laberinto."""

    def __init__(self, filas, columnas, muros, inicio_pacman,
                 inicios_fantasmas, puntos_iniciales, pildoras_iniciales):
        self.filas = filas
        self.columnas = columnas
        self.muros = muros                          # set de casillas que son muro
        self.inicio_pacman = inicio_pacman          # casilla (fila, col)
        self.inicios_fantasmas = inicios_fantasmas  # tupla de casillas: salida del fantasma 1, 2, 3, 4
        self.puntos_iniciales = puntos_iniciales    # frozenset de casillas con bolita
        self.pildoras_iniciales = pildoras_iniciales  # frozenset de casillas con píldora de poder
        self.distancias = None                      # tabla BFS: distancias[origen][destino] (ver cargar_mapa)

    def es_muro(self, casilla):
        """True si la casilla es muro o está fuera del mapa."""
        fila, col = casilla
        if fila < 0 or fila >= self.filas or col < 0 or col >= self.columnas:
            return True
        return casilla in self.muros

    def vecinas(self, casilla):
        """Casillas libres adyacentes, en el orden de DIRECCIONES."""
        resultado = []
        for direccion in DIRECCIONES:
            vecina = sumar(casilla, direccion)
            if not self.es_muro(vecina):
                resultado.append(vecina)
        return resultado

    def casillas_libres(self):
        """Todas las casillas que no son muro (las usa la tabla de distancias BFS)."""
        libres = []
        for fila in range(self.filas):
            for col in range(self.columnas):
                if (fila, col) not in self.muros:
                    libres.append((fila, col))
        return libres


def cargar_mapa(ruta, max_fantasmas):
    """
    Lee el fichero de texto y construye el Mapa.
    Cada carácter es una casilla; cada línea, una fila.
    """
    with open(ruta, encoding="utf-8") as fichero:
        lineas = [linea.rstrip("\n") for linea in fichero if linea.strip()]

    filas = len(lineas)
    columnas = len(lineas[0])
    for numero, linea in enumerate(lineas):
        if len(linea) != columnas:
            raise ValueError(f"La fila {numero} del mapa mide {len(linea)} y debería medir {columnas}")

    muros = set()
    puntos = set()
    pildoras = set()
    inicio_pacman = None
    inicios_fantasmas = []

    for fila, linea in enumerate(lineas):
        for col, simbolo in enumerate(linea):
            casilla = (fila, col)
            if simbolo == MURO:
                muros.add(casilla)
            elif simbolo == PUNTO:
                puntos.add(casilla)
            elif simbolo == PILDORA:
                pildoras.add(casilla)
            elif simbolo == INICIO_PACMAN:
                inicio_pacman = casilla
            elif simbolo in SALIDAS_FANTASMAS:
                inicios_fantasmas.append((int(simbolo), casilla))
                puntos.add(casilla)
            elif simbolo != VACIO:
                raise ValueError(f"Símbolo desconocido '{simbolo}' en la casilla {casilla}")

    if inicio_pacman is None:
        raise ValueError("El mapa no tiene posición inicial de Pac-Man ('P')")
    if len(inicios_fantasmas) < max_fantasmas:
        raise ValueError(f"El mapa tiene {len(inicios_fantasmas)} salidas de fantasma y se necesitan {max_fantasmas}")

    # Ordenadas por su número: la salida "1" es la del fantasma 1, etc.
    salidas = tuple(casilla for _numero, casilla in sorted(inicios_fantasmas))
    mapa = Mapa(filas, columnas, muros, inicio_pacman,
                salidas, frozenset(puntos), frozenset(pildoras))

    # Distancias reales entre casillas: se calculan una sola vez, aquí.
    mapa.distancias = calcular_distancias(mapa)
    return mapa
