from app.UI.scenes.base_scene   import BaseScene
from settings.settings          import settings
from app.UI.pg_assets           import (
                                    load_background_cached, draw_background, 
                                    pick_random_bg, draw_photo_frame
                                )
import pygame as pg

class MenuScene(BaseScene):
    def __init__(self, app):
        super().__init__(app) 
        self.bg = load_background_cached(
            settings.BG_MENU, (settings.WIDTH, settings.HEIGHT)
        )

    def handle_event(self, e):
        if e.type == pg.KEYDOWN:
            if e.key == pg.K_1: 
                self.app.set_scene("show_menu_select_character")
            elif e.key == pg.K_2: 
                if hasattr(self.app, 'orchestrator') and self.app.orchestrator.player_character:
                    # Generar historia personalizada y ir a fight
                    self.app.set_scene("intro")
                else:
                    print("[Menu] -> No hay personaje seleccionado")
            elif e.key == pg.K_3 and settings.debug_fight_mode:
                # Modo debug de lucha
                self.app.set_scene("debug_fight")
            elif e.key == pg.K_4:
                # Pantalla de configuración
                self.app.set_scene("settings")
            elif e.key in (pg.K_0, pg.K_ESCAPE):
                self.app.running = False

    def draw(self, screen):
        draw_background(screen, self.bg, (28,28,35))
        selected = settings.selected_player_name
        y = 80
        self.text(screen, "=== Welcome to Simple Fighter ===", (40,y), big=True); y+=60
        
        # Mostrar información del personaje seleccionado
        if hasattr(self.app, 'orchestrator') and self.app.orchestrator.player_character:
            player = self.app.orchestrator.player_character
            rarity = player.get_rarity_description()
            self.text(screen, f"[1] Select character", (40,y)); y+=30
            self.text(screen, f"Selected: [{player.name}] - {player.weapon} ({rarity})", (40,y), color=(255,215,0)); y+=30
            
            # Verificar si la historia ya está generada
            story_ready = self.app.orchestrator.story_context.get("story_generated", False)
            if story_ready:
                self.text(screen, f"[2] Start Adventure with {player.name}! (Story Ready)", (40,y), color=(100,255,100)); y+=30
            else:
                self.text(screen, f"[2] Start Adventure with {player.name}! (Generating Story...)", (40,y), color=(255,255,100)); y+=30
        else:
            self.text(screen, f"[1] Select character  | No player selected", (40,y)); y+=30
            self.text(screen, "[2] Fight ! (Select character first)", (40,y), color=(255,100,100)); y+=30
        
        self.text(screen, "[0] Salir", (40,y)); y+=30
        
        # Mostrar opción de debug si está habilitada
        if settings.debug_fight_mode:
            self.text(screen, "[3] Debug Fight (Test with existing assets)", (40,y), color=(255,165,0)); y+=30
        
        self.text(screen, "[4] Settings (Configurar IA)", (40,y), color=(100,200,255)); y+=30
        
        self.text(screen, "FIGHT: SPACE atk, E atk enemigo, R reset, N nuevo enemy, ESC menú", (40, 500))
