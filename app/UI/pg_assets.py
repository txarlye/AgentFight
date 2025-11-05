import os, random
import pygame as pg

_BG_CACHE = {}

def load_background(path: str, size: tuple[int,int], alpha: bool = False):
    """Carga y escala; si falla, devuelve None."""
    try:
        img = pg.image.load(path)
        img = img.convert_alpha() if alpha else img.convert()
        return pg.transform.scale(img, size)
    except Exception:
        return None

def load_background_cached(path: str, size: tuple[int,int], alpha: bool = False):
    key = (path, size, alpha)
    surf = _BG_CACHE.get(key)
    if surf is None:
        surf = load_background(path, size, alpha)
        _BG_CACHE[key] = surf
    return surf

def draw_background(screen: pg.Surface, bg_surf, fallback_color=(28,28,35)):
    if bg_surf is not None:
        screen.blit(bg_surf, (0, 0))
    else:
        screen.fill(fallback_color)

def pick_random_bg(directory: str, size: tuple[int,int], alpha: bool = False):
    """Elige aleatorio de la carpeta; si no hay, None."""
    try:
        files = [f for f in os.listdir(directory)
                 if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
        if not files:
            return None
        path = os.path.join(directory, random.choice(files))
        return load_background_cached(path, size, alpha)
    except Exception:
        return None

def draw_photo_frame(screen: pg.Surface, rect: pg.Rect, color=(200,200,200)):
    """Marco simple para ‘slot’ de candidato."""
    pg.draw.rect(screen, color, rect, width=2, border_radius=8)

