"""
logica/evaluacion.py
--------------------
Función de evaluación: puntuacion(tablero, profundidad).

Da un número a cada HOJA del árbol de Minimax, siempre desde el punto de
vista de Pac-Man:
    número alto  -> bueno para Pac-Man        (MAX lo busca)
    número bajo  -> bueno para los fantasmas  (MIN lo busca)

OJO: esto NO es la poda. La poda alfa-beta usa estos números, ya propagados
hacia arriba, para saltarse ramas. Si la puntuación es mala, la poda funciona
igual de bien, pero los fantasmas toman malas decisiones.

Los fantasmas se dividen en dos grupos:
    amenazas = fantasmas normales     -> Pac-Man quiere tenerlos LEJOS
    presas   = fantasmas asustados    -> Pac-Man quiere tenerlos CERCA (se los puede comer)

Términos (todos desde el punto de vista de Pac-Man):

    + PESO_MAS_CERCANO   * distancia a la amenaza más cercana     (peligro inmediato)
    + PESO_SUMA          * suma de distancias a las amenazas      (que todas se acerquen)
    + PESO_ZONA          * casillas de la zona segura             (ENCIERRO)
    + PESO_BOLITAS_ZONA  * comida dentro de la zona segura        (comida que puede alcanzar tranquilo)
    - PESO_CAZA          * suma de distancias a las presas        (signo INVERTIDO: ahora cerca es bueno)
    + PESO_MARCADOR      * marcador                               (bolitas, píldoras y fantasmas comidos)
"""

from config import DESCANSO_FANTASMAS_CADA

# Valor de un estado final. Tiene que ser mucho mayor que cualquier valor
# que pueda dar la parte heurística, para que ganar o perder pese siempre más.
VALOR_FINAL = 100000

PESO_MAS_CERCANO = 10
PESO_SUMA = 1
PESO_ZONA = 2
PESO_BOLITAS_ZONA = 2
PESO_CAZA = 3
PESO_MARCADOR = 0.5

# La zona segura solo se mide en las casillas a este número de pasos de Pac-Man
# o menos: mide el encierro de Pac-Man, no quién controla el mapa entero.
RADIO_ZONA = 6

# Los fantasmas recorren (N-1)/N casillas por ronda (3/4 con N = 4):
# para recorrer d casillas necesitan d / VELOCIDAD_FANTASMAS rondas.
VELOCIDAD_FANTASMAS = (DESCANSO_FANTASMAS_CADA - 1) / DESCANSO_FANTASMAS_CADA


def zona_segura(tablero, amenazas):
    """
    Casillas cercanas a Pac-Man (a RADIO_ZONA pasos o menos) a las que llega
    ANTES que cualquier fantasma amenaza (teniendo en cuenta que los fantasmas
    son más lentos).

    Es la medida del ENCIERRO: en campo abierto la zona está casi completa;
    cuando los fantasmas le cierran las salidas por los dos lados, se reduce
    al trozo de pasillo que queda entre ellos.

    Por qué solo alrededor de Pac-Man: si se midiera en todo el mapa, a un
    fantasma lejano le compensaría colocarse en el centro (desde ahí "controla"
    más casillas) en vez de perseguir, y daría vueltas al centro.

    Devuelve (número de casillas, comida dentro de la zona).
    Solo hace lecturas de la tabla de distancias BFS: no lanza ningún BFS.
    """
    distancias = tablero.mapa.distancias
    desde_pacman = distancias[tablero.pacman]
    desde_amenazas = [distancias[f] for f in amenazas]

    casillas = 0
    comida = 0
    for casilla, pasos_pacman in desde_pacman.items():
        if pasos_pacman > RADIO_ZONA:
            continue
        if desde_amenazas:
            rondas_fantasma = min(d[casilla] for d in desde_amenazas) / VELOCIDAD_FANTASMAS
            if pasos_pacman >= rondas_fantasma:
                continue                     # un fantasma llega antes o a la vez: no es segura
        casillas += 1
        if casilla in tablero.puntos or casilla in tablero.pildoras:
            comida += 1
    return casillas, comida


def puntuacion(tablero, profundidad):
    """
    profundidad = en qué nivel del árbol está esta hoja (0 = raíz).
    Solo se usa en los estados finales: una captura más cercana vale más
    para los fantasmas que una lejana.
    """
    # --- Estados finales ---------------------------------------------------
    if tablero.capturado:
        # -100000 + profundidad: capturar en el nivel 2 (-99998) es MÁS bajo
        # que capturar en el nivel 6 (-99994). Así los fantasmas eligen la
        # captura más rápida y Pac-Man, si no puede evitarla, la retrasa.
        return -VALOR_FINAL + profundidad
    if not tablero.puntos and not tablero.pildoras:
        return VALOR_FINAL - profundidad

    distancias = tablero.mapa.distancias
    amenazas = [f for f, asustado in zip(tablero.fantasmas, tablero.asustados) if not asustado]
    presas = [f for f, asustado in zip(tablero.fantasmas, tablero.asustados) if asustado]

    # --- Persecución: distancias reales a las amenazas (tabla BFS) ---------
    persecucion = 0
    if amenazas:
        d = [distancias[f][tablero.pacman] for f in amenazas]
        persecucion = PESO_MAS_CERCANO * min(d) + PESO_SUMA * sum(d)

    # --- Encierro: zona segura alrededor de Pac-Man ------------------------
    # Dos fantasmas juntos cubren menos que separados, así que este término
    # hace que se REPARTAN y ataquen por lados distintos sin ninguna regla extra.
    casillas_zona, comida_zona = zona_segura(tablero, amenazas)
    encierro = PESO_ZONA * casillas_zona + PESO_BOLITAS_ZONA * comida_zona

    # --- Caza: fantasmas asustados (el signo se invierte) ------------------
    # Para Pac-Man ahora es bueno estar CERCA; los fantasmas asustados
    # minimizan, así que con el mismo Minimax huyen de él.
    caza = -PESO_CAZA * sum(distancias[f][tablero.pacman] for f in presas)

    # --- Progreso de Pac-Man ------------------------------------------------
    # Bolitas, píldoras y fantasmas comidos suben el marcador. Así, dentro del
    # árbol, el Pac-Man simulado va a por la comida (como un jugador real) y
    # aprovecha las píldoras, en vez de solo huir.
    progreso = PESO_MARCADOR * tablero.marcador

    return persecucion + encierro + caza + progreso
