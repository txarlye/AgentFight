#!/usr/bin/env python3
"""
Script de prueba para verificar que los sprites de sample_character se cargan correctamente.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def test_sample_character_sprites():
    """Prueba que los sprites de sample_character se cargan correctamente."""
    print("🎮 Probando carga de sprites de sample_character...")
    
    try:
        from app.UI.debug_assets_manager import debug_assets_manager
        from app.UI.sprite_renderer import sprite_renderer
        
        # Verificar que sample_character está disponible
        if "sample_character" not in debug_assets_manager.character_sprites:
            print("❌ sample_character no está en character_sprites")
            return False
        
        print(f"✅ sample_character encontrado con {len(debug_assets_manager.character_sprites['sample_character'])} sprites")
        print(f"   Sprites disponibles: {list(debug_assets_manager.character_sprites['sample_character'].keys())}")
        
        # Obtener un personaje aleatorio
        character = debug_assets_manager.get_random_character()
        if not character:
            print("❌ No se pudo obtener personaje aleatorio")
            return False
        
        print(f"✅ Personaje obtenido: {character.name}")
        
        # Verificar que tiene sprite_paths asignados
        if not hasattr(character, 'sprite_paths') or not character.sprite_paths:
            print("❌ El personaje no tiene sprite_paths asignados")
            return False
        
        print(f"✅ sprite_paths asignados: {len(character.sprite_paths)} sprites")
        
        # Verificar que los sprites apuntan a sample_character
        sample_character_paths = debug_assets_manager.character_sprites["sample_character"]
        if character.sprite_paths != sample_character_paths:
            print("❌ Los sprite_paths no coinciden con sample_character")
            print(f"   Esperado: {list(sample_character_paths.keys())}")
            print(f"   Obtenido: {list(character.sprite_paths.keys())}")
            return False
        
        print("✅ Los sprite_paths coinciden con sample_character")
        
        # Cargar los sprites en el SpriteRenderer
        success = sprite_renderer.load_character_sprites(character)
        if not success:
            print("❌ No se pudieron cargar los sprites")
            return False
        
        print("✅ Sprites cargados en SpriteRenderer")
        
        # Verificar que se pueden obtener los sprites
        for sprite_type in ['idle', 'walk', 'attack', 'jump']:
            sprite = sprite_renderer.get_sprite(character.name, sprite_type)
            if sprite:
                print(f"✅ Sprite {sprite_type} obtenido: {sprite.get_size()}")
            else:
                print(f"❌ No se pudo obtener sprite {sprite_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando prueba de sprites de sample_character...\n")
    
    success = test_sample_character_sprites()
    
    if success:
        print("\n🎉 ¡Prueba exitosa! Los sprites de sample_character se están cargando correctamente.")
    else:
        print("\n💥 Prueba fallida. Hay un problema con la carga de sprites.")
