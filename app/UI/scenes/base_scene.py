import pygame as pg
from settings.settings import settings

class BaseScene:
    def __init__(self, app):
        self.app = app
        # fuentes “preset”
        self.font = pg.font.SysFont(settings.FONT_NAME, 22)
        self.big  = pg.font.SysFont(settings.FONT_NAME, 28, bold=True)
        # ✅ caché para fuentes de tamaño/estilo variables
        self._font_cache: dict[tuple[int, bool], pg.font.Font] = {}

    def enter(self): ...
    def exit(self): ...
    def handle_event(self, e): ...
    def update(self, dt): ...
    def draw(self, screen): ...

    def _get_font(self, size: int, bold: bool):
        key = (size, bool(bold))
        f = self._font_cache.get(key)
        if f is None:
            f = pg.font.SysFont(settings.FONT_NAME, size, bold=bold)
            self._font_cache[key] = f
        return f

    def text(self, screen, s, pos, big=False, color=(240,240,240), size=None, bold=None):
        """
        - Si pasas size, se ignora `big` y usas ese tamaño.
        - Si pasas size y NO pasas bold, por defecto bold=False (no negrita).
        """
        if size is not None:
            b = False if bold is None else bool(bold)
            f = self._get_font(size, b)
        else:
            f = self.big if big else self.font
        screen.blit(f.render(s, True, color), pos)
