import os
import random
import pygame as pg
from pathlib import Path
from typing import List, Dict, Optional
from app.domain.character import Character
from settings.settings import settings

class DebugAssetsManager:
    """
    Gestiona los assets existentes para el modo debug de lucha.
    Carga personajes, sprites y fondos ya generados.
    """
    
    def __init__(self):
        self.portraits_dir = Path(settings.PORTRAIT_DIR)
        self.sprites_dir = Path("app/UI/assets/images/sprites")
        self.backgrounds_dir = Path(settings.BG_FIGHT_DIR)
        self.generated_bg_dir = Path(settings.BG_GEN_DIR)
        
        # Cache de assets cargados
        self.available_characters: List[Character] = []
        self.available_backgrounds: List[str] = []
        self.character_sprites: Dict[str, Dict[str, str]] = {}
        
        # Cargar assets disponibles
        self._load_available_assets()
    
    def _load_available_assets(self):
        """Carga todos los assets disponibles."""
        self._load_available_characters()
        self._load_available_backgrounds()
        self._load_character_sprites()
    
    def _load_available_characters(self):
        """Carga personajes desde los retratos existentes."""
        if not self.portraits_dir.exists():
            print(f"[DebugAssetsManager] Directorio de retratos no encontrado: {self.portraits_dir}")
            return
        
        # Buscar archivos de retratos
        portrait_files = list(self.portraits_dir.glob("*.png"))
        
        for portrait_file in portrait_files:
            try:
                # Extraer nombre del personaje del nombre del archivo
                character_name = portrait_file.stem
                
                # Crear personaje con stats aleatorias
                character = Character(
                    name=character_name,
                    damage=random.randint(5, 15),
                    resistence=random.randint(3, 12),
                    weapon=self._get_random_weapon(),
                    description=f"Personaje debug: {character_name}",
                    portrait=str(portrait_file)
                )
                
                self.available_characters.append(character)
                print(f"[DebugAssetsManager] Cargado personaje: {character_name}")
                
            except Exception as e:
                print(f"[DebugAssetsManager] Error cargando personaje {portrait_file}: {e}")
        
        print(f"[DebugAssetsManager] Total personajes cargados: {len(self.available_characters)}")
    
    def _load_available_backgrounds(self):
        """Carga fondos existentes."""
        # Buscar en directorio de batalla
        if self.backgrounds_dir.exists():
            bg_files = list(self.backgrounds_dir.glob("*.png"))
            self.available_backgrounds.extend([str(f) for f in bg_files])
        
        # Buscar en directorio de fondos generados
        if self.generated_bg_dir.exists():
            gen_bg_files = list(self.generated_bg_dir.glob("*.png"))
            self.available_backgrounds.extend([str(f) for f in gen_bg_files])
        
        # Añadir fondo por defecto si no hay otros
        if not self.available_backgrounds:
            default_bg = Path(settings.BG_SEED_PATH)
            if default_bg.exists():
                self.available_backgrounds.append(str(default_bg))
        
        print(f"[DebugAssetsManager] Total fondos cargados: {len(self.available_backgrounds)}")
    
    def _load_character_sprites(self):
        """Carga sprites existentes para los personajes."""
        if not self.sprites_dir.exists():
            print(f"[DebugAssetsManager] Directorio de sprites no encontrado: {self.sprites_dir}")
            return
        
        # Buscar directorios de personajes
        for character_dir in self.sprites_dir.iterdir():
            if character_dir.is_dir():
                character_name = character_dir.name
                sprite_paths = {}
                
                # Buscar sprites en el directorio del personaje (PNG y TXT)
                for sprite_file in character_dir.glob("*.*"):
                    if sprite_file.suffix.lower() in ['.png', '.txt']:
                        # Mapear nombres de archivo a tipos de sprite
                        sprite_name = sprite_file.stem.lower()
                        sprite_type = self._map_sprite_name_to_type(sprite_name)
                        if sprite_type:
                            # Lógica de priorización compleja
                            existing = sprite_paths.get(sprite_type)
                            if existing is None:
                                sprite_paths[sprite_type] = str(sprite_file)
                            else:
                                should_replace = False
                                
                                # 1. Preferir PNG sobre TXT
                                existing_is_txt = existing.lower().endswith('.txt')
                                current_is_png = sprite_file.suffix.lower() == '.png'
                                if existing_is_txt and current_is_png:
                                    should_replace = True
                                
                                # 2. Para attacks: Attack3 > Attack2 > attack
                                elif sprite_type == "attack":
                                    existing_name = Path(existing).stem.lower()
                                    current_name = sprite_file.stem.lower()
                                    
                                    # Determinar prioridad (mayor = mejor)
                                    def get_attack_priority(name):
                                        if "attack3" in name: return 3
                                        elif "attack2" in name: return 2
                                        elif "attack" in name: return 1
                                        return 0
                                    
                                    if get_attack_priority(current_name) > get_attack_priority(existing_name):
                                        should_replace = True
                                
                                # 3. Para death: Death > Fall
                                elif sprite_type == "death":
                                    existing_name = Path(existing).stem.lower()
                                    current_name = sprite_file.stem.lower()
                                    
                                    if "death" in current_name and "fall" in existing_name:
                                        should_replace = True
                                
                                if should_replace:
                                    sprite_paths[sprite_type] = str(sprite_file)
                
                if sprite_paths:
                    self.character_sprites[character_name] = sprite_paths
                    print(f"[DebugAssetsManager] Cargados {len(sprite_paths)} sprites para {character_name}")
                    print(f"  Sprites: {list(sprite_paths.keys())}")
    
    def _map_sprite_name_to_type(self, sprite_name: str) -> str:
        """Mapea nombres de archivo a tipos de sprite estándar."""
        sprite_name = sprite_name.lower()
        
        # Mapeos específicos para sample_character y archivos PNG reales
        if "idle" in sprite_name:
            return "idle"
        elif "walk" in sprite_name or "run" in sprite_name:
            return "walk"
        elif "attack" in sprite_name:
            # Todos los tipos de attack se mapean a "attack" para compatibilidad
            return "attack"
        elif "block" in sprite_name:
            return "block"
        elif "hurt" in sprite_name or "take hit" in sprite_name:
            return "hurt"
        elif "jump" in sprite_name:
            return "jump"
        elif "death" in sprite_name or "fall" in sprite_name:
            # Todos se mapean a "death" para compatibilidad
            return "death"
        elif "warrior" in sprite_name:
            return "idle"  # Usar como sprite por defecto
        else:
            return None
    
    def _get_random_weapon(self) -> str:
        """Retorna un arma aleatoria."""
        weapons = ["espada", "hacha", "katana", "dagas", "bastón", "guantes", "nunchaku", "lanza"]
        return random.choice(weapons)
    
    def get_random_character(self) -> Optional[Character]:
        """Obtiene un personaje aleatorio de los disponibles."""
        if not self.available_characters:
            return None
        
        character = random.choice(self.available_characters)
        
        # Lógica de sprites basada en configuración
        if settings.generate_character_sprites:
            # Generar sprites únicos para cada personaje (futuro)
            if character.name in self.character_sprites:
                character.sprite_paths = self.character_sprites[character.name]
                print(f"[DebugAssetsManager] Usando sprites únicos para {character.name}")
            else:
                # Fallback a sample_character si no hay sprites únicos
                if "sample_character" in self.character_sprites:
                    character.sprite_paths = self.character_sprites["sample_character"]
                    print(f"[DebugAssetsManager] Fallback a sample_character para {character.name}")
        else:
            # Usar siempre sample_character cuando la generación está desactivada
            if "sample_character" in self.character_sprites:
                character.sprite_paths = self.character_sprites["sample_character"]
                print(f"[DebugAssetsManager] Usando sample_character para {character.name} (generación desactivada)")
        
        return character
    
    def get_random_background(self) -> Optional[str]:
        """Obtiene un fondo aleatorio de los disponibles."""
        if not self.available_backgrounds:
            return None
        
        return random.choice(self.available_backgrounds)
    
    def get_random_background_surface(self, size: tuple[int, int] = (960, 540)) -> Optional[pg.Surface]:
        """Obtiene una superficie de fondo aleatorio cargada."""
        if not self.available_backgrounds:
            return None
        
        bg_path = random.choice(self.available_backgrounds)
        try:
            from app.UI.pg_assets import load_background_cached
            bg_surface = load_background_cached(bg_path, size)
            if bg_surface is None:
                print(f"[DebugAssetsManager] No se pudo cargar fondo: {bg_path}")
                return None
            return bg_surface
        except Exception as e:
            print(f"[DebugAssetsManager] Error cargando fondo {bg_path}: {e}")
            return None
    
    def get_character_by_name(self, name: str) -> Optional[Character]:
        """Obtiene un personaje específico por nombre."""
        for character in self.available_characters:
            if character.name.lower() == name.lower():
                # Lógica de sprites basada en configuración
                if settings.generate_character_sprites:
                    # Generar sprites únicos para cada personaje (futuro)
                    if character.name in self.character_sprites:
                        character.sprite_paths = self.character_sprites[character.name]
                        print(f"[DebugAssetsManager] Usando sprites únicos para {character.name}")
                    else:
                        # Fallback a sample_character si no hay sprites únicos
                        if "sample_character" in self.character_sprites:
                            character.sprite_paths = self.character_sprites["sample_character"]
                            print(f"[DebugAssetsManager] Fallback a sample_character para {character.name}")
                else:
                    # Usar siempre sample_character cuando la generación está desactivada
                    if "sample_character" in self.character_sprites:
                        character.sprite_paths = self.character_sprites["sample_character"]
                        print(f"[DebugAssetsManager] Usando sample_character para {character.name} (generación desactivada)")
                return character
        return None
    
    def get_all_characters(self) -> List[Character]:
        """Obtiene todos los personajes disponibles."""
        # Asignar sprites a todos los personajes basado en configuración
        for character in self.available_characters:
            if settings.generate_character_sprites:
                # Generar sprites únicos para cada personaje (futuro)
                if character.name in self.character_sprites:
                    character.sprite_paths = self.character_sprites[character.name]
                    print(f"[DebugAssetsManager] Usando sprites únicos para {character.name}")
                else:
                    # Fallback a sample_character si no hay sprites únicos
                    if "sample_character" in self.character_sprites:
                        character.sprite_paths = self.character_sprites["sample_character"]
                        print(f"[DebugAssetsManager] Fallback a sample_character para {character.name}")
            else:
                # Usar siempre sample_character cuando la generación está desactivada
                if "sample_character" in self.character_sprites:
                    character.sprite_paths = self.character_sprites["sample_character"]
                    print(f"[DebugAssetsManager] Usando sample_character para {character.name} (generación desactivada)")
        
        return self.available_characters.copy()
    
    def get_all_backgrounds(self) -> List[str]:
        """Obtiene todos los fondos disponibles."""
        return self.available_backgrounds.copy()
    
    def create_debug_enemy(self, player: Character) -> Character:
        """Crea un enemigo de debug basado en el jugador."""
        # Usar un personaje diferente al jugador
        available_enemies = [c for c in self.available_characters if c.name != player.name]
        
        if available_enemies:
            enemy = random.choice(available_enemies)
        else:
            # Crear enemigo genérico si no hay otros
            enemy = Character(
                name="Enemigo_Debug",
                damage=random.randint(5, 15),
                resistence=random.randint(3, 12),
                weapon=self._get_random_weapon(),
                description="Enemigo de debug"
            )
        
        # Lógica de sprites basada en configuración
        if settings.generate_character_sprites:
            # Generar sprites únicos para cada personaje (futuro)
            if enemy.name in self.character_sprites:
                enemy.sprite_paths = self.character_sprites[enemy.name]
                print(f"[DebugAssetsManager] Usando sprites únicos para enemigo {enemy.name}")
            else:
                # Fallback a sample_character si no hay sprites únicos
                if "sample_character" in self.character_sprites:
                    enemy.sprite_paths = self.character_sprites["sample_character"]
                    print(f"[DebugAssetsManager] Fallback a sample_character para enemigo {enemy.name}")
        else:
            # Usar siempre sample_character cuando la generación está desactivada
            if "sample_character" in self.character_sprites:
                enemy.sprite_paths = self.character_sprites["sample_character"]
                print(f"[DebugAssetsManager] Usando sample_character para enemigo {enemy.name} (generación desactivada)")
        
        return enemy
    
    def get_asset_info(self) -> Dict[str, int]:
        """Obtiene información sobre los assets disponibles."""
        return {
            "characters": len(self.available_characters),
            "backgrounds": len(self.available_backgrounds),
            "characters_with_sprites": len(self.character_sprites)
        }

# Instancia global
debug_assets_manager = DebugAssetsManager()
