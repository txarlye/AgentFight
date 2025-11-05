import pygame as pg
import threading
import random
from app.UI.scenes.base_scene import BaseScene
from app.domain.character import Character
from app.Agent.agent_character_creator import create_candidates
from app.Agent.agent_story_weaver import create_story_beat
from settings.settings import settings

class VSScene(BaseScene):
    """
    Escena VS que muestra el enfrentamiento entre el jugador y el enemigo.
    Muestra características de ambos y el motivo del conflicto.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.bg = None
        self.player = None
        self.enemy = None
        self.conflict_reason = ""
        self.generating = True
        self._thread = None
        self.countdown = 3  # Cuenta regresiva antes del combate
        self.countdown_timer = 0
        
        # Estados de la escena
        self.state = "loading"  # loading, showing, countdown, complete
        
    def enter(self):
        """Inicializa la escena y genera el enemigo"""
        self.generating = True
        self.countdown = 3
        self.countdown_timer = 0
        self.state = "loading"
        
        # Obtener el jugador del orchestrator
        if hasattr(self.app, 'orchestrator'):
            self.player = self.app.orchestrator.player_character
        
        def generate_enemy():
            try:
                # Generar enemigo usando el agente de IA
                if settings.use_local_enemy_for_test:
                    # Usar enemigo local para test
                    self.enemy = self._create_local_enemy()
                else:
                    # Generar enemigo con IA
                    enemies = create_candidates(1)
                    self.enemy = enemies[0] if enemies else self._create_local_enemy()
                
                # Generar motivo del conflicto
                self.conflict_reason = self._generate_conflict_reason()
                
                self.generating = False
                self.state = "showing"
                print(f"VSScene: Enemigo generado - {self.enemy.name}")
                
            except Exception as e:
                print(f"VSScene: Error generando enemigo - {e}")
                self.enemy = self._create_local_enemy()
                self.conflict_reason = "Un conflicto épico se desata en el reino."
                self.generating = False
                self.state = "showing"
        
        self._thread = threading.Thread(target=generate_enemy, daemon=True)
        self._thread.start()
    
    def _create_local_enemy(self) -> Character:
        """Crea un enemigo local para testing"""
        names = ["Grom", "Zarath", "Malak", "Vexar", "Kronos"]
        weapons = ["espada maldita", "hacha de guerra", "lanza venenosa", "martillo de trueno", "dagas sombrías"]
        
        return Character(
            name=random.choice(names) + f"_{random.randint(1,99)}",
            damage=random.randint(4, 10),
            resistence=random.randint(3, 9),
            weapon=random.choice(weapons),
            description="Un enemigo formidable que amenaza la paz del reino.",
            portrait="app/UI/assets/test/portraits/maligno-tit-n.png"
        )
    
    def _generate_conflict_reason(self) -> str:
        """Genera un motivo épico para el conflicto"""
        reasons = [
            "Se comió el último trozo de pizza",
            "Mató a mi padre",
            "Robó mi espada legendaria",
            "Destruyó mi aldea",
            "Secuestró a mi mascota",
            "Insultó a mi madre",
            "Pisó mis flores",
            "Rompió mi vaso favorito",
            "Usó mi toalla sin permiso",
            "No devolvió el libro que le presté"
        ]
        
        # Usar Story Weaver si está disponible
        try:
            if hasattr(self.app, 'orchestrator') and self.player and self.enemy:
                context = {
                    "player": self.player.name,
                    "enemy": self.enemy.name,
                    "player_weapon": self.player.weapon,
                    "enemy_weapon": self.enemy.weapon
                }
                return create_story_beat("conflict_motive", self.player, context)
        except Exception:
            pass
        
        return random.choice(reasons)
    
    def handle_event(self, e):
        if e.type == pg.KEYDOWN:
            if e.key in (pg.K_ESCAPE, pg.K_SPACE, pg.K_RETURN):
                if self.state == "showing":
                    # Comenzar cuenta regresiva
                    self.state = "countdown"
                elif self.state == "countdown":
                    # Saltar cuenta regresiva
                    self._start_combat()
                elif self.state == "loading":
                    # Saltar generación
                    self.enemy = self._create_local_enemy()
                    self.conflict_reason = "Un conflicto épico se desata."
                    self.generating = False
                    self.state = "showing"
    
    def update(self, dt):
        if self.state == "countdown":
            self.countdown_timer += dt
            if self.countdown_timer >= 1.0:
                self.countdown_timer = 0
                self.countdown -= 1
                if self.countdown <= 0:
                    self._start_combat()
    
    def _start_combat(self):
        """Inicia el combate"""
        self.state = "complete"
        print("VSScene: Iniciando combate")
        
        # Registrar el enemigo en el orchestrator
        if hasattr(self.app, 'orchestrator'):
            self.app.orchestrator.add_choice(f"vs_{self.enemy.name}", "combat_start")
        
        # Transicionar a la escena de combate
        self.app.set_scene("fight")
    
    def draw(self, screen):
        # Fondo oscuro
        screen.fill((20, 20, 30))
        
        if self.state == "loading":
            self._draw_loading(screen)
        elif self.state == "showing":
            self._draw_vs_screen(screen)
        elif self.state == "countdown":
            self._draw_countdown(screen)
    
    def _draw_loading(self, screen):
        """Dibuja la pantalla de carga"""
        title_font = pg.font.SysFont(settings.FONT_NAME, 32, bold=True)
        title = title_font.render("Generando Enemigo...", True, (240, 240, 240))
        screen.blit(title, (settings.WIDTH//2 - title.get_width()//2, 200))
        
        loading_font = pg.font.SysFont(settings.FONT_NAME, 18)
        dots = "." * (int(pg.time.get_ticks() / 500) % 4)
        loading_text = loading_font.render(f"Preparando batalla{dots}", True, (180, 180, 180))
        screen.blit(loading_text, (settings.WIDTH//2 - loading_text.get_width()//2, 280))
        
        instruction_font = pg.font.SysFont(settings.FONT_NAME, 16)
        instruction = instruction_font.render("Presiona ESPACIO para saltar", True, (120, 120, 120))
        screen.blit(instruction, (settings.WIDTH//2 - instruction.get_width()//2, 350))
    
    def _draw_vs_screen(self, screen):
        """Dibuja la pantalla VS"""
        if not self.player or not self.enemy:
            return
        
        # Título VS
        title_font = pg.font.SysFont(settings.FONT_NAME, 36, bold=True)
        title = title_font.render("VS", True, (255, 0, 0))
        screen.blit(title, (settings.WIDTH//2 - title.get_width()//2, 50))
        
        # Marco del jugador (izquierda)
        player_rect = pg.Rect(50, 120, 400, 300)
        pg.draw.rect(screen, (100, 100, 255), player_rect, 3)
        
        # Marco del enemigo (derecha)
        enemy_rect = pg.Rect(510, 120, 400, 300)
        pg.draw.rect(screen, (255, 100, 100), enemy_rect, 3)
        
        # Información del jugador
        self._draw_character_info(screen, self.player, player_rect, "TU HÉROE", (100, 100, 255))
        
        # Información del enemigo
        self._draw_character_info(screen, self.enemy, enemy_rect, "ENEMIGO", (255, 100, 100))
        
        # Motivo del conflicto
        conflict_font = pg.font.SysFont(settings.FONT_NAME, 18, bold=True)
        conflict_title = conflict_font.render("MOTIVO DEL CONFLICTO:", True, (255, 215, 0))
        screen.blit(conflict_title, (settings.WIDTH//2 - conflict_title.get_width()//2, 450))
        
        conflict_text_font = pg.font.SysFont(settings.FONT_NAME, 16)
        conflict_lines = self._wrap_text(conflict_text_font, self.conflict_reason, settings.WIDTH - 100)
        y = 480
        for line in conflict_lines:
            text_surface = conflict_text_font.render(line, True, (220, 220, 220))
            screen.blit(text_surface, (settings.WIDTH//2 - text_surface.get_width()//2, y))
            y += conflict_text_font.get_linesize()
        
        # Instrucciones
        instruction_font = pg.font.SysFont(settings.FONT_NAME, 16)
        instruction = instruction_font.render("Presiona ESPACIO para comenzar el combate", True, (120, 120, 120))
        screen.blit(instruction, (settings.WIDTH//2 - instruction.get_width()//2, settings.HEIGHT - 50))
    
    def _draw_character_info(self, screen, character: Character, rect: pg.Rect, title: str, color: tuple):
        """Dibuja la información de un personaje"""
        # Título
        title_font = pg.font.SysFont(settings.FONT_NAME, 20, bold=True)
        title_surface = title_font.render(title, True, color)
        screen.blit(title_surface, (rect.x + 10, rect.y + 10))
        
        # Nombre
        name_font = pg.font.SysFont(settings.FONT_NAME, 18, bold=True)
        name_surface = name_font.render(character.name, True, (255, 255, 255))
        screen.blit(name_surface, (rect.x + 10, rect.y + 40))
        
        # Stats
        stats_font = pg.font.SysFont(settings.FONT_NAME, 16)
        y = rect.y + 70
        
        stats = [
            f"Daño: {character.damage}",
            f"Resistencia: {character.resistence}",
            f"Arma: {character.weapon}",
            f"Rareza: {character.get_rarity_description()}"
        ]
        
        for stat in stats:
            stat_surface = stats_font.render(stat, True, (220, 220, 220))
            screen.blit(stat_surface, (rect.x + 10, y))
            y += stats_font.get_linesize() + 5
        
        # Descripción
        desc_font = pg.font.SysFont(settings.FONT_NAME, 14)
        desc_lines = self._wrap_text(desc_font, character.description, rect.width - 20)
        y = rect.y + 200
        for line in desc_lines:
            desc_surface = desc_font.render(line, True, (180, 180, 180))
            screen.blit(desc_surface, (rect.x + 10, y))
            y += desc_font.get_linesize()
    
    def _draw_countdown(self, screen):
        """Dibuja la cuenta regresiva"""
        # Fondo semi-transparente
        overlay = pg.Surface((settings.WIDTH, settings.HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Número de cuenta regresiva
        countdown_font = pg.font.SysFont(settings.FONT_NAME, 72, bold=True)
        countdown_text = countdown_font.render(str(self.countdown), True, (255, 0, 0))
        screen.blit(countdown_text, (settings.WIDTH//2 - countdown_text.get_width()//2, settings.HEIGHT//2 - countdown_text.get_height()//2))
        
        # Texto
        text_font = pg.font.SysFont(settings.FONT_NAME, 24)
        text_surface = text_font.render("¡COMBATE!", True, (255, 255, 255))
        screen.blit(text_surface, (settings.WIDTH//2 - text_surface.get_width()//2, settings.HEIGHT//2 + 50))
    
    def _wrap_text(self, font, text, max_width):
        """Envuelve el texto para que quepa en el ancho especificado"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
