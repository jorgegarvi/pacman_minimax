"""
logica/minimax.py
-----------------
Minimax con poda alfa-beta, basado en el esquema de clase.

La estructura es la MISMA que la de la diapositiva. Las líneas marcadas con
"# CAMBIO" son las adaptaciones necesarias para este juego:

  (1) el caso base devuelve una tupla (jugada, valor), igual que el resto
      de la función (en la diapositiva devolvía solo el valor y el [1] fallaba);
  (2) aplicar() devuelve un tablero NUEVO; el original no se modifica,
      así cada jugada se evalúa sobre el tablero correcto;
  (3) el caso base también corta si la partida ha terminado (captura o victoria);
  (4) jugada_seleccionada empieza en None y siempre se queda con la primera
      jugada, aunque todas valgan -inf o +inf;
  (5) en vez de un booleano 'maximizador' hay un número de 'agente':
      0 = Pac-Man (MAX), 1..N = fantasmas (MIN). El turno pasa de forma
      cíclica; con 2 fantasmas: 0 -> 1 -> 2 -> 0; con 4: 0 -> 1 -> 2 -> 3 -> 4 -> 0.
      Los fantasmas forman un único jugador minimizador que mueve por
      partes (coalición), así que alpha y beta significan lo mismo en todas
      las capas MIN.

Llamada desde el juego, cuando le toca decidir al fantasma k:
    jugada, valor = minimax(0, estado, k, RONDAS * num_agentes(estado), -math.inf, math.inf)
"""

import math

from logica.reglas import PACMAN, num_agentes, jugadasPosibles, aplicar, es_final
from logica.evaluacion import puntuacion


def minimax(profundidad, tablero, agente, profundidadMaxima, alpha, beta):   # CAMBIO (5): agente
    # caso base : profundidad máxima alcanzada o partida terminada
    if profundidad == profundidadMaxima or es_final(tablero):                # CAMBIO (3)
        return None, puntuacion(tablero, profundidad)                        # CAMBIO (1)

    siguiente = (agente + 1) % num_agentes(tablero)                          # CAMBIO (5): turno cíclico
    jugada_seleccionada = None                                               # CAMBIO (4)

    if agente == PACMAN:                                                     # MAX
        maximo = -math.inf
        for jugada in jugadasPosibles(tablero, agente):
            nuevo_tablero = aplicar(jugada, tablero, agente)                 # CAMBIO (2)
            nuevo_score = minimax(profundidad + 1, nuevo_tablero, siguiente,
                                  profundidadMaxima, alpha, beta)[1]
            if nuevo_score > maximo or jugada_seleccionada is None:          # CAMBIO (4)
                maximo = nuevo_score
                jugada_seleccionada = jugada

            alpha = max(alpha, nuevo_score)
            if alpha >= beta:
                break
        return jugada_seleccionada, maximo

    else:                                                                    # MIN (cualquier fantasma)
        minimo = math.inf
        for jugada in jugadasPosibles(tablero, agente):
            nuevo_tablero = aplicar(jugada, tablero, agente)                 # CAMBIO (2)
            nuevo_score = minimax(profundidad + 1, nuevo_tablero, siguiente,
                                  profundidadMaxima, alpha, beta)[1]
            if nuevo_score < minimo or jugada_seleccionada is None:          # CAMBIO (4)
                minimo = nuevo_score
                jugada_seleccionada = jugada

            beta = min(beta, nuevo_score)
            if alpha >= beta:
                break
        return jugada_seleccionada, minimo
