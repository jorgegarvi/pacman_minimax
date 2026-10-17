"""
juego.py
--------
Controlador del juego: une la lógica (paquete logica) con la parte visual
(paquete visual).

Responsabilidades:
  - el bucle principal de pygame (eventos -> actualizar -> dibujar);
  - leer el teclado (incluida la elección del número de fantasmas);
  - avanzar la partida en "ticks": cada tick, Pac-Man y después cada fantasma
    se mueven una casilla, por turnos, igual que en el árbol de Minimax;
  - gestionar vidas, game over, victoria y récord.
"""

import math

import pygame

from config import (RUTA_MAPA, NUM_FANTASMAS, MAX_FANTASMAS, VIDAS, RONDAS, FPS, DURACION_TICK_MS,
                    PUNTOS_POR_FANTASMA, TAM_CASILLA, ALTO_HUD, TITULO_VENTANA, COLOR_FONDO)
from logica.mapa import cargar_mapa, ARRIBA, ABAJO, IZQUIERDA, DERECHA, QUIETO
from logica.estado import Estado
from logica.reglas import (PACMAN, num_agentes, jugadasPosibles, aplicar,
                           elegir_movimiento_pacman)
from logica.minimax import minimax
from record import cargar_record, guardar_record
from visual.render import Render, centro_casilla
from visual.hud import Hud
from visual.pantallas import Pantallas
from visual.efectos import TextosFlotantes

# Fases de la partida
INICIO = "INICIO"             # pantalla de inicio: se elige el número de fantasmas
ESPERANDO = "ESPERANDO"       # tras reiniciar o perder una vida: espera una flecha
JUGANDO = "JUGANDO"
CAPTURANDO = "CAPTURANDO"     # la lógica ya ha detectado la captura; la animación sigue hasta que los dibujos se tocan
VIDA_PERDIDA = "VIDA_PERDIDA" # pausa breve con la imagen congelada antes de volver a salir
GANANDO = "GANANDO"           # se ha comido la última bolita; Pac-Man termina de llegar a ella
GAME_OVER = "GAME_OVER"
VICTORIA = "VICTORIA"

PAUSA_VIDA_MS = 1300          # duración de la pausa al perder una vida

# Seguridad: si por lo que sea los dibujos no llegan a tocarse, la captura se resuelve igualmente.
MAX_TICKS_CAPTURANDO = 4

TECLAS_DIRECCION = {
    pygame.K_UP: ARRIBA,
    pygame.K_DOWN: ABAJO,
    pygame.K_LEFT: IZQUIERDA,
    pygame.K_RIGHT: DERECHA,
}

# Teclas 1-4 (fila superior y teclado numérico) para elegir el número de fantasmas
TECLAS_FANTASMAS = {
    pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4,
    pygame.K_KP1: 1, pygame.K_KP2: 2, pygame.K_KP3: 3, pygame.K_KP4: 4,
}


class Juego:

    def __init__(self):
        pygame.init()
        self.mapa = cargar_mapa(RUTA_MAPA, MAX_FANTASMAS)

        ancho = self.mapa.columnas * TAM_CASILLA
        alto = ALTO_HUD + self.mapa.filas * TAM_CASILLA
        self.pantalla = pygame.display.set_mode((ancho, alto))
        pygame.display.set_caption(TITULO_VENTANA)
        self.reloj = pygame.time.Clock()

        self.render = Render(self.pantalla, self.mapa)
        self.hud = Hud(self.pantalla)
        self.pantallas = Pantallas(self.pantalla, self.render)
        self.textos = TextosFlotantes(self.pantalla)

        self.num_fantasmas = NUM_FANTASMAS
        self.record = cargar_record()
        self.reiniciar()
        self.fase = INICIO

    # ------------------------------------------------------------------
    # Partida
    # ------------------------------------------------------------------
    def reiniciar(self):
        """Partida nueva desde cero, con el número de fantasmas elegido."""
        self.estado = Estado.inicial(self.mapa, VIDAS, self.num_fantasmas)
        self.nuevo_record = False
        self._preparar_salida()

    def _preparar_salida(self):
        """Deja a los agentes listos para arrancar (inicio o tras perder una vida)."""
        self.fase = ESPERANDO
        self.direccion_deseada = QUIETO   # última flecha pulsada
        self.direccion_actual = QUIETO    # dirección en la que se está moviendo Pac-Man
        self.tiempo_acumulado = 0         # ms transcurridos desde el último tick
        self.indice_captor = None         # fantasma que ha capturado a Pac-Man
        self.tiempo_pausa = 0             # ms transcurridos en la pausa de vida perdida
        self.textos.vaciar()
        # Para la animación: posiciones (y comida) al empezar el tick actual.
        self.anteriores = (self.estado.pacman, self.estado.fantasmas,
                           self.estado.puntos, self.estado.pildoras)
        self.render.reiniciar_fantasmas(self.estado.fantasmas)

    def _terminar_partida(self, fase_final):
        """GAME_OVER o VICTORIA: actualiza el récord si se ha superado."""
        self.fase = fase_final
        if self.estado.marcador > self.record:
            self.record = self.estado.marcador
            self.nuevo_record = True
            guardar_record(self.record)

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------
    def ejecutar(self):
        ejecutando = True
        while ejecutando:
            ms_transcurridos = self.reloj.tick(FPS)
            ejecutando = self._procesar_eventos()
            self._actualizar(ms_transcurridos)
            self._dibujar()
        pygame.quit()

    def _procesar_eventos(self):
        """Lee el teclado. Devuelve False si hay que cerrar el juego."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            if evento.type != pygame.KEYDOWN:
                continue

            if evento.key == pygame.K_ESCAPE:
                return False
            if evento.key == pygame.K_r:
                self.reiniciar()
            elif evento.key == pygame.K_RETURN and self.fase in (GAME_OVER, VICTORIA):
                self.reiniciar()
                self.fase = INICIO                     # volver al menú para cambiar de fantasmas
            elif evento.key in TECLAS_FANTASMAS and self.fase == INICIO:
                self.num_fantasmas = min(TECLAS_FANTASMAS[evento.key], MAX_FANTASMAS)
                self.reiniciar()
                self.fase = INICIO
            elif evento.key in TECLAS_DIRECCION:
                self.direccion_deseada = TECLAS_DIRECCION[evento.key]
                if self.fase in (INICIO, ESPERANDO):
                    self.fase = JUGANDO
        return True

    def _actualizar(self, ms_transcurridos):
        """Avanza el tiempo. En JUGANDO, cada DURACION_TICK_MS ejecuta un tick de juego."""
        self.textos.actualizar(ms_transcurridos)
        if self.fase in (JUGANDO, CAPTURANDO, GANANDO):
            self.render.actualizar_fantasmas(ms_transcurridos)

        if self.fase == JUGANDO:
            self.tiempo_acumulado += ms_transcurridos
            if self.tiempo_acumulado >= DURACION_TICK_MS:
                self.tiempo_acumulado -= DURACION_TICK_MS
                self._tick()

        elif self.fase == CAPTURANDO:
            # La lógica ya no avanza; solo la animación, hasta que los dibujos se tocan.
            self.tiempo_acumulado += ms_transcurridos
            contacto = self.render.hay_contacto(self.estado, self.anteriores, self._progreso_dibujo(),
                                                self._tiempo_animacion(), self.indice_captor)
            if contacto or self.tiempo_acumulado >= MAX_TICKS_CAPTURANDO * DURACION_TICK_MS:
                self._resolver_captura()

        elif self.fase == GANANDO:
            # Pac-Man termina de recorrer la última casilla; después, el cartel de victoria.
            self.tiempo_acumulado += ms_transcurridos
            if self.tiempo_acumulado >= DURACION_TICK_MS:
                self.tiempo_acumulado = DURACION_TICK_MS
                self._terminar_partida(VICTORIA)

        elif self.fase == VIDA_PERDIDA:
            # Imagen congelada (no se avanza tiempo_acumulado) durante la pausa.
            self.tiempo_pausa += ms_transcurridos
            if self.tiempo_pausa >= PAUSA_VIDA_MS:
                self.estado = self.estado.perder_vida()
                self._preparar_salida()

    # ------------------------------------------------------------------
    # Un tick = una ronda: mueve Pac-Man y luego cada fantasma, por turnos
    # ------------------------------------------------------------------
    def _tick(self):
        # Guardar dónde estaba cada agente: el render anima desde aquí.
        self.anteriores = (self.estado.pacman, self.estado.fantasmas,
                           self.estado.puntos, self.estado.pildoras)
        self._jugar_ronda()
        # Apuntar las casillas nuevas de los fantasmas para su animación.
        self.render.registrar_fantasmas(self.estado)

    def _jugar_ronda(self):
        # 1. Pac-Man (jugador humano)
        movimiento = elegir_movimiento_pacman(self.estado, self.direccion_deseada, self.direccion_actual)
        self._aplicar(movimiento, PACMAN)
        if movimiento != QUIETO:
            self.direccion_actual = movimiento
        if self._comprobar_fin_de_ronda():
            return

        # 2. Fantasmas: agentes 1 .. N, en orden
        for agente in range(1, num_agentes(self.estado)):
            jugada = self._decidir_fantasma(agente)
            self._aplicar(jugada, agente)
            if self._comprobar_fin_de_ronda():
                break

    def _aplicar(self, jugada, agente):
        """Aplica la jugada con las reglas y lanza el "+200" si Pac-Man se ha comido un fantasma."""
        antes = self.estado
        self.estado = aplicar(jugada, antes, agente)
        for i in range(len(antes.fantasmas)):
            # Un fantasma comido deja de estar asustado mientras el susto sigue activo.
            if antes.asustados[i] and not self.estado.asustados[i] and self.estado.susto > 0:
                self.textos.anadir(f"+{PUNTOS_POR_FANTASMA}", centro_casilla(self.estado.pacman))

    def _decidir_fantasma(self, agente):
        """
        El fantasma 'agente' lanza su propia búsqueda Minimax con poda alfa-beta,
        siendo él la raíz del árbol. Equivale a la "llamada inicial" del esquema:
            jugada, valor_minimax = minimax(0, tablero, ..., profundidadMaxima, -inf, inf)
        """
        # Si solo hay una jugada posible (p. ej. en una ronda de descanso: QUIETO)
        # no hay nada que decidir y nos ahorramos explorar el árbol.
        jugadas = jugadasPosibles(self.estado, agente)
        if len(jugadas) == 1:
            return jugadas[0]

        profundidad_maxima = RONDAS * num_agentes(self.estado)
        jugada, _valor = minimax(0, self.estado, agente, profundidad_maxima, -math.inf, math.inf)
        return jugada

    def _comprobar_fin_de_ronda(self):
        """
        Tras cada movimiento: ¿han capturado a Pac-Man? ¿se ha comido toda la comida?
        Devuelve True si la ronda debe terminar aquí.
        """
        if self.estado.capturado:
            # La lógica ya ha decidido la captura. Se pasa a CAPTURANDO para que
            # la animación continúe hasta que los dibujos se toquen de verdad.
            self.fase = CAPTURANDO
            self.indice_captor = self.estado.fantasmas.index(self.estado.pacman)
            return True
        if self.estado.comida_restante() == 0:
            # La lógica ya ha decidido la victoria, pero el dibujo de Pac-Man aún
            # está saliendo de la casilla anterior: se deja terminar la animación.
            self.fase = GANANDO
            return True
        return False

    def _resolver_captura(self):
        """Los dibujos ya se tocan: se pierde una vida o termina la partida."""
        if self.estado.vidas > 1:
            self.fase = VIDA_PERDIDA       # pausa breve; al terminar, perder_vida() y vuelta a salir
            self.tiempo_pausa = 0
        else:
            self.estado.vidas = 0
            self._terminar_partida(GAME_OVER)   # el tiempo ya no avanza: imagen congelada en el contacto

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def _progreso_dibujo(self):
        """Fracción del tick que se dibuja para Pac-Man (0 = casilla anterior, 1 = casilla actual)."""
        return min(1.0, self.tiempo_acumulado / DURACION_TICK_MS)

    def _tiempo_animacion(self):
        """Ticks transcurridos desde la salida, con decimales (lo usa la animación de los fantasmas)."""
        return self.estado.ronda + self.tiempo_acumulado / DURACION_TICK_MS

    def _dibujar(self):
        self.pantalla.fill(COLOR_FONDO)
        self.render.dibujar(self.estado, self.direccion_actual, self.anteriores,
                            self._progreso_dibujo(), self._tiempo_animacion())
        self.textos.dibujar()
        self.hud.dibujar(self.estado, self.record)

        if self.fase == INICIO:
            self.pantallas.inicio(self.num_fantasmas)
        elif self.fase == ESPERANDO:
            self.pantallas.esperando()
        elif self.fase == VIDA_PERDIDA:
            self.pantallas.vida_perdida(self.estado.vidas - 1)
        elif self.fase == GAME_OVER:
            self.pantallas.game_over(self.nuevo_record)
        elif self.fase == VICTORIA:
            self.pantallas.victoria(self.nuevo_record)

        pygame.display.flip()
