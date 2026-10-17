"""
logica/estado.py
----------------
Parte DINÁMICA del juego: todo lo que cambia con cada movimiento.

En Minimax, un Estado es el 'tablero' del esquema de clase.

Todos sus atributos son inmutables (tuplas, frozenset, int, bool) y el Mapa
se comparte. Por eso copiar un Estado es solo copiar unas pocas referencias:
muy barato, que es justo lo que hace falta porque Minimax crea miles de
estados en cada decisión.
"""


class Estado:

    def __init__(self, mapa, pacman, fantasmas, puntos, pildoras, marcador, vidas,
                 capturado=False, ronda=0, direcciones=None, susto=0, asustados=None,
                 espera_hasta=None):
        self.mapa = mapa              # referencia al Mapa (compartido, no se copia)
        self.pacman = pacman          # casilla (fila, col) de Pac-Man
        self.fantasmas = fantasmas    # tupla de casillas; el fantasma k está en fantasmas[k - 1]
        self.puntos = puntos          # frozenset de casillas que aún tienen bolita
        self.pildoras = pildoras      # frozenset de casillas que aún tienen píldora de poder
        self.marcador = marcador      # puntuación del jugador
        self.vidas = vidas            # vidas restantes
        self.capturado = capturado    # True si un fantasma ha atrapado a Pac-Man
        self.ronda = ronda            # rondas jugadas (sube cada vez que mueve Pac-Man);
                                      # decide en qué rondas descansan los fantasmas
        # Última dirección en la que se movió cada fantasma (para la regla de
        # no dar media vuelta). Al salir, ninguna: QUIETO = (0, 0).
        if direcciones is None:
            direcciones = tuple((0, 0) for _ in fantasmas)
        self.direcciones = direcciones
        # Píldoras de poder: rondas de susto que quedan (0 = nadie asustado)
        # y qué fantasmas están asustados (uno comido deja de estarlo).
        self.susto = susto
        if asustados is None:
            asustados = tuple(False for _ in fantasmas)
        self.asustados = asustados
        # Fantasmas recién reaparecidos: el fantasma i no se mueve mientras
        # ronda <= espera_hasta[i]. Al salir, nadie espera (-1).
        if espera_hasta is None:
            espera_hasta = tuple(-1 for _ in fantasmas)
        self.espera_hasta = espera_hasta

    @classmethod
    def inicial(cls, mapa, vidas, num_fantasmas):
        """Estado al empezar la partida, con 'num_fantasmas' fantasmas (salidas 1..N del mapa)."""
        return cls(mapa, mapa.inicio_pacman, mapa.inicios_fantasmas[:num_fantasmas],
                   mapa.puntos_iniciales, mapa.pildoras_iniciales, 0, vidas)

    def copiar(self):
        """Copia barata: los atributos son inmutables, así que basta con compartirlos."""
        return Estado(self.mapa, self.pacman, self.fantasmas, self.puntos, self.pildoras,
                      self.marcador, self.vidas, self.capturado, self.ronda,
                      self.direcciones, self.susto, self.asustados, self.espera_hasta)

    def comida_restante(self):
        """Bolitas + píldoras que quedan. La partida se gana cuando llega a 0."""
        return len(self.puntos) + len(self.pildoras)

    def perder_vida(self):
        """
        Nuevo estado tras una captura cuando aún quedan vidas:
        los agentes vuelven a su posición inicial, la comida ya comida no
        vuelve, y el contador de rondas, las direcciones, el susto y las esperas se reinician.
        """
        salidas = self.mapa.inicios_fantasmas[:len(self.fantasmas)]
        return Estado(self.mapa, self.mapa.inicio_pacman, salidas,
                      self.puntos, self.pildoras, self.marcador, self.vidas - 1)
