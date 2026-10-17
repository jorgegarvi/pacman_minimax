"""
logica/reglas.py
----------------
Reglas del juego. Son las funciones auxiliares que usa el esquema de Minimax:

    jugadasPosibles(tablero, agente)   -> lista de jugadas legales
    aplicar(jugada, tablero, agente)   -> NUEVO tablero tras la jugada
    es_final(tablero)                  -> True si la partida ha terminado

Regla de oro: el juego real usa EXACTAMENTE estas mismas funciones.
Si Minimax simulara unas reglas y el juego aplicara otras, los fantasmas
tomarían decisiones sobre un juego que no existe.

Agentes:  0 = Pac-Man (MAX)   |   1 .. número de fantasmas = fantasmas (MIN)
El número de fantasmas se elige al empezar la partida, así que el número de
agentes se calcula a partir del propio tablero: num_agentes(tablero).
"""

from config import (PUNTOS_POR_BOLITA, PUNTOS_POR_PILDORA,
                    PUNTOS_POR_FANTASMA, DURACION_SUSTO, DESCANSO_FANTASMAS_CADA,
                    ESPERA_REAPARICION)
from logica.mapa import DIRECCIONES, QUIETO, sumar

PACMAN = 0

# Un fantasma comido reaparece al menos a esta distancia (en pasos) de Pac-Man...
DISTANCIA_MINIMA_REAPARICION = 8
# ...y al menos a esta distancia de cualquier otro fantasma
SEPARACION_MINIMA_REAPARICION = 3


def num_agentes(tablero):
    """Pac-Man + los fantasmas de esta partida."""
    return 1 + len(tablero.fantasmas)


def fantasmas_descansan(tablero):
    """
    True si en esta ronda los fantasmas no se mueven.
    Con DESCANSO_FANTASMAS_CADA = 4: rondas 1, 2 y 3 se mueven, la 4 descansan,
    5, 6 y 7 se mueven, la 8 descansan... -> velocidad 3/4 respecto a Pac-Man.
    """
    return tablero.ronda % DESCANSO_FANTASMAS_CADA == 0


def esperando(tablero, indice):
    """True si el fantasma 'indice' acaba de reaparecer y aún está esperando para salir."""
    return tablero.ronda <= tablero.espera_hasta[indice]


def ronda_de_salida(ronda_reaparicion):
    """
    Hasta qué ronda espera un fantasma que reaparece en 'ronda_reaparicion':
    al menos ESPERA_REAPARICION rondas, alargadas hasta el siguiente múltiplo de
    DESCANSO_FANTASMAS_CADA. Así vuelve a moverse en el mismo punto del ciclo de
    descanso que los demás fantasmas (todos empezaron en la ronda 0), y su
    dibujo lleva exactamente el mismo retraso que el de ellos (ver visual/animacion.py).
    """
    n = DESCANSO_FANTASMAS_CADA
    minima = ronda_reaparicion + ESPERA_REAPARICION
    return ((minima + n - 1) // n) * n


def jugadasPosibles(tablero, agente):
    """
    Direcciones legales para el agente:
      - nunca hacia un muro;
      - un fantasma no puede entrar en la casilla de otro fantasma;
      - Pac-Man SÍ puede entrar en la casilla de un fantasma (y lo capturan,
        o se lo come si está asustado);
      - en las rondas de descanso, la única jugada de un fantasma es QUIETO;
      - un fantasma recién reaparecido también se queda QUIETO mientras espera;
      - un fantasma NO puede dar media vuelta (volver por donde ha venido)
        salvo que no tenga otra salida. Es la regla del Pac-Man original y
        evita que los fantasmas "tiemblen" yendo y viniendo en un pasillo.
    Si no hay ninguna salida, la única jugada es QUIETO
    (así el bucle de Minimax nunca se queda sin jugadas).
    """
    if agente != PACMAN and (fantasmas_descansan(tablero) or esperando(tablero, agente - 1)):
        return [QUIETO]

    if agente == PACMAN:
        origen = tablero.pacman
        ocupadas = ()
    else:
        origen = tablero.fantasmas[agente - 1]
        ocupadas = [f for i, f in enumerate(tablero.fantasmas) if i != agente - 1]

    jugadas = []
    for direccion in DIRECCIONES:
        destino = sumar(origen, direccion)
        if not tablero.mapa.es_muro(destino) and destino not in ocupadas:
            jugadas.append(direccion)

    # Regla de no dar media vuelta (solo fantasmas, y solo si hay alternativa)
    if agente != PACMAN and len(jugadas) > 1:
        ultima = tablero.direcciones[agente - 1]
        media_vuelta = (-ultima[0], -ultima[1])
        if ultima != QUIETO and media_vuelta in jugadas:
            jugadas.remove(media_vuelta)

    if not jugadas:
        jugadas.append(QUIETO)
    return jugadas


def aplicar(jugada, tablero, agente):
    """
    Devuelve un NUEVO tablero con la jugada aplicada. El original no se toca.
    (Es la corrección 2 del esquema de clase: trabajar sobre una copia.)

    Contacto (regla A): si tras el movimiento un fantasma y Pac-Man están en
    la misma casilla:
      - fantasma normal   -> Pac-Man queda capturado;
      - fantasma asustado -> Pac-Man se lo come (ver _comer_fantasma).
    """
    nuevo = tablero.copiar()

    if agente == PACMAN:
        nuevo.ronda += 1          # cada movimiento de Pac-Man abre una ronda nueva

        # El susto se consume una ronda; al acabar, ningún fantasma está asustado.
        if nuevo.susto > 0:
            nuevo.susto -= 1
            if nuevo.susto == 0:
                nuevo.asustados = tuple(False for _ in nuevo.fantasmas)

        nuevo.pacman = sumar(tablero.pacman, jugada)
        if nuevo.pacman in nuevo.fantasmas:
            _contacto(nuevo, nuevo.fantasmas.index(nuevo.pacman))
        if not nuevo.capturado:
            if nuevo.pacman in nuevo.puntos:
                nuevo.puntos = nuevo.puntos - {nuevo.pacman}   # frozenset nuevo, sin esa bolita
                nuevo.marcador += PUNTOS_POR_BOLITA
            elif nuevo.pacman in nuevo.pildoras:
                nuevo.pildoras = nuevo.pildoras - {nuevo.pacman}
                nuevo.marcador += PUNTOS_POR_PILDORA
                _asustar_fantasmas(nuevo)
    else:
        indice = agente - 1
        destino = sumar(tablero.fantasmas[indice], jugada)
        fantasmas = list(nuevo.fantasmas)
        fantasmas[indice] = destino
        nuevo.fantasmas = tuple(fantasmas)
        if jugada != QUIETO:      # en descanso conserva la dirección que llevaba
            _cambiar_direccion(nuevo, indice, jugada)
        if destino == nuevo.pacman:
            _contacto(nuevo, indice)

    return nuevo


def _contacto(nuevo, indice):
    """Pac-Man y el fantasma 'indice' están en la misma casilla."""
    if nuevo.asustados[indice]:
        _comer_fantasma(nuevo, indice)
    else:
        nuevo.capturado = True


def _asustar_fantasmas(nuevo):
    """
    Pac-Man se ha comido una píldora: todos los fantasmas se asustan durante
    DURACION_SUSTO rondas y, como en el original, dan media vuelta
    (se borra su última dirección, así que pueden volver por donde venían).
    """
    nuevo.susto = DURACION_SUSTO
    nuevo.asustados = tuple(True for _ in nuevo.fantasmas)
    nuevo.direcciones = tuple(QUIETO for _ in nuevo.fantasmas)


def _comer_fantasma(nuevo, indice):
    """
    Pac-Man se come al fantasma asustado: suma puntos y el fantasma reaparece,
    ya sin susto, en la casilla de reaparición (ver _casilla_reaparicion).
    """
    nuevo.marcador += PUNTOS_POR_FANTASMA

    fantasmas = list(nuevo.fantasmas)
    fantasmas[indice] = _casilla_reaparicion(nuevo, indice)
    nuevo.fantasmas = tuple(fantasmas)

    asustados = list(nuevo.asustados)
    asustados[indice] = False
    nuevo.asustados = tuple(asustados)
    _cambiar_direccion(nuevo, indice, QUIETO)

    espera_hasta = list(nuevo.espera_hasta)
    espera_hasta[indice] = ronda_de_salida(nuevo.ronda)
    nuevo.espera_hasta = tuple(espera_hasta)


def _casilla_reaparicion(nuevo, indice):
    """
    Dónde reaparece un fantasma comido:
      - nunca encima de otro fantasma (ni de Pac-Man), y al menos a
        SEPARACION_MINIMA_REAPARICION pasos de cualquier otro fantasma (así
        tampoco coincide con el dibujo de otro, que va algo retrasado);
      - lo más LEJOS posible de Pac-Man (distancia real, tabla BFS), para que
        reaparecer no le ponga un fantasma encima y no suba la dificultad.
    Primero se mira entre las 4 salidas del mapa (las esquinas, aunque se juegue
    con menos fantasmas). Si ninguna salida libre está al menos a
    DISTANCIA_MINIMA_REAPARICION pasos de Pac-Man, se busca en todo el mapa.
    Si hay empate, la primera de la lista: así es determinista y Minimax puede
    simularlo exactamente igual que el juego real.
    """
    tabla = nuevo.mapa.distancias
    otros = [f for i, f in enumerate(nuevo.fantasmas) if i != indice]
    distancias = tabla[nuevo.pacman]

    def libre(casilla):
        return (casilla != nuevo.pacman and
                all(tabla[f][casilla] >= SEPARACION_MINIMA_REAPARICION for f in otros))

    candidatas = [c for c in nuevo.mapa.inicios_fantasmas
                  if libre(c) and distancias[c] >= DISTANCIA_MINIMA_REAPARICION]
    if not candidatas:
        candidatas = [c for c in nuevo.mapa.casillas_libres() if libre(c)]
    if not candidatas:                                  # mapa casi lleno: basta con que no se solape
        candidatas = [c for c in nuevo.mapa.casillas_libres() if c != nuevo.pacman and c not in otros]
    return max(candidatas, key=lambda casilla: distancias[casilla])


def _cambiar_direccion(nuevo, indice, direccion):
    """Guarda la última dirección del fantasma 'indice' (la usa la regla de no dar media vuelta)."""
    direcciones = list(nuevo.direcciones)
    direcciones[indice] = direccion
    nuevo.direcciones = tuple(direcciones)


def es_final(tablero):
    """La partida termina si capturan a Pac-Man o si no queda comida (bolitas ni píldoras)."""
    return tablero.capturado or (not tablero.puntos and not tablero.pildoras)


def elegir_movimiento_pacman(tablero, deseada, actual):
    """
    Movimiento del jugador humano en el juego real (no se usa dentro de Minimax):
      1. la última dirección pulsada, si es legal;
      2. si no, seguir en la dirección actual, si es legal;
      3. si no, quedarse quieto (está contra una pared).
    Guardar la dirección deseada permite pulsar el giro antes de llegar al cruce.
    """
    legales = jugadasPosibles(tablero, PACMAN)
    if deseada in legales:
        return deseada
    if actual in legales:
        return actual
    return QUIETO
