"""
visual/efectos.py
-----------------
Textos flotantes (por ejemplo "+200" al comerse un fantasma): aparecen en un
punto, suben un poco y se desvanecen. Es solo decoración: no afecta a la lógica.
"""

import pygame

from config import COLOR_TEXTO

DURACION_MS = 900     # cuánto tarda en desaparecer
SUBIDA_PX = 24        # cuánto sube mientras se desvanece


class TextosFlotantes:

    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.fuente = pygame.font.SysFont(None, 28)
        self.textos = []      # cada texto: [superficie, x, y, ms_vividos]

    def anadir(self, texto, centro, color=COLOR_TEXTO):
        superficie = self.fuente.render(texto, True, color)
        self.textos.append([superficie, centro[0], centro[1], 0])

    def vaciar(self):
        self.textos = []

    def actualizar(self, ms):
        for texto in self.textos:
            texto[3] += ms
        self.textos = [t for t in self.textos if t[3] < DURACION_MS]

    def dibujar(self):
        for superficie, x, y, vivido in self.textos:
            avance = vivido / DURACION_MS                 # 0 -> 1
            imagen = superficie.copy()
            imagen.set_alpha(int(255 * (1 - avance)))     # se va haciendo transparente
            self.pantalla.blit(imagen, (x - imagen.get_width() // 2,
                                        y - imagen.get_height() // 2 - SUBIDA_PX * avance))
