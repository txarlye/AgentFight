#!/usr/bin/env python3
"""
Script de prueba para verificar la lógica de sprites con diferentes configuraciones.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def test_sprite_logic():
    """Prueba la lógica de sprites con diferentes configuraciones."""
    print("🎮 Probando lógica de sprites...")
    
    try:
        import pygame as pg
        
        # Inicializar Pygame
        pg.init()
        temp_screen = pg.display.set_mode((100, 100))
        pg.display.set_caption("Test Temporal")
        
        from app.UI.debug_assets_manager import debug_assets_manager
        from settings.settings import settings
        
        print(f"✅ Configuración actual: generate_character_sprites = {settings.generate_character_sprites}")
        
        # Verificar que sample_character está disponible
        if "sample_character" not in debug_assets_manager.character_sprites:
            print("❌ sample_character no está disponible")
            return False
        
        print(f"✅ sample_character disponible con {len(debug_assets_manager.character_sprites['sample_character'])} sprites")
        
        # Probar obtención de personajes
        print("\n🔍 Probando obtención de personajes...")
        
        # Obtener varios personajes para verificar que todos usan sample_character
        characters = []
        for i in range(3):
            character = debug_assets_manager.get_random_character()
            if character:
                characters.append(character)
                print(f"   - {character.name}: {len(character.sprite_paths)} sprites asignados")
        
        if len(characters) < 3:
            print("❌ No se pudieron obtener suficientes personajes")
            return False
        
        # Verificar que todos los personajes tienen los mismos sprites (sample_character)
        first_sprites = set(characters[0].sprite_paths.keys())
        all_same = all(set(char.sprite_paths.keys()) == first_sprites for char in characters)
        
        if all_same:
            print(f"✅ Todos los personajes usan los mismos sprites: {list(first_sprites)}")
        else:
            print("❌ Los personajes no tienen los mismos sprites")
            return False
        
        # Verificar que los sprites apuntan a sample_character
        sample_character_paths = debug_assets_manager.character_sprites["sample_character"]
        all_use_sample = all(char.sprite_paths == sample_character_paths for char in characters)
        
        if all_use_sample:
            print("✅ Todos los personajes usan sprites de sample_character")
        else:
            print("❌ No todos los personajes usan sprites de sample_character")
            return False
        
        # Probar que se pueden cargar los sprites
        print("\n🎨 Probando carga de sprites...")
        from app.UI.sprite_renderer import sprite_renderer
        
        success_count = 0
        for character in characters:
            success = sprite_renderer.load_character_sprites(character)
            if success:
                success_count += 1
                print(f"   ✅ {character.name}: sprites cargados correctamente")
            else:
                print(f"   ❌ {character.name}: error cargando sprites")
        
        if success_count == len(characters):
            print(f"✅ Todos los personajes ({success_count}) cargaron sprites correctamente")
        else:
            print(f"❌ Solo {success_count}/{len(characters)} personajes cargaron sprites")
            return False
        
        # Limpiar
        pg.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando prueba de lógica de sprites...\n")
    
    success = test_sprite_logic()
    
    if success:
        print("\n🎉 ¡Prueba exitosa! La lógica de sprites funciona correctamente.")
        print("   - Con generate_character_sprites = false, todos usan sample_character")
        print("   - Los sprites se cargan y asignan correctamente")
    else:
        print("\n💥 Prueba fallida. Hay un problema con la lógica de sprites.")
