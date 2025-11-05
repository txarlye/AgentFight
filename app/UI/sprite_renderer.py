import pygame as pg
from pathlib import Path
from typing import Dict, Optional, List
from app.domain.physics import ActionState
from app.domain.character import Character

class SpriteRenderer:
    """
    Sistema de renderizado de sprites para personajes.
    Maneja la carga, cache y animación de sprites.
    """
    
    def __init__(self):
        self.sprite_cache: Dict[str, pg.Surface] = {}
        self.animation_frames: Dict[str, List[pg.Surface]] = {}
        self.frame_data: Dict[str, Dict] = {}  # Por personaje: {current_frame, timer}
        self.frame_delay = 90  # ms entre frames (~11 FPS por animación)
        
    def load_character_sprites(self, character: Character) -> bool:
        """
        Carga los sprites de un personaje desde su directorio.
        """
        if not hasattr(character, 'sprite_paths') or not character.sprite_paths:
            print(f"[SpriteRenderer] No sprite paths for {character.name}")
            return False
        
        try:
            loaded_count = 0
            for sprite_type, sprite_path in character.sprite_paths.items():
                sprite_file = Path(sprite_path)
                if sprite_file.exists():
                    if sprite_file.suffix.lower() == '.txt':
                        # Crear sprite de placeholder para archivos .txt
                        sprite_surface = self._create_placeholder_sprite(sprite_type)
                    else:
                        # Cargar sprite PNG real
                        sprite_surface = pg.image.load(sprite_path).convert_alpha()
                        # Si es un spritesheet horizontal, extraer frames
                        frames = self._try_extract_frames(sprite_surface, sprite_type, sprite_path)
                        if frames:
                            self.animation_frames[f"{character.name}_{sprite_type}"] = frames
                            # Usar el primer frame como base para cache simple
                            sprite_surface = frames[0]
                        else:
                            # No escalar aquí, se hará en render_character con el multiplicador
                            pass
                    
                    # Guardar sprite con la clave del personaje
                    self.sprite_cache[f"{character.name}_{sprite_type}"] = sprite_surface
                    print(f"[SpriteRenderer] Loaded sprite: {character.name}_{sprite_type} from {sprite_path}")
                    loaded_count += 1
                else:
                    print(f"[SpriteRenderer] Sprite not found: {sprite_path}")
            
            print(f"[SpriteRenderer] Total sprites loaded for {character.name}: {loaded_count}")
            return loaded_count > 0
            
        except Exception as e:
            print(f"[SpriteRenderer] Error loading sprites for {character.name}: {e}")
            return False
    
    def get_sprite(self, character_name: str, sprite_type: str) -> Optional[pg.Surface]:
        """
        Obtiene un sprite específico del cache.
        """
        key = f"{character_name}_{sprite_type}"
        return self.sprite_cache.get(key)
    
    def get_animated_sprite(self, character_name: str, action_state: ActionState, dt: float) -> Optional[pg.Surface]:
        """
        Obtiene un sprite animado basado en el estado de acción.
        """
        # Mapear estados de acción a tipos de sprite
        sprite_type = self._action_to_sprite_type(action_state)
        
        # Obtener sprite base
        sprite = self.get_sprite(character_name, sprite_type)
        if not sprite:
            return None
        
        # Animación si existen frames
        key = f"{character_name}_{sprite_type}"
        frames = self.animation_frames.get(key)
        if not frames or len(frames) <= 1:
            return sprite
        
        # Frame tracking por personaje
        char_key = f"{character_name}_{sprite_type}"
        if char_key not in self.frame_data:
            self.frame_data[char_key] = {"current_frame": 0, "timer": 0.0}
        
        frame_info = self.frame_data[char_key]
        frame_info["timer"] += dt * 1000.0
        
        if frame_info["timer"] >= self.frame_delay:
            frame_info["timer"] = 0.0
            frame_info["current_frame"] = (frame_info["current_frame"] + 1) % len(frames)
        
        return frames[frame_info["current_frame"]]
    
    def _action_to_sprite_type(self, action_state: ActionState) -> str:
        """
        Mapea estados de acción a tipos de sprite.
        """
        mapping = {
            ActionState.IDLE: "idle",
            ActionState.WALKING: "walk",
            ActionState.RUNNING: "walk",  # Usar walk para running por ahora
            ActionState.JUMPING: "jump",
            ActionState.ATTACKING: "attack",
            ActionState.ATTACKING2: "attack2",
            ActionState.ATTACKING3: "attack3",
            ActionState.BLOCKING: "block",
            ActionState.HURT: "hurt",
            ActionState.DEAD: "hurt"  # Usar hurt para dead por ahora
        }
        return mapping.get(action_state, "idle")
    
    def render_character(self, screen: pg.Surface, character: Character, 
                        x: float, y: float, facing_right: bool = True, 
                        action_state: ActionState = ActionState.IDLE, dt: float = 0.0) -> bool:
        """
        Renderiza un personaje en la pantalla.
        """
        # Obtener sprite apropiado
        sprite = self.get_animated_sprite(character.name, action_state, dt)
        if not sprite:
            # Fallback: dibujar rectángulo
            rect = pg.Rect(x, y, 80, 160)
            color = (90, 150, 240) if character == character else (240, 90, 90)
            pg.draw.rect(screen, color, rect)
            return False
        
        # Voltear sprite si es necesario
        if not facing_right:
            sprite = pg.transform.flip(sprite, True, False)
        
        # Escalar sprite al tamaño apropiado usando configuración
        from settings.settings import settings
        size_multiplier = getattr(settings, 'CHARACTER_SIZE_MULTIPLIER', 2.0)
        # Aplicar multiplicador directamente sin división
        target_width = int(162 * size_multiplier)
        target_height = int(162 * size_multiplier)
        scaled_sprite = pg.transform.scale(sprite, (target_width, target_height))
        
        # Dibujar en pantalla
        screen.blit(scaled_sprite, (x, y))
        return True

    def _try_extract_frames(self, sheet: pg.Surface, sprite_type: str, sprite_path: str = "") -> Optional[List[pg.Surface]]:
        """Intenta extraer frames de un spritesheet horizontal según reglas por tipo.
        El alto esperado del frame es 162 px (tu set), y el número de frames depende del tipo.
        Devuelve lista de frames o None si no aplica.
        """
        # Determinar número de frames basado en el archivo real, no el tipo
        def get_frames_from_filename(file_path: str) -> int:
            filename = Path(file_path).stem.lower()
            if "attack3" in filename: return 8
            elif "attack2" in filename: return 7
            elif "attack" in filename: return 7
            elif "death" in filename: return 7
            elif "fall" in filename: return 3
            elif "jump" in filename: return 3
            elif "idle" in filename: return 10
            elif "run" in filename or "walk" in filename: return 8
            elif "hurt" in filename or "take hit" in filename: return 3
            else: return 6  # Default
        
        # Usar la ruta del archivo si está disponible
        if sprite_path:
            num_frames = get_frames_from_filename(sprite_path)
        else:
            # Fallback a mapeo por tipo
            type_to_frames = {
                "attack": 7, "death": 7, "jump": 3, "idle": 10,
                "walk": 8, "run": 8, "hurt": 3, "block": 3,
            }
            num_frames = type_to_frames.get(sprite_type, 6)
        if not num_frames:
            return None
        sheet_w, sheet_h = sheet.get_width(), sheet.get_height()
        # Esperamos altura 162
        if sheet_h < 100:
            return None
        frame_w = sheet_w // num_frames
        if frame_w <= 0:
            return None
        frames: List[pg.Surface] = []
        for i in range(num_frames):
            rect = pg.Rect(i * frame_w, 0, frame_w, sheet_h)
            frame = sheet.subsurface(rect).copy()
            frames.append(frame)
        return frames
    
    def _create_placeholder_sprite(self, sprite_type: str) -> pg.Surface:
        """Crea un sprite placeholder basado en el tipo."""
        # Crear superficie de 80x160
        sprite_surface = pg.Surface((80, 160), pg.SRCALPHA)
        
        # Colores por tipo de sprite
        colors = {
            "idle": (100, 200, 100),      # Verde
            "walk": (200, 200, 100),      # Amarillo
            "attack": (200, 100, 100),    # Rojo
            "block": (100, 100, 200),     # Azul
            "hurt": (200, 100, 200),      # Rosa
            "jump": (100, 200, 200),      # Cian
            "death": (150, 150, 150)      # Gris
        }
        
        color = colors.get(sprite_type, (150, 150, 150))
        
        # Dibujar rectángulo principal
        pg.draw.rect(sprite_surface, color, (10, 10, 60, 140))
        
        # Dibujar texto del tipo
        font = pg.font.Font(None, 16)
        text = font.render(sprite_type.upper(), True, (255, 255, 255))
        text_rect = text.get_rect(center=(40, 80))
        sprite_surface.blit(text, text_rect)
        
        return sprite_surface
    
    def clear_cache(self):
        """
        Limpia el cache de sprites.
        """
        self.sprite_cache.clear()
        self.animation_frames.clear()
        self.frame_data.clear()

# Instancia global
sprite_renderer = SpriteRenderer()
