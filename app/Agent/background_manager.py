import os
import re
import time
from pathlib import Path
from typing import Optional, Dict, List
from app.Agent.agent_background_director import create_combat_background_brief
from app.Agent.image_renderer import generate_background_image
from app.domain.character import Character
from settings.settings import settings

class BackgroundManager:
    """
    Gestiona inteligentemente los fondos de batalla con sistema de cache
    y generación condicional basada en tipo de enemigo y rareza.
    """
    
    def __init__(self):
        self.battle_dir = Path(settings.BG_FIGHT_DIR)
        self.generated_dir = Path(settings.BG_GEN_DIR)
        self.seed_path = Path(settings.BG_SEED_PATH)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Asegura que existan los directorios necesarios."""
        self.battle_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_enemy_type(self, enemy: Character) -> str:
        """Extrae el tipo de enemigo basado en su nombre y características."""
        name_lower = enemy.name.lower()
        
        # Mapeo de tipos basado en palabras clave
        type_mapping = {
            'hielo': ['hielo', 'nieve', 'helado', 'frio', 'glacial'],
            'fuego': ['fuego', 'flama', 'infernal', 'ardiente', 'caliente'],
            'agua': ['agua', 'oceano', 'marino', 'acuatico'],
            'tierra': ['tierra', 'roca', 'piedra', 'golem', 'montaña'],
            'sombra': ['sombra', 'oscuro', 'tenebroso', 'necro'],
            'luz': ['luz', 'sagrado', 'divino', 'angel'],
            'viento': ['viento', 'aire', 'tornado', 'huracan'],
            'electrico': ['electrico', 'rayo', 'trueno', 'voltaje']
        }
        
        for enemy_type, keywords in type_mapping.items():
            if any(keyword in name_lower for keyword in keywords):
                return enemy_type
        
        # Si no coincide, usar el primer elemento del nombre
        return name_lower.split()[0] if name_lower.split() else 'generico'
    
    def _get_enemy_rarity(self, enemy: Character) -> str:
        """Determina la rareza del enemigo basado en sus stats."""
        # Lógica simple basada en stats - se puede mejorar
        total_power = (enemy.attack + enemy.defense + enemy.speed + enemy.health) / 4
        
        if total_power > 80:
            return 'legendario'
        elif total_power > 60:
            return 'epico'
        elif total_power > 40:
            return 'raro'
        else:
            return 'comun'
    
    def _generate_background_filename(self, enemy: Character) -> str:
        """Genera nombre de archivo para el fondo basado en enemigo."""
        enemy_type = self._get_enemy_type(enemy)
        rarity = self._get_enemy_rarity(enemy)
        timestamp = int(time.time())
        return f"{enemy_type}_{rarity}_{timestamp}.png"
    
    def _find_existing_background(self, enemy: Character) -> Optional[Path]:
        """Busca un fondo existente para el tipo y rareza del enemigo."""
        enemy_type = self._get_enemy_type(enemy)
        rarity = self._get_enemy_rarity(enemy)
        
        # Buscar en directorio de batalla
        pattern = f"{enemy_type}_{rarity}_*.png"
        existing_files = list(self.battle_dir.glob(pattern))
        
        if existing_files:
            # Retornar el más reciente
            return max(existing_files, key=lambda x: x.stat().st_mtime)
        
        return None
    
    def get_combat_background(self, player: Character, enemy: Character) -> str:
        """
        Obtiene el fondo de batalla para un combate específico.
        Primero busca en cache, si no existe y está habilitada la generación, crea uno nuevo.
        """
        # Buscar fondo existente
        existing_bg = self._find_existing_background(enemy)
        if existing_bg:
            print(f"[BackgroundManager] Usando fondo existente: {existing_bg}")
            return str(existing_bg)
        
        # Si no existe y la generación está habilitada
        if settings.generate_backgrounds and settings.BACKGROUND_CACHE_ENABLED:
            print(f"[BackgroundManager] Generando nuevo fondo para {enemy.name}")
            
            try:
                # Crear brief específico para el combate
                background_brief = create_combat_background_brief(player, enemy)
                
                # Generar imagen
                generated_path = generate_background_image(background_brief)
                
                if generated_path:
                    # Mover a directorio de batalla con nombre codificado
                    new_filename = self._generate_background_filename(enemy)
                    new_path = self.battle_dir / new_filename
                    
                    # Mover archivo generado
                    Path(generated_path).rename(new_path)
                    print(f"[BackgroundManager] Fondo generado y guardado: {new_path}")
                    return str(new_path)
                    
            except Exception as e:
                print(f"[BackgroundManager] Error generando fondo: {e}")
        
        # Fallback: usar fondo por defecto
        print(f"[BackgroundManager] Usando fondo por defecto")
        return str(self.seed_path)
    
    def get_backgrounds_by_type(self, enemy_type: str) -> List[Path]:
        """Obtiene todos los fondos de un tipo específico."""
        pattern = f"{enemy_type}_*.png"
        return list(self.battle_dir.glob(pattern))
    
    def get_backgrounds_by_rarity(self, rarity: str) -> List[Path]:
        """Obtiene todos los fondos de una rareza específica."""
        pattern = f"*_{rarity}_*.png"
        return list(self.battle_dir.glob(pattern))
    
    def cleanup_old_backgrounds(self, max_age_days: int = 30):
        """Limpia fondos antiguos para ahorrar espacio."""
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        for bg_file in self.battle_dir.glob("*.png"):
            file_age = current_time - bg_file.stat().st_mtime
            if file_age > max_age_seconds:
                bg_file.unlink()
                print(f"[BackgroundManager] Eliminado fondo antiguo: {bg_file}")

# Instancia global
background_manager = BackgroundManager()
