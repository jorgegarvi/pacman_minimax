"""
logica/distancias.py
--------------------
Tabla de distancias REALES (en pasos, rodeando muros) entre todas las
casillas libres del mapa.

Se calcula UNA sola vez al cargar el mapa, lanzando un BFS desde cada casilla.
Durante la partida, saber la distancia entre dos casillas es solo leer la tabla:

    distancia = mapa.distancias[origen][destino]

Por qué precalcular: puntuacion() se ejecuta en cada hoja del árbol de
Minimax (miles de veces por tick). Hacer un BFS en cada hoja sería
muchísimo más lento; como los muros no cambian, las distancias tampoco.
"""

from collections import deque


def bfs_desde(mapa, origen):
    """
    Distancia mínima desde 'origen' a todas las casillas alcanzables.

    BFS (búsqueda en anchura) explora por niveles: primero las casillas a
    1 paso, luego las de 2, etc. Como cada paso cuesta lo mismo, la primera
    vez que llega a una casilla, ese nivel ES la distancia mínima.
    """
    distancias = {origen: 0}
    cola = deque([origen])
    while cola:
        actual = cola.popleft()                  # sale la más antigua: se respetan los niveles
        for vecina in mapa.vecinas(actual):      # solo casillas que no son muro
            if vecina not in distancias:         # primera vez que se alcanza = distancia mínima
                distancias[vecina] = distancias[actual] + 1
                cola.append(vecina)
    return distancias


def calcular_distancias(mapa):
    """Tabla completa: un BFS desde cada casilla libre."""
    tabla = {}
    for casilla in mapa.casillas_libres():
        tabla[casilla] = bfs_desde(mapa, casilla)
    return tabla
