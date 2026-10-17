"""
visual/render.py
----------------
Dibuja el laberinto, las bolitas, Pac-Man y los fantasmas.

La lógica mueve a los agentes de casilla en casilla una vez por tick. Si se
dibujaran siempre en el centro de su casilla se verían "saltos". Para que el
movimiento sea fluido (SOLO visual; la lógica y Minimax siguen trabajando con
casillas enteras):

  - Pac-Man: interpolación dentro del tick, entre la casilla donde estaba al
    empezar el tick y la casilla donde está ahora:
        posición dibujada = anterior + (actual - anterior) * progreso     (progreso de 0 a 1)

  - Fantasmas: recorren su camino a velocidad constante (ver visual/animacion.py),
    para que la regla de descanso no se vea como "avanzar, avanzar, pararse".
"""

import math
import pygame

from config import (TAM_CASILLA, ALTO_HUD, COLOR_FONDO, COLOR_MURO, COLOR_MURO_BORDE,
                    COLOR_PUNTO, COLOR_PACMAN, COLORES_FANTASMAS, COLOR_OJO, COLOR_PUPILA,
                    COLOR_ASUSTADO, COLOR_ASUSTADO_AVISO,
                    DESCANSO_FANTASMAS_CADA, DURACION_TICK_MS)
from logica.mapa import DIRECCIONES, DERECHA, QUIETO, sumar
from visual.animacion import AnimadorFantasmas


RADIO_PACMAN = TAM_CASILLA // 2 - 4
RADIO_FANTASMA = TAM_CASILLA // 2 - 5


def pixel_de(posicion):
    """
    Píxel del centro de una posición (fila, col) del mapa. Acepta decimales:
    (2, 5.5) está a medio camino entre las casillas (2, 5) y (2, 6).
    El mapa empieza debajo del HUD.
    """
    fila, col = posicion
    return (col * TAM_CASILLA + TAM_CASILLA / 2,
            ALTO_HUD + fila * TAM_CASILLA + TAM_CASILLA / 2)


def centro_casilla(casilla):
    """Píxel central de una casilla entera (fila, col)."""
    return pixel_de(casilla)


def posicion_interpolada(anterior, actual, progreso):
    """Píxel entre el centro de 'anterior' y el de 'actual' (progreso 0 -> anterior, 1 -> actual)."""
    x0, y0 = pixel_de(anterior)
    x1, y1 = pixel_de(actual)
    return (x0 + (x1 - x0) * progreso, y0 + (y1 - y0) * progreso)


class Render:

    def __init__(self, pantalla, mapa):
        self.pantalla = pantalla
        self.mapa = mapa
        # Los muros no cambian nunca: se dibujan una vez en una superficie aparte
        # y en cada fotograma solo se copia esa imagen (mucho más rápido).
        self.fondo_mapa = self._crear_fondo_mapa()
        self.animador = AnimadorFantasmas(DESCANSO_FANTASMAS_CADA)

    # ------------------------------------------------------------------
    # Animación de los fantasmas (la llama juego.py)
    # ------------------------------------------------------------------
    def reiniciar_fantasmas(self, casillas):
        self.animador.reiniciar(casillas)

    def registrar_fantasmas(self, estado):
        self.animador.registrar(estado)

    def actualizar_fantasmas(self, ms):
        self.animador.actualizar(ms / DURACION_TICK_MS)

    def _pixel_pacman(self, estado, anteriores, progreso):
        return posicion_interpolada(anteriores[0], estado.pacman, progreso)

    def _pixel_fantasma(self, indice, t):
        return pixel_de(self.animador.posicion(indice, t))

    def hay_contacto(self, estado, anteriores, progreso, t, indice):
        """True si el dibujo de Pac-Man y el del fantasma 'indice' se están tocando."""
        px, py = self._pixel_pacman(estado, anteriores, progreso)
        fx, fy = self._pixel_fantasma(indice, t)
        return math.hypot(px - fx, py - fy) <= RADIO_PACMAN + RADIO_FANTASMA

    # ------------------------------------------------------------------
    # Muros
    # ------------------------------------------------------------------
    def _crear_fondo_mapa(self):
        ancho = self.mapa.columnas * TAM_CASILLA
        alto = self.mapa.filas * TAM_CASILLA
        superficie = pygame.Surface((ancho, alto))
        superficie.fill(COLOR_FONDO)

        margen = TAM_CASILLA // 5
        # Dos pasadas: primero el borde (más grueso) y encima el relleno.
        # Cada muro es un bloque redondeado, y se "suelda" con sus muros vecinos
        # para que el laberinto se vea como tuberías continuas.
        for color, extra in ((COLOR_MURO_BORDE, 2), (COLOR_MURO, 0)):
            for (fila, col) in self.mapa.muros:
                x = col * TAM_CASILLA
                y = fila * TAM_CASILLA
                m = margen - extra
                bloque = pygame.Rect(x + m, y + m, TAM_CASILLA - 2 * m, TAM_CASILLA - 2 * m)
                pygame.draw.rect(superficie, color, bloque, border_radius=6)
                for direccion in DIRECCIONES:
                    vecina = sumar((fila, col), direccion)
                    if vecina in self.mapa.muros:
                        puente = bloque.copy()
                        puente.move_ip(direccion[1] * TAM_CASILLA // 2, direccion[0] * TAM_CASILLA // 2)
                        pygame.draw.rect(superficie, color, puente)
        return superficie

    # ------------------------------------------------------------------
    # Dibujo de cada fotograma
    # ------------------------------------------------------------------
    def dibujar(self, estado, direccion_pacman, anteriores, progreso, t):
        """
        anteriores = (casilla de Pac-Man, casillas de fantasmas, bolitas, píldoras) al empezar el tick.
        progreso   = fracción del tick actual transcurrida (0..1), para Pac-Man.
        t          = ticks transcurridos desde la salida, con decimales, para los fantasmas.
        """
        _pacman, _fantasmas, puntos_anteriores, pildoras_anteriores = anteriores

        self.pantalla.blit(self.fondo_mapa, (0, ALTO_HUD))
        # La comida que Pac-Man se come en este tick sigue visible hasta que
        # su dibujo llega a ella (mitad del recorrido).
        llegado = progreso >= 0.5
        self._dibujar_puntos(estado.puntos if llegado else puntos_anteriores)
        self._dibujar_pildoras(estado.pildoras if llegado else pildoras_anteriores)

        # Boca: si Pac-Man está avanzando, se abre y se cierra una vez por casilla
        # (cerrada al salir y al llegar, abierta a mitad de camino). Quieto, semiabierta.
        if anteriores[0] != estado.pacman:
            apertura = 5 + 40 * math.sin(math.pi * progreso)
        else:
            apertura = 30
        self._dibujar_pacman(self._pixel_pacman(estado, anteriores, progreso), direccion_pacman, apertura)

        for indice in range(len(estado.fantasmas)):
            centro = self._pixel_fantasma(indice, t)
            if estado.asustados[indice]:
                color = self._color_asustado(estado.susto)      # mismo dibujo, solo cambia el color
            else:
                color = COLORES_FANTASMAS[indice % len(COLORES_FANTASMAS)]
            self._dibujar_fantasma(centro, color)

    def _dibujar_puntos(self, puntos):
        radio = max(2, TAM_CASILLA // 10)
        for casilla in puntos:
            pygame.draw.circle(self.pantalla, COLOR_PUNTO, centro_casilla(casilla), radio)

    def _dibujar_pildoras(self, pildoras):
        # Laten (el radio crece y decrece) para que se distingan de las bolitas.
        latido = (math.sin(pygame.time.get_ticks() / 150) + 1) / 2      # 0..1
        radio = TAM_CASILLA // 6 + int(2 * latido)
        for casilla in pildoras:
            pygame.draw.circle(self.pantalla, COLOR_PUNTO, centro_casilla(casilla), radio)

    def dibujar_icono_pacman(self, centro):
        """Pac-Man suelto (lo usa la pantalla de inicio)."""
        self._dibujar_pacman(centro, DERECHA, 35)

    def dibujar_icono_fantasma(self, centro, color):
        """Fantasma suelto (lo usa la pantalla de inicio)."""
        self._dibujar_fantasma(centro, color)

    def _dibujar_pacman(self, centro, direccion, apertura_grados):
        """
        Pac-Man como un "quesito": un círculo al que le falta el sector de la boca.
        Se dibuja directamente el polígono del cuerpo (centro + puntos del borde
        fuera de la boca), así no queda ningún resto amarillo delante de la boca.
        apertura_grados = mitad del ángulo de la boca.
        """
        cx, cy = centro
        radio = RADIO_PACMAN
        if apertura_grados < 1:
            pygame.draw.circle(self.pantalla, COLOR_PACMAN, (cx, cy), radio)
            return

        if direccion == QUIETO:
            direccion = DERECHA
        angulo = math.atan2(direccion[0], direccion[1])   # (fila, col) -> (y, x)
        apertura = math.radians(apertura_grados)

        pasos = 32
        inicio = angulo + apertura                        # el cuerpo empieza donde acaba la boca...
        barrido = 2 * math.pi - 2 * apertura              # ...y da la vuelta hasta el otro labio
        puntos = [(cx, cy)]
        for i in range(pasos + 1):
            a = inicio + barrido * i / pasos
            puntos.append((cx + radio * math.cos(a), cy + radio * math.sin(a)))
        pygame.draw.polygon(self.pantalla, COLOR_PACMAN, puntos)

    def _dibujar_cuerpo(self, cx, cy, radio, color):
        """Media circunferencia arriba + rectángulo abajo + tres "pies"."""
        pygame.draw.circle(self.pantalla, color, (cx, cy - 2), radio)
        pygame.draw.rect(self.pantalla, color, (cx - radio, cy - 2, 2 * radio, radio))
        ancho_pie = (2 * radio) // 3
        for i in range(3):
            pie_x = cx - radio + i * ancho_pie + ancho_pie // 2
            pygame.draw.circle(self.pantalla, color, (pie_x, cy + radio - 3), ancho_pie // 2)

    def _color_asustado(self, susto):
        """Azul mientras dura el susto; en las últimas rondas parpadea en blanco como aviso."""
        aviso = susto <= 7 and (pygame.time.get_ticks() // 200) % 2 == 0
        return COLOR_ASUSTADO_AVISO if aviso else COLOR_ASUSTADO

    def _dibujar_fantasma(self, centro, color):
        cx, cy = int(centro[0]), int(centro[1])
        radio = RADIO_FANTASMA
        self._dibujar_cuerpo(cx, cy, radio, color)

        # Ojos
        separacion = radio // 2
        for lado in (-1, 1):
            ojo = (cx + lado * separacion, cy - 4)
            pygame.draw.circle(self.pantalla, COLOR_OJO, ojo, radio // 3)
            pygame.draw.circle(self.pantalla, COLOR_PUPILA, ojo, radio // 6)
