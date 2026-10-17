"""
record.py
---------
Récord de puntuación "de toda la vida": se guarda en un fichero de texto
(record.txt, junto al juego) para que no se pierda al cerrar el programa.

No es lógica del juego ni parte visual: es persistencia de datos, por eso
va en su propio módulo.
"""

from config import RUTA_RECORD


def cargar_record():
    """Lee el récord guardado. Si el fichero no existe o está dañado, el récord es 0."""
    try:
        with open(RUTA_RECORD, encoding="utf-8") as fichero:
            return int(fichero.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def guardar_record(puntuacion):
    """Guarda el récord. Si no se puede escribir (permisos, etc.) el juego sigue igual."""
    try:
        with open(RUTA_RECORD, "w", encoding="utf-8") as fichero:
            fichero.write(str(puntuacion))
    except OSError:
        pass
