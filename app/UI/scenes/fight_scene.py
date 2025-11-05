# app/UI/scenes/fight_scene.py
import threading
import pygame as pg
from settings.settings import settings
from app.Agent import orchestrator
from app.UI.pg_assets import draw_background, pick_random_bg
from .base_scene import BaseScene
from app.Agent.background_manager import background_manager
from app.domain.physics import PhysicsEngine, PhysicsBody, ActionState
from app.Agent.agent_enemy_ai import create_enemy_ai, EnemyAI
from app.UI.sprite_renderer import sprite_renderer

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

        # Sistema de físicas
        self.physics_engine = PhysicsEngine(settings.WIDTH, settings.HEIGHT)
        self.player_body = None
        self.enemy_body = None
        self.enemy_ai = None

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

        # Inicializar cuerpos físicos
        self._init_physics_bodies()

        # Fondo inicial usando BackgroundManager
        self.bg = self._get_background()

        # Enemigo inicial
        self.enemy = self._prefetch_enemy or self._make_enemy()
        self._prefetch_enemy = None
        
        # Configurar IA del enemigo
        if self.enemy and self.enemy_body:
            self.enemy_ai = create_enemy_ai(self.enemy, self.enemy_body, "NORMAL")
            self.enemy_ai.set_target(self.player_body)
        
        # Cargar sprites de los personajes
        self._load_character_sprites()
        
        self.reset_round()

        # Arranca el prefetch para el siguiente
        self._start_prefetch()

    def _init_physics_bodies(self):
        """Inicializa los cuerpos físicos del jugador y enemigo."""
        ground_y = settings.HEIGHT - 100  # 100px desde abajo
        
        # Cuerpo del jugador
        self.player_body = PhysicsBody(
            x=160,
            y=ground_y - 160,  # Altura del personaje
            width=80,
            height=160,
            facing_right=True,
            GROUND_Y=ground_y
        )
        
        # Cuerpo del enemigo
        self.enemy_body = PhysicsBody(
            x=settings.WIDTH-240,
            y=ground_y - 160,
            width=80,
            height=160,
            facing_right=False,
            GROUND_Y=ground_y
        )
        
        self.physics_engine.add_body(self.player_body)
        self.physics_engine.add_body(self.enemy_body)
    
    def _load_character_sprites(self):
        """Carga los sprites de los personajes."""
        # Cargar sprites del jugador
        player = settings.Player_selected_Player
        if player:
            sprite_renderer.load_character_sprites(player)
        
        # Cargar sprites del enemigo
        if self.enemy:
            sprite_renderer.load_character_sprites(self.enemy)

    def _get_background(self):
        """Obtiene el fondo usando el BackgroundManager."""
        player = settings.Player_selected_Player
        if not player or not self.enemy:
            return pick_random_bg(settings.BG_FIGHT_DIR, (settings.WIDTH, settings.HEIGHT))
        
        try:
            bg_path = background_manager.get_combat_background(player, self.enemy)
            return bg_path
        except Exception as e:
            print(f"[FightScene] Error getting background: {e}")
            return pick_random_bg(settings.BG_FIGHT_DIR, (settings.WIDTH, settings.HEIGHT))

    def handle_event(self, e):
        if e.type == pg.KEYDOWN:
            if e.key == pg.K_ESCAPE:
                self.app.set_scene("show_principal_menu")
            elif e.key == pg.K_r:
                self.reset_round()
            elif e.key == pg.K_n:
                self._next_round()
            elif e.key == pg.K_SPACE:
                self._player_attack()
            elif e.key == pg.K_e:
                self._enemy_attack()
            elif e.key == pg.K_LEFT:
                self.player_body.move_left(8.0)  # Velocidad constante
            elif e.key == pg.K_RIGHT:
                self.player_body.move_right(8.0)
            elif e.key == pg.K_UP:
                self.player_body.jump()
        
        # Detener movimiento al soltar teclas
        elif e.type == pg.KEYUP:
            if e.key in [pg.K_LEFT, pg.K_RIGHT]:
                self.player_body.velocity_x = 0

    def update(self, dt):
        # Actualizar física
        self.physics_engine.update(dt)
        
        # Actualizar IA del enemigo
        if self.enemy_ai and self.e_hp > 0:
            actions = self.enemy_ai.update(dt, self.physics_engine)
            self._execute_enemy_actions(actions)
        
        # Verificar colisiones y aplicar daño
        self._check_collisions()

    def _execute_enemy_actions(self, actions):
        """Ejecuta las acciones determinadas por la IA del enemigo."""
        if actions.get('move_left'):
            self.enemy_body.move_left()
        if actions.get('move_right'):
            self.enemy_body.move_right()
        if actions.get('jump'):
            self.enemy_body.jump()
        if actions.get('attack'):
            self._enemy_attack()

    def _check_collisions(self):
        """Verifica colisiones entre jugador y enemigo."""
        if not self.player_body or not self.enemy_body:
            return
        
        # Verificar colisión básica
        if self.physics_engine.get_collision_between_bodies(self.player_body, self.enemy_body):
            # Separar los cuerpos para evitar que se superpongan
            if self.player_body.x < self.enemy_body.x:
                self.player_body.x = self.enemy_body.x - self.player_body.width
            else:
                self.enemy_body.x = self.player_body.x - self.enemy_body.width

    def _player_attack(self):
        """El jugador ataca al enemigo."""
        p = settings.Player_selected_Player
        if self.enemy and self.e_hp > 0 and self.p_hp > 0 and p:
            dmg = max(1, p.damage - self.enemy.resistence // 3)
            self.e_hp = max(0, self.e_hp - dmg)
            
            # Notificar a la IA del enemigo
            if self.enemy_ai:
                self.enemy_ai.take_damage(dmg)
            
            print(f"[FightScene] Player attack: {dmg} damage to enemy")

    def _enemy_attack(self):
        """El enemigo ataca al jugador."""
        p = settings.Player_selected_Player
        if self.enemy and self.e_hp > 0 and self.p_hp > 0 and p:
            dmg = max(1, self.enemy.damage - p.resistence // 3)
            self.p_hp = max(0, self.p_hp - dmg)
            print(f"[FightScene] Enemy attack: {dmg} damage to player")

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

        # suelo
        ground_y = settings.HEIGHT - 100
        pg.draw.rect(screen, (90,90,100), (0, ground_y, settings.WIDTH, 100))
        
        # Dibujar personajes usando sprites o rectángulos como fallback
        player = settings.Player_selected_Player
        if self.player_body and player:
            # Determinar estado de acción del jugador
            player_action = ActionState.IDLE
            if not self.player_body.on_ground:
                player_action = ActionState.JUMPING
            elif abs(self.player_body.velocity_x) > 0.1:
                player_action = ActionState.WALKING
            
            # Renderizar sprite del jugador
            sprite_rendered = sprite_renderer.render_character(
                screen, player,
                self.player_body.x, self.player_body.y,
                self.player_body.facing_right,
                player_action, dt=0.0
            )
            
            # Fallback si no hay sprite
            if not sprite_rendered:
                pg.draw.rect(screen, (90,150,240), self.player_body.get_rect())
        
        if self.enemy_body and self.enemy:
            # Determinar estado de acción del enemigo
            enemy_action = ActionState.IDLE
            if not self.enemy_body.on_ground:
                enemy_action = ActionState.JUMPING
            elif abs(self.enemy_body.velocity_x) > 0.1:
                enemy_action = ActionState.WALKING
            elif self.enemy_ai and self.enemy_ai.state.value == "attacking":
                enemy_action = ActionState.ATTACKING
            
            # Renderizar sprite del enemigo
            sprite_rendered = sprite_renderer.render_character(
                screen, self.enemy,
                self.enemy_body.x, self.enemy_body.y,
                self.enemy_body.facing_right,
                enemy_action, dt=0.0
            )
            
            # Fallback si no hay sprite
            if not sprite_rendered:
                pg.draw.rect(screen, (240,90,90), self.enemy_body.get_rect())

        # Mostrar estado de la IA (debug)
        if self.enemy_ai:
            ai_state = self.enemy_ai.state.value
            self.text(screen, f"AI State: {ai_state}", (40, settings.HEIGHT-80))

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
        
        # Resetear posiciones físicas
        if self.player_body:
            self.player_body.x = 160
            self.player_body.y = settings.HEIGHT-220
            self.player_body.velocity_x = 0
            self.player_body.velocity_y = 0
            self.player_body.on_ground = True
            
        if self.enemy_body:
            self.enemy_body.x = settings.WIDTH-240
            self.enemy_body.y = settings.HEIGHT-220
            self.enemy_body.velocity_x = 0
            self.enemy_body.velocity_y = 0
            self.enemy_body.on_ground = True

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
                # El fondo se generará dinámicamente cuando se necesite
            finally:
                self._prefetching = False

        threading.Thread(target=worker, daemon=True).start()

    def _next_round(self):
        # Usa lo prefetched si está listo; si no, crea al vuelo
        self.enemy = self._prefetch_enemy or self._make_enemy()
        
        # Obtener nuevo fondo usando BackgroundManager
        self.bg = self._get_background()
        
        # Configurar nueva IA del enemigo
        if self.enemy and self.enemy_body:
            self.enemy_ai = create_enemy_ai(self.enemy, self.enemy_body, "NORMAL")
            self.enemy_ai.set_target(self.player_body)
        
        self._prefetch_enemy = None
        self._prefetch_bg = None
        self.reset_round()
        self._start_prefetch()
