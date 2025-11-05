# app/UI/scenes/debug_fight_scene.py
import threading
import pygame as pg
from settings.settings import settings
from app.UI.pg_assets import draw_background
from .base_scene import BaseScene
from app.domain.physics import PhysicsEngine, PhysicsBody, ActionState
from app.Agent.agent_enemy_ai import create_enemy_ai, EnemyAI
from app.UI.sprite_renderer import sprite_renderer
from app.UI.debug_assets_manager import debug_assets_manager

class DebugFightScene(BaseScene):
    """
    Escena de debug para probar el sistema de lucha usando assets existentes.
    Permite probar físicas, IA y sprites sin generar nuevo contenido.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.bg = None
        self.player = None
        self.enemy = None
        self.p_hp = 100
        self.e_hp = 100

        # Sistema de físicas
        self.physics_engine = PhysicsEngine(settings.WIDTH, settings.HEIGHT)
        self.player_body = None
        self.enemy_body = None
        self.enemy_ai = None

        # Información de debug
        self.debug_info = {}
        self.show_debug_info = True
        
        # Timer para ataques
        self.attack_timer = 0

    def enter(self):
        """Inicializa la escena de debug de lucha."""
        print("[DebugFightScene] Iniciando modo debug de lucha...")
        
        # Obtener información de assets disponibles
        self.debug_info = debug_assets_manager.get_asset_info()
        
        # Seleccionar jugador aleatorio
        self.player = debug_assets_manager.get_random_character()
        if not self.player:
            print("[DebugFightScene] No hay personajes disponibles, creando uno genérico...")
            self.player = self._create_generic_player()
        
        # Crear enemigo
        self.enemy = debug_assets_manager.create_debug_enemy(self.player)
        
        # Seleccionar fondo
        self.bg = debug_assets_manager.get_random_background_surface((settings.WIDTH, settings.HEIGHT))
        
        # Inicializar cuerpos físicos
        self._init_physics_bodies()
        
        # Configurar IA del enemigo
        if self.enemy and self.enemy_body:
            self.enemy_ai = create_enemy_ai(self.enemy, self.enemy_body, "NORMAL")
            self.enemy_ai.set_target(self.player_body)
        
        # Cargar sprites de los personajes
        self._load_character_sprites()
        
        self.reset_round()
        
        print(f"[DebugFightScene] Lucha iniciada: {self.player.name} vs {self.enemy.name}")

    def _create_generic_player(self):
        """Crea un jugador genérico para debug."""
        from app.domain.character import Character
        return Character(
            name="DebugPlayer",
            damage=10,
            resistence=5,
            weapon="espada",
            description="Jugador de debug"
        )

    def _init_physics_bodies(self):
        """Inicializa los cuerpos físicos del jugador y enemigo."""
        # Cuerpo del jugador (lado izquierdo)
        self.player_body = PhysicsBody(
            x=160,
            y=settings.HEIGHT-220,
            width=80,
            height=160,
            facing_right=True
        )
        
        # Actualizar GROUND_Y dinámicamente
        self.player_body.GROUND_Y = settings.HEIGHT - 60  # 60 píxeles desde abajo
        
        # Cuerpo del enemigo (lado derecho)
        self.enemy_body = PhysicsBody(
            x=settings.WIDTH-240,
            y=settings.HEIGHT-220,
            width=80,
            height=160,
            facing_right=False
        )
        
        # Actualizar GROUND_Y dinámicamente
        self.enemy_body.GROUND_Y = settings.HEIGHT - 60  # 60 píxeles desde abajo
        
        # Asegurar que ambos cuerpos estén en el suelo inicialmente
        self.player_body.y = self.player_body.GROUND_Y - self.player_body.height
        self.enemy_body.y = self.enemy_body.GROUND_Y - self.enemy_body.height
        
        # Añadir al motor de físicas
        self.physics_engine.add_body(self.player_body)
        self.physics_engine.add_body(self.enemy_body)

    def _load_character_sprites(self):
        """Carga los sprites de los personajes."""
        if self.player:
            sprite_renderer.load_character_sprites(self.player)
        
        if self.enemy:
            sprite_renderer.load_character_sprites(self.enemy)

    def handle_event(self, e):
        if e.type == pg.KEYDOWN:
            if e.key == pg.K_ESCAPE:
                self.app.set_scene("show_principal_menu")
            elif e.key == pg.K_r:
                self.reset_round()
            elif e.key == pg.K_n:
                self._new_debug_fight()
            elif e.key == pg.K_SPACE:
                self._player_attack(1)
            elif e.key == pg.K_q:
                self._player_attack(2)
            elif e.key == pg.K_e:
                self._player_attack(3)
            elif e.key == pg.K_r:
                self._enemy_attack()
            elif e.key == pg.K_d:
                self.show_debug_info = not self.show_debug_info
            # Controles de movimiento del jugador (WASD)
            elif e.key == pg.K_a or e.key == pg.K_LEFT:
                self.player_body.move_left()
            elif e.key == pg.K_d or e.key == pg.K_RIGHT:
                self.player_body.move_right()
            elif e.key == pg.K_w or e.key == pg.K_UP:
                self.player_body.jump()

    def update(self, dt):
        # Actualizar física
        self.physics_engine.update(dt)
        
        # Actualizar IA del enemigo
        if self.enemy_ai and self.e_hp > 0:
            actions = self.enemy_ai.update(dt, self.physics_engine)
            self._execute_enemy_actions(actions)
        
        # Resetear acción del jugador después de un tiempo
        if hasattr(self, 'attack_timer'):
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.player_action = ActionState.IDLE
                self.attack_timer = 0
        
        # Verificar colisiones
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
        
        if self.physics_engine.get_collision_between_bodies(self.player_body, self.enemy_body):
            # Separar los cuerpos
            if self.player_body.x < self.enemy_body.x:
                self.player_body.x = self.enemy_body.x - self.player_body.width
            else:
                self.enemy_body.x = self.player_body.x - self.enemy_body.width

    def _player_attack(self, attack_type: int = 1):
        """El jugador ataca al enemigo con diferentes tipos de ataque."""
        if self.enemy and self.e_hp > 0 and self.p_hp > 0 and self.player:
            # Diferentes tipos de ataque con diferentes daños
            base_damage = self.player.damage
            if attack_type == 1:
                dmg = max(1, base_damage - self.enemy.resistence // 3)
                self.player_action = ActionState.ATTACKING
                self.attack_timer = 0.5  # 0.5 segundos
                print(f"[DebugFightScene] Player attack1 (SPACE): {dmg} damage to enemy")
            elif attack_type == 2:
                dmg = max(1, int(base_damage * 1.2) - self.enemy.resistence // 3)
                self.player_action = ActionState.ATTACKING2
                self.attack_timer = 0.6  # 0.6 segundos
                print(f"[DebugFightScene] Player attack2 (Q): {dmg} damage to enemy")
            elif attack_type == 3:
                dmg = max(1, int(base_damage * 1.5) - self.enemy.resistence // 3)
                self.player_action = ActionState.ATTACKING3
                self.attack_timer = 0.7  # 0.7 segundos
                print(f"[DebugFightScene] Player attack3 (E): {dmg} damage to enemy")
            else:
                dmg = max(1, base_damage - self.enemy.resistence // 3)
                self.player_action = ActionState.ATTACKING
                self.attack_timer = 0.5  # 0.5 segundos
                print(f"[DebugFightScene] Player attack: {dmg} damage to enemy")
            
            self.e_hp = max(0, self.e_hp - dmg)
            
            if self.enemy_ai:
                self.enemy_ai.take_damage(dmg)

    def _enemy_attack(self):
        """El enemigo ataca al jugador."""
        if self.enemy and self.e_hp > 0 and self.p_hp > 0 and self.player:
            dmg = max(1, self.enemy.damage - self.player.resistence // 3)
            self.p_hp = max(0, self.p_hp - dmg)
            print(f"[DebugFightScene] Enemy attack: {dmg} damage to player")

    def _new_debug_fight(self):
        """Inicia una nueva lucha de debug con personajes diferentes."""
        print("[DebugFightScene] Iniciando nueva lucha de debug...")
        
        # Seleccionar nuevos personajes
        self.player = debug_assets_manager.get_random_character()
        if self.player:
            self.enemy = debug_assets_manager.create_debug_enemy(self.player)
        
        # Nuevo fondo
        self.bg = debug_assets_manager.get_random_background_surface((settings.WIDTH, settings.HEIGHT))
        
        # Limpiar sprites y cargar nuevos
        sprite_renderer.clear_cache()
        self._load_character_sprites()
        
        # Configurar nueva IA
        if self.enemy and self.enemy_body:
            self.enemy_ai = create_enemy_ai(self.enemy, self.enemy_body, "NORMAL")
            self.enemy_ai.set_target(self.player_body)
        
        self.reset_round()
        
        print(f"[DebugFightScene] Nueva lucha: {self.player.name} vs {self.enemy.name}")

    def draw(self, screen):
        # Dibujar fondo
        draw_background(screen, self.bg, (20,40,70))

        # HUD principal
        pname = self.player.name if self.player else "???"
        ename = self.enemy.name if self.enemy else "???"
        self.text(screen, f"Player: {pname}", (40,20))
        self.text(screen, f"Enemy : {ename}", (settings.WIDTH-360,20))
        self._draw_bar(screen, 40, 50, 300, 16, self.p_hp, (80,200,120))
        self._draw_bar(screen, settings.WIDTH-340, 50, 300, 16, self.e_hp, (220,90,90))

        # suelo
        pg.draw.rect(screen, (90,90,100), (0, settings.HEIGHT-40, settings.WIDTH, 40))
        
        # Dibujar personajes usando sprites o rectángulos como fallback
        if self.player_body and self.player:
            # Determinar estado de acción del jugador
            player_action = ActionState.IDLE
            if not self.player_body.on_ground:
                player_action = ActionState.JUMPING
            elif abs(self.player_body.velocity_x) > 0.1:
                player_action = ActionState.WALKING
            
            # Renderizar sprite del jugador
            sprite_rendered = sprite_renderer.render_character(
                screen, self.player,
                self.player_body.x, self.player_body.y,
                self.player_body.facing_right,
                player_action, dt=self.app.clock.get_time()/1000.0
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
                enemy_action, dt=self.app.clock.get_time()/1000.0
            )
            
            # Fallback si no hay sprite
            if not sprite_rendered:
                pg.draw.rect(screen, (240,90,90), self.enemy_body.get_rect())

        # Información de debug
        if self.show_debug_info:
            self._draw_debug_info(screen)

        # Mostrar estado de la IA
        if self.enemy_ai:
            ai_state = self.enemy_ai.state.value
            self.text(screen, f"AI State: {ai_state}", (40, settings.HEIGHT-80))

        # Mensaje de victoria/derrota
        if self.e_hp <= 0 or self.p_hp <= 0:
            msg = "VICTORY!" if self.e_hp <= 0 else "DEFEAT..."
            self.text(screen, msg + "  (R reset, N nueva lucha, ESC menú)",
                      (120, settings.HEIGHT//2 - 12), big=True)

    def _draw_debug_info(self, screen):
        """Dibuja información de debug."""
        y_offset = 100
        line_height = 20
        
        # Título
        self.text(screen, "=== DEBUG INFO ===", (40, y_offset), color=(255, 255, 0))
        y_offset += line_height
        
        # Información de assets
        self.text(screen, f"Personajes disponibles: {self.debug_info.get('characters', 0)}", (40, y_offset))
        y_offset += line_height
        self.text(screen, f"Fondos disponibles: {self.debug_info.get('backgrounds', 0)}", (40, y_offset))
        y_offset += line_height
        self.text(screen, f"Personajes con sprites: {self.debug_info.get('characters_with_sprites', 0)}", (40, y_offset))
        y_offset += line_height * 2
        
        # Información de personajes actuales
        if self.player:
            self.text(screen, f"Player: {self.player.name} (DMG: {self.player.damage}, DEF: {self.player.resistence})", (40, y_offset))
            y_offset += line_height
        
        if self.enemy:
            self.text(screen, f"Enemy: {self.enemy.name} (DMG: {self.enemy.damage}, DEF: {self.enemy.resistence})", (40, y_offset))
            y_offset += line_height * 2
        
        # Controles
        self.text(screen, "Controles: WASD/ARROWS mover, SPACE atacar, R reset, N nueva lucha, D toggle debug", (40, y_offset), color=(200, 200, 200))

    def _draw_bar(self, screen, x, y, w, h, hp, color):
        """Dibuja una barra de vida."""
        pg.draw.rect(screen, (60,60,60), (x, y, w, h))
        pg.draw.rect(screen, color, (x, y, int(w*(hp/100.0)), h))

    def reset_round(self):
        """Resetea la ronda actual."""
        self.p_hp = 100
        self.e_hp = 100
        
        # Resetear posiciones físicas
        if self.player_body:
            self.player_body.x = 160
            self.player_body.y = self.player_body.GROUND_Y - self.player_body.height
            self.player_body.velocity_x = 0
            self.player_body.velocity_y = 0
            self.player_body.on_ground = True
            
        if self.enemy_body:
            self.enemy_body.x = settings.WIDTH-240
            self.enemy_body.y = self.enemy_body.GROUND_Y - self.enemy_body.height
            self.enemy_body.velocity_x = 0
            self.enemy_body.velocity_y = 0
            self.enemy_body.on_ground = True
