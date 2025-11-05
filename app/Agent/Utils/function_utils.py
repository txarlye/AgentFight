"""
Funciones auxiliares reutilizables para agentes.
Consolida funciones que estaban duplicadas en diferentes archivos.
"""

import unicodedata
import re


def normalize_name(s: str) -> str:
    """
    Normaliza nombres: minúsculas sin acentos/espacios dobles.
    Útil para deduplicar nombres.
    
    Args:
        s: String a normalizar
    
    Returns:
        str: String normalizado
    """
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def clip_value(x: int, lo: int = 1, hi: int = 10) -> int:
    """
    Limita valores a un rango específico.
    
    Args:
        x: Valor a limitar
        lo: Valor mínimo (default: 1)
        hi: Valor máximo (default: 10)
    
    Returns:
        int: Valor limitado al rango [lo, hi]
    """
    try:
        v = int(x)
    except Exception:
        v = lo
    return max(lo, min(hi, v))


def slugify(s: str) -> str:
    """
    Convierte string a slug (para nombres de archivo).
    Elimina caracteres especiales y espacios.
    
    Args:
        s: String a convertir
    
    Returns:
        str: Slug generado
    """
    _slug_rx = re.compile(r"[^a-z0-9]+", re.I)
    s = (s or "").strip().lower()
    return _slug_rx.sub("-", s).strip("-") or "char"

