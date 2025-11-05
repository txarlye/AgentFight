"""
Utilidades de rutas y archivos.
Consolida funciones de manejo de rutas que estaban duplicadas.
"""

from pathlib import Path


def get_project_root() -> Path:
    """
    Obtiene la raíz del proyecto.
    Desde app/Agent/ -> sube 2 niveles hasta la raíz del proyecto.
    
    Returns:
        Path: Ruta absoluta a la raíz del proyecto
    """
    # Desde app/Agent/Utils/ -> sube 3 niveles hasta la raíz
    return Path(__file__).resolve().parents[3]


def ensure_directory(path: Path) -> None:
    """
    Crea un directorio si no existe.
    
    Args:
        path: Ruta del directorio a crear
    """
    path.mkdir(parents=True, exist_ok=True)

