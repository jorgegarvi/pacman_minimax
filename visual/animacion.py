"""
visual/animacion.py
-------------------
Movimiento SUAVE de los fantasmas (solo visual).

Problema: por la regla de velocidad (N-1)/N, cada fantasma avanza una casilla
varios ticks seguidos y en uno de cada N descansa (QUIETO). Interpolando tick
a tick se ve "avanzar, avanzar, ..., pararse".

Solución: el dibujo recorre el CAMINO que ha seguido el fantasma (la lista
de casillas por las que ha pasado) a velocidad CONSTANTE, con un tick de
retraso:

    distancia recorrida por el dibujo = velocidad * (t - inicio - 1)

    velocidad = (N - 1) / N casillas por tick     (N = DESCANSO_FANTASMAS_CADA; con N = 4 -> 3/4)
    t         = ticks transcurridos desde la salida, con decimales

Con ese tick de retraso el dibujo nunca alcanza a la posición lógica, así que
nunca tiene que esperar: los N-1 pasos quedan repartidos entre los N ticks.

Importante: esto solo funciona si el fantasma empieza a moverse al principio
del ciclo de descanso (ronda 0, N, 2N...). Por eso un fantasma comido espera
en su casilla de reaparición hasta una ronda múltiplo de N (reglas.ronda_de_salida):
así todos los fantasmas van en la misma fase y sus dibujos llevan el mismo
retraso, sin pausas y sin que un dibujo se monte encima de otro.

Si un fantasma se queda bloqueado (encajonado entre otros) y pierde un paso,
su dibujo hace una única pausa del tiempo que tarda en recorrer una casilla y
vuelve a quedar acompasado. Sin esa pausa, el desfase se arrastraría para
siempre y el dibujo se pararía en cada ciclo.

Coste: el dibujo va hasta ~1 casilla por detrás de la casilla real.
La lógica y Minimax NO se ven afectados: siguen usando la casilla real.
"""


class AnimadorFantasmas:

    def __init__(self, descanso_cada):
        self.descanso_cada = descanso_cada
        self.velocidad = (descanso_cada - 1) / descanso_cada   # casillas por tick
        self.caminos = []          # por fantasma: casillas por las que ha pasado desde que empezó su camino
        self.inicios = []          # por fantasma: instante (en ticks) en que empezó a moverse
        self.pausas = []           # por fantasma: ticks de pausa pendientes (tras un bloqueo)

    def reiniciar(self, casillas):
        """Inicio de partida o tras perder una vida: cada camino empieza en su casilla, en la ronda 0."""
        self.caminos = [[casilla] for casilla in casillas]
        self.inicios = [0.0 for _ in casillas]
        self.pausas = [0.0 for _ in casillas]

    def registrar(self, estado):
        """
        Tras cada tick, para cada fantasma:
          - si se ha movido a una casilla contigua, se añade a su camino;
          - si ha saltado a una casilla no contigua, ha reaparecido (se lo ha
            comido Pac-Man): su camino empieza de nuevo ahí y vuelve a moverse
            cuando termine su espera (estado.espera_hasta), que siempre coincide
            con el principio de un ciclo de descanso, igual que la ronda 0;
          - si NO se ha movido en una ronda en la que le tocaba moverse (estaba
            bloqueado por otros fantasmas), ha perdido un paso respecto al resto:
            su dibujo hará una pausa de 1 / velocidad ticks (lo que tarda en
            recorrer una casilla) para volver a ir acompasado con su fantasma.
        """
        descanso = estado.ronda % self.descanso_cada == 0      # misma regla que reglas.fantasmas_descansan
        for i, casilla in enumerate(estado.fantasmas):
            ultima = self.caminos[i][-1]
            if casilla == ultima:
                if not descanso and estado.ronda > estado.espera_hasta[i]:
                    self.pausas[i] += 1 / self.velocidad
            elif abs(casilla[0] - ultima[0]) + abs(casilla[1] - ultima[1]) == 1:
                self.caminos[i].append(casilla)
            else:
                self.caminos[i] = [casilla]
                self.inicios[i] = float(estado.espera_hasta[i])
                self.pausas[i] = 0.0

    def actualizar(self, ticks):
        """
        Avanza las pausas pendientes. Mientras un fantasma está en pausa, su
        instante de inicio se retrasa al mismo ritmo que pasa el tiempo, así
        que su dibujo se queda quieto sin dar saltos hacia atrás.
        """
        for i in range(len(self.pausas)):
            if self.pausas[i] > 0:
                consumido = min(self.pausas[i], ticks)
                self.pausas[i] -= consumido
                self.inicios[i] += consumido

    def posicion(self, indice, t):
        """
        Posición dibujada del fantasma 'indice' en el instante t (en ticks),
        en "unidades de casilla" con decimales: (2.0, 5.5) está entre (2, 5) y (2, 6).
        """
        camino = self.caminos[indice]
        recorrido = self.velocidad * (t - self.inicios[indice] - 1)   # 1 tick de retraso
        recorrido = max(0.0, min(recorrido, len(camino) - 1))       # nunca más allá de la casilla real

        tramo = int(recorrido)                 # entre qué dos casillas del camino está
        if tramo >= len(camino) - 1:
            fila, col = camino[-1]
            return float(fila), float(col)
        fraccion = recorrido - tramo
        (f0, c0), (f1, c1) = camino[tramo], camino[tramo + 1]
        return f0 + (f1 - f0) * fraccion, c0 + (c1 - c0) * fraccion
