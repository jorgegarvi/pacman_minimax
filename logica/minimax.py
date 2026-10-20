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


def minimax(profundidad, tablero, agente, profundidadMaxima, alpha, beta):  
    # caso base : profundidad máxima alcanzada o partida terminada
    if profundidad == profundidadMaxima or es_final(tablero):                
        return None, puntuacion(tablero, profundidad)                       

    # Secuencia de agentes que se va evaluando, como no jugamos en modo de un jugador contra la máquina
    # si no que tenemos más máquinas (fantasmas) necesitamos una secuencia que evalué cada fantasma por separado
    siguiente = (agente + 1) % num_agentes(tablero)                          
    jugada_seleccionada = None                                              

    # Maximizador del algoritmo, en este paso es pacman quien evalua la jugada mas prometedora
    if agente == PACMAN:                                                     
        maximo = -math.inf # Valor máximo que utilizaremos para comparar contra Alfa más adelante
        for jugada in jugadasPosibles(tablero, agente):
            nuevo_tablero = aplicar(jugada, tablero, agente) # Evaluamos la jugada sobre un tablero nuevo para no pisar el tablero actual del juego                
            nuevo_score = minimax(profundidad + 1, nuevo_tablero, siguiente, 
                                  profundidadMaxima, alpha, beta)[1] # Evaluamos la jugada llamando recursivamente a nuestro minimax
            if nuevo_score > maximo or jugada_seleccionada is None: # Si la jugada es mejor que nuestra jugada anteriormente evaluada, la actualizamos
                maximo = nuevo_score # Actualizamos 
                jugada_seleccionada = jugada

            alpha = max(alpha, nuevo_score) # Actualizamos alfa siempre y cuándo sea mayor el valor de la jugada seleccionada a nuestra alfa actual
            if alpha >= beta: # Si alfa es mayor que beta, no vamos a encontrar jugadas que mejoren la jugada actual, entonces podemos podar las demás ramas o nodos que queden por explorar
                break
        return jugada_seleccionada, maximo # Retornamos jugada seleccionada y nuestra alfa al nodo padre

    else:                                                                    
        minimo = math.inf # Valor mínimo que utilizaremos para comparar contra Beta más adelante
        for jugada in jugadasPosibles(tablero, agente): 
            nuevo_tablero = aplicar(jugada, tablero, agente) # Evaluamos la jugada sobre un tablero nuevo para no pisar el tablero actual del juego               
            nuevo_score = minimax(profundidad + 1, nuevo_tablero, siguiente,
                                  profundidadMaxima, alpha, beta)[1] # Evaluamos la jugada llamando recursivamente a nuestro minimax
            if nuevo_score < minimo or jugada_seleccionada is None: # Si la jugada que acabamos de evaluar minimiza a la jugada anterior, guardamos la jugada y la puntuación
                minimo = nuevo_score
                jugada_seleccionada = jugada

            beta = min(beta, nuevo_score) # Actualizamos la beta siempre y cuando el valor de la jugada que hemos evaluado sea menor al valor anterior de nuestra Beta
            if alpha >= beta: # Si evaluamos que alfa es mayor que beta, podamos las ramas y nodos contiguos ya que no vamos a encontrar una jugada que mejore la actual
                break
        return jugada_seleccionada, minimo
