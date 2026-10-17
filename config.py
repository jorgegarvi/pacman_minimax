"""
config.py
---------
Constantes de configuración del juego.

Es el ÚNICO sitio donde se cambian los valores de ajuste: reglas de la partida,
velocidad, profundidad de búsqueda, tamaños y colores.
No importa pygame, así que lo pueden usar tanto la lógica como la parte visual.
"""

import os

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
RUTA_MAPA = os.path.join(DIRECTORIO_BASE, "mapas", "mapa_15x15.txt")
RUTA_RECORD = os.path.join(DIRECTORIO_BASE, "record.txt")

# ---------------------------------------------------------------------------
# Reglas de la partida
# ---------------------------------------------------------------------------
VIDAS = 3                 # vidas con las que empieza Pac-Man
NUM_FANTASMAS = 2         # fantasmas al abrir el juego (se cambia en la pantalla de inicio con las teclas 1-4)
MAX_FANTASMAS = 4         # el mapa tiene 4 salidas de fantasma (1, 2, 3, 4)
PUNTOS_POR_BOLITA = 10    # lo que suma al marcador cada bolita comida
PUNTOS_POR_PILDORA = 50   # lo que suma cada píldora de poder
PUNTOS_POR_FANTASMA = 200 # lo que suma comerse un fantasma asustado

# Píldoras de poder: rondas que duran asustados los fantasmas tras comerse una
# (25 rondas x 200 ms = 5 segundos).
DURACION_SUSTO = 25

# Velocidad de los fantasmas: descansan 1 de cada N rondas.
# Con 4 se mueven 3 de cada 4 rondas (velocidad 3/4 respecto a Pac-Man).
# Es una REGLA del juego: Minimax también la simula dentro del árbol.
DESCANSO_FANTASMAS_CADA = 4

# Un fantasma comido espera en su casilla de reaparición al menos estas rondas
# antes de volver a moverse (como la "casa" de los fantasmas del original).
ESPERA_REAPARICION = 4

# ---------------------------------------------------------------------------
# Búsqueda (Minimax con poda alfa-beta)
# ---------------------------------------------------------------------------
# Una ronda = mueven Pac-Man y todos los fantasmas = (1 + fantasmas) niveles del árbol.
# profundidadMaxima = RONDAS * (1 + fantasmas)
# (con 2 fantasmas: 3 niveles por ronda -> 6 niveles; con 4 fantasmas: 10 niveles).
RONDAS = 2

# ---------------------------------------------------------------------------
# Tiempo
# ---------------------------------------------------------------------------
FPS = 60                  # fotogramas por segundo (fluidez del dibujo)
DURACION_TICK_MS = 200    # cada cuánto avanza cada agente una casilla

# ---------------------------------------------------------------------------
# Pantalla
# ---------------------------------------------------------------------------
TAM_CASILLA = 40          # píxeles por casilla
ALTO_HUD = 60             # franja superior con marcador, vidas, etc.
TITULO_VENTANA = "Pac-Man"

# ---------------------------------------------------------------------------
# Colores (R, G, B)
# ---------------------------------------------------------------------------
COLOR_FONDO = (8, 8, 20)
COLOR_MURO = (28, 45, 140)
COLOR_MURO_BORDE = (70, 110, 255)
COLOR_PUNTO = (255, 205, 170)
COLOR_PACMAN = (255, 215, 0)
COLOR_TEXTO = (240, 240, 240)
COLOR_TEXTO_SECUNDARIO = (150, 150, 180)
COLOR_OJO = (255, 255, 255)
COLOR_PUPILA = (30, 40, 140)
COLOR_ASUSTADO = (35, 50, 210)          # fantasma asustado
COLOR_ASUSTADO_AVISO = (235, 235, 255)  # parpadeo cuando el susto está a punto de acabar
COLOR_PELIGRO = (235, 60, 60)           # títulos de ¡ATRAPADO! y GAME OVER

# Un color por fantasma: el fantasma k sale de la casilla 'k' del mapa
COLORES_FANTASMAS = [
    (235, 50, 50),     # rojo     -> fantasma 1
    (255, 150, 200),   # rosa     -> fantasma 2
    (255, 165, 60),    # naranja  -> fantasma 3
    (60, 200, 230),    # azul     -> fantasma 4
]
