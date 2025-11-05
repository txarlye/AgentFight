"""
Escena de configuración para ajustar opciones de generación con IA.
Permite configurar:
- Generación de personajes con IA (sí/no)
- Proveedor de IA para personajes (Ollama/OpenAI)
- Generación de imágenes con IA (sí/no)
- Proveedor de IA para imágenes (Stable Diffusion/OpenAI DALL-E)
"""
from app.UI.scenes.base_scene import BaseScene
from settings.settings import settings
from settings.load_settings import load_config
from app.UI.pg_assets import (
    load_background_cached, draw_background
)
import pygame as pg
import json
import os


class SettingsScene(BaseScene):
    """Escena de configuración de opciones de IA"""
    
    def __init__(self, app):
        super().__init__(app)
        self.bg = load_background_cached(
            settings.BG_MENU, (settings.WIDTH, settings.HEIGHT)
        )
        self.cursor = 0  # Índice de la opción seleccionada
        self.settings_path = "settings/settings.json"
        
        # Opciones configurables
        self.options = [
            {
                "name": "Generar personajes con IA",
                "key": "generate_characters_with_ai",
                "type": "bool",
                "section": "Debug",
                "json_key": "use_local_characters_for_test",
                "invert": True  # Si use_local_characters_for_test=False, entonces genera con IA
            },
            {
                "name": "IA para personajes",
                "key": "character_ai_provider",
                "type": "choice",
                "choices": ["ollama", "openai"],
                "section": "AIProvider",
                "json_key": "provider"
            },
            {
                "name": "Generar imágenes con IA",
                "key": "generate_images_with_ai",
                "type": "bool",
                "section": "Debug",
                "json_key": "use_existing_assets",
                "invert": True  # Si use_existing_assets=False, entonces genera con IA
            },
            {
                "name": "IA para imágenes",
                "key": "image_ai_provider",
                "type": "choice",
                "choices": ["stable_diffusion", "openai"],
                "section": "ImageGeneration",
                "json_key": "provider"
            }
        ]
        
        # Cargar valores actuales
        self.load_current_values()
    
    def load_current_values(self):
        """Carga los valores actuales desde settings"""
        for option in self.options:
            if option["section"] == "Debug":
                if option["json_key"] == "use_existing_assets":
                    current = getattr(settings, "use_existing_assets", False)
                    option["value"] = not current if option.get("invert") else current
                elif option["json_key"] == "use_local_characters_for_test":
                    current = getattr(settings, "use_local_characters_for_test", True)
                    option["value"] = not current if option.get("invert") else current
            elif option["section"] == "AIProvider":
                current = getattr(settings, "AI_PROVIDER", "ollama")
                option["value"] = current
            elif option["section"] == "ImageGeneration":
                current = getattr(settings, "IMAGE_PROVIDER", "stable_diffusion")
                option["value"] = current
    
    def handle_event(self, e):
        if e.type == pg.KEYDOWN:
            if e.key in (pg.K_0, pg.K_ESCAPE):
                # Guardar y volver al menú
                self.save_settings()
                self.app.set_scene("show_principal_menu")
            elif e.key in (pg.K_UP, pg.K_w):
                self.cursor = max(0, self.cursor - 1)
            elif e.key in (pg.K_DOWN, pg.K_s):
                self.cursor = min(len(self.options) - 1, self.cursor + 1)
            elif e.key in (pg.K_LEFT, pg.K_a, pg.K_RIGHT, pg.K_d, pg.K_RETURN, pg.K_SPACE):
                # Cambiar valor de la opción actual
                self._toggle_option(self.cursor)
    
    def _toggle_option(self, index):
        """Cambia el valor de la opción seleccionada"""
        if index < 0 or index >= len(self.options):
            return
        
        option = self.options[index]
        
        if option["type"] == "bool":
            # Alternar valor booleano
            option["value"] = not option["value"]
        elif option["type"] == "choice":
            # Cambiar a la siguiente opción en la lista
            current_idx = option["choices"].index(option["value"])
            next_idx = (current_idx + 1) % len(option["choices"])
            option["value"] = option["choices"][next_idx]
        
        print(f"[Settings] Cambiado: {option['name']} = {option['value']}")
    
    def save_settings(self):
        """Guarda los cambios en settings.json"""
        try:
            # Cargar el JSON completo
            with open(self.settings_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Aplicar cambios
            for option in self.options:
                section = option["section"]
                json_key = option["json_key"]
                value = option["value"]
                
                # Si tiene invert, ajustar el valor
                if option.get("invert") and option["type"] == "bool":
                    value = not value
                
                if section not in config:
                    config[section] = {}
                
                config[section][json_key] = value
            
            # Guardar el JSON
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            print(f"[Settings] ✅ Configuración guardada en {self.settings_path}")
            
            # Recargar settings en el objeto global
            settings.load_configuration(self.settings_path)
            
        except Exception as e:
            print(f"[Settings] ❌ Error guardando configuración: {e}")
            import traceback
            traceback.print_exc()
    
    def draw(self, screen):
        draw_background(screen, self.bg, (28, 28, 35))
        
        y = 60
        self.text(screen, "=== Configuración de IA ===", (40, y), big=True, color=(255, 255, 100)); y += 50
        
        # Mostrar opciones
        for i, option in enumerate(self.options):
            # Color según si está seleccionada
            if i == self.cursor:
                color = (255, 255, 0)  # Amarillo para seleccionada
                prefix = "▶ "
            else:
                color = (240, 240, 240)  # Blanco para no seleccionada
                prefix = "  "
            
            # Nombre de la opción
            name = option["name"]
            self.text(screen, f"{prefix}{name}:", (40, y), color=color)
            
            # Valor actual
            value = option["value"]
            if option["type"] == "bool":
                value_str = "SÍ" if value else "NO"
                value_color = (100, 255, 100) if value else (255, 100, 100)
            else:
                value_str = value.upper()
                value_color = (200, 200, 255)
            
            self.text(screen, f"  {value_str}", (250, y), color=value_color)
            y += 35
        
        # Instrucciones
        y += 30
        self.text(screen, "Controles:", (40, y), color=(200, 200, 200)); y += 25
        self.text(screen, "  ↑/↓ o W/S: Navegar", (50, y), color=(180, 180, 180)); y += 20
        self.text(screen, "  ←/→ o A/D o ENTER: Cambiar valor", (50, y), color=(180, 180, 180)); y += 20
        self.text(screen, "  ESC o 0: Guardar y volver al menú", (50, y), color=(180, 180, 180)); y += 30
        
        # Información adicional
        y += 10
        self.text(screen, "Notas:", (40, y), color=(255, 200, 100), big=True); y += 20
        self.text(screen, "• Personajes: Si NO, usa personajes de test", (40, y), color=(255, 200, 100)); y += 18
        self.text(screen, "• Imágenes: Si NO, usa imágenes de test", (40, y), color=(255, 200, 100)); y += 18
        self.text(screen, "• Los cambios se guardan al salir (ESC)", (40, y), color=(200, 255, 200))

