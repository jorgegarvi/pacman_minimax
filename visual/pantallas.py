"""
visual/pantallas.py
-------------------
Pantallas y mensajes superpuestos sobre el juego:
inicio, preparado, vida perdida, game over y victoria.
"""

import pygame

from config import (ALTO_HUD, TAM_CASILLA, COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_PACMAN,
                    COLOR_PUNTO, COLORES_FANTASMAS, COLOR_ASUSTADO, COLOR_PELIGRO, MAX_FANTASMAS)


class Pantallas:

    def __init__(self, pantalla, render):
        self.pantalla = pantalla
        self.render = render      # para dibujar los iconos de Pac-Man y fantasmas con el mismo estilo
        self.fuente_grande = pygame.font.SysFont(None, 96)
        self.fuente_titulo = pygame.font.SysFont(None, 64)
        self.fuente_texto = pygame.font.SysFont(None, 28)
        self.fuente_pequena = pygame.font.SysFont(None, 24)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _oscurecer(self, opacidad):
        ancho, alto = self.pantalla.get_size()
        capa = pygame.Surface((ancho, alto - ALTO_HUD), pygame.SRCALPHA)
        capa.fill((0, 0, 0, opacidad))
        self.pantalla.blit(capa, (0, ALTO_HUD))

    def _texto_centrado(self, fuente, texto, color, y):
        imagen = fuente.render(texto, True, color)
        x = self.pantalla.get_width() // 2 - imagen.get_width() // 2
        self.pantalla.blit(imagen, (x, y))
        return imagen.get_height()

    def _parpadeo(self, periodo_ms=500):
        return (pygame.time.get_ticks() // periodo_ms) % 2 == 0

    def dibujar_mensaje(self, titulo, subtitulo, color_titulo=COLOR_PACMAN, oscurecer=True):
        alto = self.pantalla.get_height()
        if oscurecer:
            self._oscurecer(160)
        centro_y = ALTO_HUD + (alto - ALTO_HUD) // 2
        imagen = self.fuente_titulo.render(titulo, True, color_titulo)
        self.pantalla.blit(imagen, (self.pantalla.get_width() // 2 - imagen.get_width() // 2,
                                    centro_y - imagen.get_height()))
        self._texto_centrado(self.fuente_texto, subtitulo, COLOR_TEXTO, centro_y + 10)

    # ------------------------------------------------------------------
    # Pantallas
    # ------------------------------------------------------------------
    def inicio(self, num_fantasmas):
        """Pantalla de inicio: título, leyenda, selector de fantasmas y controles."""
        self._oscurecer(215)
        ancho = self.pantalla.get_width()
        y = ALTO_HUD + 50

        y += self._texto_centrado(self.fuente_grande, "PAC-MAN", COLOR_PACMAN, y) + 4
        y += self._texto_centrado(self.fuente_texto, "Fantasmas con Minimax y poda alfa-beta",
                                  COLOR_TEXTO_SECUNDARIO, y) + 30

        # Leyenda: icono + explicación
        x_icono = ancho // 2 - 160
        x_texto = x_icono + 45
        filas = [
            ("pacman", "Tú: cómete todas las bolitas"),
            ("fantasmas", "Fantasmas: te persiguen y te encierran"),
            ("pildora", "Píldora: asusta a los fantasmas"),
            ("asustado", "Fantasma asustado: ¡cómetelo! (+200)"),
        ]
        for tipo, texto in filas:
            centro = (x_icono, y + 12)
            if tipo == "pacman":
                self.render.dibujar_icono_pacman(centro)
            elif tipo == "fantasmas":
                separacion = 22
                x0 = centro[0] - separacion // 2
                for i in range(2):
                    self.render.dibujar_icono_fantasma((x0 + separacion * i, centro[1]), COLORES_FANTASMAS[i])
            elif tipo == "pildora":
                pygame.draw.circle(self.pantalla, COLOR_PUNTO, centro, TAM_CASILLA // 6 + 1)
            else:
                self.render.dibujar_icono_fantasma(centro, COLOR_ASUSTADO)
            imagen = self.fuente_texto.render(texto, True, COLOR_TEXTO)
            self.pantalla.blit(imagen, (x_texto, y + 12 - imagen.get_height() // 2))
            y += 40

        y += 14
        self._selector_fantasmas(num_fantasmas, y)
        y += 56
        y += self._texto_centrado(self.fuente_pequena, "Flechas: mover     R: reiniciar     ESC: salir",
                                  COLOR_TEXTO_SECUNDARIO, y) + 22
        if self._parpadeo():
            self._texto_centrado(self.fuente_texto, "Pulsa una flecha para empezar", COLOR_PACMAN, y)

    def _selector_fantasmas(self, num_fantasmas, y):
        """Fila 'FANTASMAS (teclas 1-4): 1 2 3 4' con el número elegido resaltado y subrayado."""
        etiqueta = self.fuente_texto.render("FANTASMAS (teclas 1-4):", True, COLOR_TEXTO_SECUNDARIO)
        numeros = [self.fuente_titulo.render(str(n), True, COLOR_PACMAN if n == num_fantasmas
                                             else COLOR_TEXTO_SECUNDARIO)
                   for n in range(1, MAX_FANTASMAS + 1)]
        separacion = 34
        ancho_total = etiqueta.get_width() + 16 + separacion * MAX_FANTASMAS
        x = self.pantalla.get_width() // 2 - ancho_total // 2
        self.pantalla.blit(etiqueta, (x, y + 10))
        x += etiqueta.get_width() + 16
        for n, imagen in enumerate(numeros, start=1):
            self.pantalla.blit(imagen, (x + (separacion - imagen.get_width()) // 2, y - 4))
            if n == num_fantasmas:
                pygame.draw.line(self.pantalla, COLOR_PACMAN, (x + 6, y + 40), (x + separacion - 6, y + 40), 3)
            x += separacion

    def esperando(self):
        self.dibujar_mensaje("PREPARADO", "Pulsa una flecha para empezar", oscurecer=False)

    def vida_perdida(self, vidas_restantes):
        texto = "Te queda 1 vida" if vidas_restantes == 1 else f"Te quedan {vidas_restantes} vidas"
        self.dibujar_mensaje("¡ATRAPADO!", texto, color_titulo=COLOR_PELIGRO)

    def _aviso_record(self, nuevo_record):
        if nuevo_record and self._parpadeo(400):
            alto = self.pantalla.get_height()
            centro_y = ALTO_HUD + (alto - ALTO_HUD) // 2
            self._texto_centrado(self.fuente_texto, "¡NUEVO RÉCORD!", COLOR_PACMAN, centro_y + 44)

    def game_over(self, nuevo_record):
        self.dibujar_mensaje("GAME OVER", "R: reiniciar    ENTER: menú    ESC: salir", color_titulo=COLOR_PELIGRO)
        self._aviso_record(nuevo_record)

    def victoria(self, nuevo_record):
        self.dibujar_mensaje("VICTORIA", "R: reiniciar    ENTER: menú    ESC: salir")
        self._aviso_record(nuevo_record)
