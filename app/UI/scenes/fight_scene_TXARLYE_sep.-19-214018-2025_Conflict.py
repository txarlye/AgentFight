# app/UI/scenes/fight_scene.py
import threading
import pygame as pg
from settings.settings import settings
from app.Agent import orchestrator
from app.UI.pg_assets import draw_background, pick_random_bg
from .base_scene import BaseScene

try:
    from app.Agent.agent_character_creator import create_candidates
except Exception:
    create_candidates = None

# Fallback local
from app.domain.character import Character
import random
def _fake_candidates(n=1):
    names = ["Kumo","Raven","Sable","Lyra","Orion","Vex","Tara","Jin"]
    weap  = ["nunchaku","hacha","katana","dagas","bastón","guantes"]
    out = []
    for _ in range(n):
        out.append(Character(
            name=random.choice(names)+f"_{random.randint(1,99)}",
            damage=random.randint(3,9),
            resistence=random.randint(2,8),
            weapon=random.choice(weap),
            description="Combatiente placeholder."
        ))
    return out

class FightScene(BaseScene):
    def __init__(self, app):
        super().__init__(app)
        self.bg = None
        self.enemy = None
        self.p_hp = 100
        self.e_hp = 100

        # Rects placeholders
        self.player_rect = pg.Rect(160, settings.HEIGHT-220, 80, 160)
        self.enemy_rect  = pg.Rect(settings.WIDTH-240, settings.HEIGHT-220, 80, 160)

        # Prefetch para la próxima ronda
        self._prefetch_enemy = None
        self._prefetch_bg    = None
        self._prefetching    = False

    def enter(self):
        # Si no hay player, vuelve a selección
        p = settings.Player_selected_Player
        if not p or not getattr(p, "name", "").strip():
            self.app.set_scene("show_menu_select_character")
            
            return

        # Fondo inicial (si hay imágenes en carpeta)
        self.bg = pick_random_bg(settings.BG_FIGHT_DIR, (settings.WIDTH, settings.HEIGHT)) or None

        # Enemigo inicial
        self.enemy = self._prefetch_enemy or self._make_enemy()
        self._prefetch_enemy = None
        self.reset_round()

        # Arranca el prefetch para el siguiente
        self._start_prefetch()
        # El prefetch de historia ya se hizo en la selección de personaje

    def handle_event(self, e):
        if e.type == pg.KEYDOWN:
            if e.key == pg.K_ESCAPE:
                self.app.set_scene("show_principal_menu")
            elif e.key == pg.K_r:
                self.reset_round()
            elif e.key == pg.K_n:
                self._next_round()
            elif e.key == pg.K_SPACE:
                # ataque player → enemy
                p = settings.Player_selected_Player
                if self.enemy and self.e_hp > 0 and self.p_hp > 0 and p:
                    dmg = max(1, p.damage - self.enemy.resistence // 3)
                    self.e_hp = max(0, self.e_hp - dmg)
            elif e.key == pg.K_e:
                # ataque enemy → player
                p = settings.Player_selected_Player
                if self.enemy and self.e_hp > 0 and self.p_hp > 0 and p:
                    dmg = max(1, self.enemy.damage - p.resistence // 3)
                    self.p_hp = max(0, self.p_hp - dmg)

    def update(self, dt):
        pass

    def draw(self, screen):
        draw_background(screen, self.bg, (20,40,70))

        # HUD
        p = settings.Player_selected_Player
        pname = p.name if p else "???"
        ename = self.enemy.name if self.enemy else "???"
        self.text(screen, f"Player: {pname}", (40,20))
        self.text(screen, f"Enemy : {ename}", (settings.WIDTH-360,20))
        self._draw_bar(screen, 40, 50, 300, 16, self.p_hp, (80,200,120))
        self._draw_bar(screen, settings.WIDTH-340, 50, 300, 16, self.e_hp, (220,90,90))

        # suelo + placeholders
        pg.draw.rect(screen, (90,90,100), (0, settings.HEIGHT-40, settings.WIDTH, 40))
        pg.draw.rect(screen, (90,150,240), self.player_rect)
        pg.draw.rect(screen, (240,90,90),  self.enemy_rect)

        if self.e_hp <= 0 or self.p_hp <= 0:
            msg = "VICTORY!" if self.e_hp <= 0 else "DEFEAT..."
            self.text(screen, msg + "  (R reset, ESC menú, N nueva ronda)",
                      (120, settings.HEIGHT//2 - 12), big=True)

    # -------- helpers --------
    def _draw_bar(self, screen, x, y, w, h, hp, color):
        pg.draw.rect(screen, (60,60,60), (x, y, w, h))
        pg.draw.rect(screen, color, (x, y, int(w*(hp/100.0)), h))

    def reset_round(self):
        self.p_hp = 100
        self.e_hp = 100

    def _make_enemy(self):
        if create_candidates:
            try:
                return create_candidates(1)[0]
            except Exception:
                pass
        return _fake_candidates(1)[0]

    def _start_prefetch(self):
        if self._prefetching:
            return
        self._prefetching = True

        def worker():
            try:
                self._prefetch_enemy = self._make_enemy()
                self._prefetch_bg = pick_random_bg(
                    settings.BG_FIGHT_DIR, (settings.WIDTH, settings.HEIGHT)
                )
            finally:
                self._prefetching = False

        threading.Thread(target=worker, daemon=True).start()

    def _next_round(self):
        # Usa lo prefetched si está listo; si no, crea al vuelo
        self.enemy = self._prefetch_enemy or self._make_enemy()
        self.bg = self._prefetch_bg or pick_random_bg(
            settings.BG_FIGHT_DIR, (settings.WIDTH, settings.HEIGHT)
        )
        self._prefetch_enemy = None
        self._prefetch_bg = None
        self.reset_round()
        self._start_prefetch()
