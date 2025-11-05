#!/usr/bin/env python3
"""
Test rápido para verificar ataques múltiples
"""

import pygame as pg
from app.domain.physics import ActionState
from app.UI.sprite_renderer import sprite_renderer
from app.UI.debug_assets_manager import debug_assets_manager
from app.domain.character import Character

def test_attacks():
    """Test de ataques múltiples"""
    print("🚀 Probando sistema de ataques múltiples...")
    
    # Inicializar Pygame
    pg.init()
    pg.display.set_mode((100, 100))
    
    # Crear personaje de prueba
    test_char = Character(
        name="TestChar",
        damage=15,
        resistence=8,
        weapon="espada",
        description="Personaje de prueba",
        portrait="test_portrait.png"
    )
    
    # Cargar sprites
    sprite_renderer.load_character_sprites(test_char)
    
    # Test de mapeo de estados
    print("\n✅ Estados de ataque disponibles:")
    print(f"  - ATTACKING: {ActionState.ATTACKING}")
    print(f"  - ATTACKING2: {ActionState.ATTACKING2}")
    print(f"  - ATTACKING3: {ActionState.ATTACKING3}")
    
    # Test de sprites por tipo de ataque
    print("\n🎯 Test de sprites por tipo de ataque:")
    
    for attack_state in [ActionState.ATTACKING, ActionState.ATTACKING2, ActionState.ATTACKING3]:
        sprite = sprite_renderer.get_animated_sprite(test_char.name, attack_state, 0.0)
        if sprite:
            print(f"  ✅ {attack_state.value}: {sprite.get_size()}")
        else:
            print(f"  ❌ {attack_state.value}: No encontrado")
    
    # Test de priorización de sprites
    print("\n🔍 Test de priorización de sprites:")
    if "attack" in test_char.sprite_paths:
        print(f"  - Sprite attack usado: {test_char.sprite_paths['attack']}")
    
    print("\n🎉 Test de ataques completado!")
    pg.quit()

if __name__ == "__main__":
    test_attacks()
