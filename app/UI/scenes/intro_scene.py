import pygame as pg
import threading
from app.UI.scenes.base_scene import BaseScene
from app.Agent.agent_story_weaver import create_introduction_story
from app.Agent.agent_background_director import create_story_background_brief
from app.Agent.image_renderer import generate_background_image
from settings.settings import settings

class IntroScene(BaseScene):
    """
    Escena de introducción que muestra la narrativa inicial del juego.
    Usa el Story Weaver para generar contenido dinámico.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.bg = None
        self.story_data = {}
        self.background_brief = {}
        self.background_image_path = None
        self.generating = True
        self._thread = None
        self.current_text_index = 0
        self.text_timer = 0
        self.text_speed = 10.0  # segundos por texto - tiempo suficiente para leer
        
        # Estados de la escena
        self.state = "loading"  # loading, showing, complete
        
    def enter(self):
        """Inicializa la escena y comienza a generar la narrativa"""
        self.generating = True
        self.current_text_index = 0
        self.text_timer = 0
        self.state = "loading"
        
        def generate_story():
            try:
                # Obtener el personaje del jugador
                player = None
                if hasattr(self.app, 'orchestrator') and self.app.orchestrator.player_character:
                    player = self.app.orchestrator.player_character
                    print(f"IntroScene: Generando historia para {player.name}")
                else:
                    print("IntroScene: No hay personaje seleccionado, usando historia genérica")
                
                # Verificar si ya tenemos historia prefetcheada
                if (hasattr(self.app, 'orchestrator') and 
                    self.app.orchestrator.story_context.get("story_generated", False)):
                    
                    print("IntroScene: Usando historia prefetcheada")
                    self.story_data = self.app.orchestrator.story_context.get("prefetched_story", {})
                    self.background_brief = self.app.orchestrator.story_context.get("prefetched_background_brief", {})
                    
                    # Generar imagen de fondo si tenemos el brief
                    if self.background_brief and settings.generate_backgrounds:
                        try:
                            print("IntroScene: Generando imagen de fondo desde brief prefetcheado")
                            self.background_image_path = generate_background_image(self.background_brief)
                            print(f"IntroScene: Imagen de fondo generada: {self.background_image_path}")
                        except Exception as e:
                            print(f"IntroScene: Error generando imagen de fondo - {e}")
                            self.background_image_path = None
                    
                    self.generating = False
                    self.state = "showing"
                    print("IntroScene: Historia prefetcheada cargada exitosamente")
                    return
                
                # Si no hay historia prefetcheada, generarla ahora
                print("IntroScene: Generando historia personalizada")
                self.story_data = create_introduction_story(player)
                
                # Generar brief de fondo si está habilitado
                if settings.generate_backgrounds:
                    try:
                        print("IntroScene: Generando brief de fondo")
                        self.background_brief = create_story_background_brief(self.story_data, player)
                        print("IntroScene: Brief de fondo generado exitosamente")
                        
                        # Generar imagen de fondo usando el brief
                        print("IntroScene: Generando imagen de fondo")
                        self.background_image_path = generate_background_image(self.background_brief)
                        print(f"IntroScene: Imagen de fondo generada: {self.background_image_path}")
                        
                    except Exception as e:
                        print(f"IntroScene: Error generando fondo - {e}")
                        self.background_brief = {}
                        self.background_image_path = None
                
                self.generating = False
                self.state = "showing"
                print("IntroScene: Narrativa generada exitosamente")
                
            except Exception as e:
                print(f"IntroScene: Error generando narrativa - {e}")
                # Fallback con texto estático
                if player:
                    self.story_data = {
                        "title": f"La Aventura de {player.name}",
                        "introduction": f"{player.name}, el guerrero con {player.weapon}, se prepara para enfrentar desafíos épicos.",
                        "conflict": "Las fuerzas del mal amenazan la paz del reino.",
                        "setting": "Un mundo fantástico donde la magia y la espada se encuentran."
                    }
                else:
                    self.story_data = {
                        "title": "La Aventura Comienza",
                        "introduction": "En un mundo lleno de misterios y peligros, un héroe se prepara para enfrentar desafíos épicos.",
                        "conflict": "Las fuerzas del mal amenazan la paz del reino.",
                        "setting": "Un mundo fantástico donde la magia y la espada se encuentran."
                    }
                self.generating = False
                self.state = "showing"
        
        self._thread = threading.Thread(target=generate_story, daemon=True)
        self._thread.start()
    
    def handle_event(self, e):
        if e.type == pg.KEYDOWN:
            if e.key in (pg.K_ESCAPE, pg.K_SPACE, pg.K_RETURN):
                if self.state == "showing":
                    # Avanzar al siguiente texto o completar
                    self.current_text_index += 1
                    if self.current_text_index >= len(self._get_text_sequence()):
                        self._complete_intro()
                elif self.state == "loading":
                    # Saltar la generación y usar texto por defecto
                    self.story_data = {
                        "title": "La Aventura Comienza",
                        "introduction": "En un mundo lleno de misterios y peligros, un héroe se prepara para enfrentar desafíos épicos.",
                        "conflict": "Las fuerzas del mal amenazan la paz del reino.",
                        "setting": "Un mundo fantástico donde la magia y la espada se encuentran."
                    }
                    self.generating = False
                    self.state = "showing"
    
    def update(self, dt):
        if self.state == "showing":
            self.text_timer += dt
            if self.text_timer >= self.text_speed:
                self.text_timer = 0
                self.current_text_index += 1
                if self.current_text_index >= len(self._get_text_sequence()):
                    self._complete_intro()
    
    def _get_text_sequence(self):
        """Obtiene la secuencia de textos a mostrar"""
        if not self.story_data:
            return []
        
        sequence = []
        if "title" in self.story_data:
            sequence.append(("title", self.story_data["title"]))
        if "introduction" in self.story_data:
            sequence.append(("intro", self.story_data["introduction"]))
        if "setting" in self.story_data:
            sequence.append(("setting", self.story_data["setting"]))
        if "conflict" in self.story_data:
            sequence.append(("conflict", self.story_data["conflict"]))
        
        return sequence
    
    def _complete_intro(self):
        """Completa la introducción y transiciona a la siguiente escena"""
        self.state = "complete"
        
        # Si hay personaje seleccionado, ir a VS
        if hasattr(self.app, 'orchestrator') and self.app.orchestrator.player_character:
            print("IntroScene: Transicionando a VS")
            self.app.set_scene("vs")
        else:
            # Si no hay personaje, ir a selección
            if hasattr(self.app, 'orchestrator'):
                self.app.orchestrator.go_to_character_select()
            else:
                self.app.set_scene("char_select")
    
    def draw(self, screen):
        # Fondo con imagen generada o color sólido
        if self.background_image_path and self.state == "showing":
            try:
                # Cargar y mostrar imagen de fondo
                bg_surface = pg.image.load(self.background_image_path)
                bg_surface = pg.transform.scale(bg_surface, (settings.WIDTH, settings.HEIGHT))
                screen.blit(bg_surface, (0, 0))
                
                # Overlay semi-transparente para mejorar legibilidad del texto
                overlay = pg.Surface((settings.WIDTH, settings.HEIGHT))
                overlay.set_alpha(100)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0, 0))
            except Exception as e:
                print(f"IntroScene: Error cargando imagen de fondo - {e}")
                screen.fill((20, 20, 30))
        else:
            screen.fill((20, 20, 30))
        
        if self.state == "loading":
            self._draw_loading(screen)
        elif self.state == "showing":
            self._draw_story(screen)
    
    def _draw_loading(self, screen):
        """Dibuja la pantalla de carga"""
        # Título
        title_font = pg.font.SysFont(settings.FONT_NAME, 32, bold=True)
        title = title_font.render("Generando Historia Personalizada...", True, (240, 240, 240))
        screen.blit(title, (settings.WIDTH//2 - title.get_width()//2, 200))
        
        # Información del personaje si existe
        if hasattr(self.app, 'orchestrator') and self.app.orchestrator.player_character:
            player = self.app.orchestrator.player_character
            player_font = pg.font.SysFont(settings.FONT_NAME, 18)
            player_text = player_font.render(f"Para {player.name} - {player.weapon}", True, (255, 215, 0))
            screen.blit(player_text, (settings.WIDTH//2 - player_text.get_width()//2, 250))
        
        # Indicador de carga
        loading_font = pg.font.SysFont(settings.FONT_NAME, 18)
        dots = "." * (int(pg.time.get_ticks() / 500) % 4)
        loading_text = loading_font.render(f"Creando narrativa{dots}", True, (180, 180, 180))
        screen.blit(loading_text, (settings.WIDTH//2 - loading_text.get_width()//2, 300))
        
        # Instrucciones
        instruction_font = pg.font.SysFont(settings.FONT_NAME, 16)
        instruction = instruction_font.render("Presiona ESPACIO para saltar", True, (120, 120, 120))
        screen.blit(instruction, (settings.WIDTH//2 - instruction.get_width()//2, 350))
    
    def _draw_story(self, screen):
        """Dibuja la narrativa"""
        sequence = self._get_text_sequence()
        if self.current_text_index >= len(sequence):
            return
        
        text_type, text_content = sequence[self.current_text_index]
        
        # Configurar fuente según el tipo de texto
        if text_type == "title":
            font = pg.font.SysFont(settings.FONT_NAME, 28, bold=True)
            color = (255, 215, 0)  # Dorado
            y_offset = 150
        else:
            font = pg.font.SysFont(settings.FONT_NAME, 18)
            color = (220, 220, 220)
            y_offset = 250
        
        # Renderizar texto con wrap
        lines = self._wrap_text(font, text_content, settings.WIDTH - 100)
        
        y = y_offset
        for line in lines:
            text_surface = font.render(line, True, color)
            x = settings.WIDTH//2 - text_surface.get_width()//2
            screen.blit(text_surface, (x, y))
            y += font.get_linesize() + 5
        
        # Indicador de progreso
        progress_font = pg.font.SysFont(settings.FONT_NAME, 14)
        progress_text = f"{self.current_text_index + 1} / {len(sequence)}"
        progress_surface = progress_font.render(progress_text, True, (120, 120, 120))
        screen.blit(progress_surface, (settings.WIDTH - 100, settings.HEIGHT - 50))
        
        # Instrucciones
        instruction_font = pg.font.SysFont(settings.FONT_NAME, 16)
        instruction = instruction_font.render("Presiona ESPACIO para continuar", True, (120, 120, 120))
        screen.blit(instruction, (settings.WIDTH//2 - instruction.get_width()//2, settings.HEIGHT - 80))
        
        # Información adicional
        info_font = pg.font.SysFont(settings.FONT_NAME, 14)
        info_text = info_font.render("La historia se avanza automáticamente cada 10 segundos", True, (100, 100, 100))
        screen.blit(info_text, (settings.WIDTH//2 - info_text.get_width()//2, settings.HEIGHT - 60))
    
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
