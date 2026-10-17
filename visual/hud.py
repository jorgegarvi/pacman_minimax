"""
visual/hud.py
-------------
Franja superior con la información de la partida:
marcador, comida restante (bolitas + píldoras), récord, número de fantasmas y vidas.

Todas las cifras usan la MISMA fuente y tamaño; las etiquetas van en un
color más apagado y los números en blanco para que destaquen.
"""

import pygame

from config import (TAM_CASILLA, ALTO_HUD, COLOR_FONDO, COLOR_TEXTO,
                    COLOR_TEXTO_SECUNDARIO, COLOR_PACMAN, COLOR_MURO_BORDE)

TAM_FUENTE = 24


class Hud:

    def __init__(self, pantalla):
        self.pantalla = pantalla
        # SysFont(None, ...) = fuente por defecto de pygame: funciona en cualquier equipo.
        self.fuente = pygame.font.SysFont(None, TAM_FUENTE)

    def _etiqueta_valor(self, etiqueta, valor, x, y):
        """Dibuja 'ETIQUETA  valor' con la misma fuente; devuelve la x donde termina."""
        texto = self.fuente.render(etiqueta, True, COLOR_TEXTO_SECUNDARIO)
        self.pantalla.blit(texto, (x, y))
        x += texto.get_width() + 8
        texto = self.fuente.render(str(valor), True, COLOR_TEXTO)
        self.pantalla.blit(texto, (x, y))
        return x + texto.get_width()

    def _ancho_etiqueta_valor(self, etiqueta, valor):
        return self.fuente.size(etiqueta)[0] + 8 + self.fuente.size(str(valor))[0]

    def dibujar(self, estado, record):
        ancho = self.pantalla.get_width()
        pygame.draw.rect(self.pantalla, COLOR_FONDO, (0, 0, ancho, ALTO_HUD))
        pygame.draw.line(self.pantalla, COLOR_MURO_BORDE, (0, ALTO_HUD - 2), (ancho, ALTO_HUD - 2), 2)

        alto_linea = self.fuente.get_height()
        y1 = ALTO_HUD // 2 - alto_linea - 2     # primera línea
        y2 = ALTO_HUD // 2 + 2                  # segunda línea

        # Marcador y bolitas restantes (izquierda), mismo tamaño
        self._etiqueta_valor("PUNTOS", estado.marcador, 15, y1)
        self._etiqueta_valor("RESTANTES", estado.comida_restante(), 15, y2)

        # Récord de toda la vida y número de fantasmas (centro, alineados en la misma columna)
        num_fantasmas = len(estado.fantasmas)
        ancho_bloque = max(self._ancho_etiqueta_valor("RÉCORD", record),
                           self._ancho_etiqueta_valor("FANTASMAS", num_fantasmas))
        x = ancho // 2 - ancho_bloque // 2
        self._etiqueta_valor("RÉCORD", record, x, y1)
        self._etiqueta_valor("FANTASMAS", num_fantasmas, x, y2)

        # Vidas (derecha): un pequeño Pac-Man por vida
        centro_y = ALTO_HUD // 2
        radio = TAM_CASILLA // 4
        for i in range(estado.vidas):
            x = ancho - 20 - radio - i * (2 * radio + 8)
            pygame.draw.circle(self.pantalla, COLOR_PACMAN, (x, centro_y), radio)
            pygame.draw.polygon(self.pantalla, COLOR_FONDO,
                                [(x, centro_y), (x + radio + 1, centro_y - radio // 2),
                                 (x + radio + 1, centro_y + radio // 2)])
