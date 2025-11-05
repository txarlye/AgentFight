#!/usr/bin/env python3
"""
Script de prueba para verificar la integración de todos los sistemas.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def test_settings():
    """Prueba la carga de configuraciones."""
    print("🔧 Probando configuraciones...")
    try:
        from settings.settings import settings
        print(f"✅ Configuraciones cargadas:")
        print(f"   - Tamaño de sprite: {settings.CHARACTER_SPRITE_SIZE}")
        print(f"   - Tamaño de fondo: {settings.BACKGROUND_SIZE}")
        print(f"   - Generar fondos: {settings.generate_backgrounds}")
        print(f"   - Generar sprites: {settings.generate_character_sprites}")
        return True
    except Exception as e:
        print(f"❌ Error cargando configuraciones: {e}")
        return False

def test_physics():
    """Prueba el sistema de físicas."""
    print("\n⚡ Probando sistema de físicas...")
    try:
        from app.domain.physics import PhysicsEngine, PhysicsBody, ActionState
        
        # Crear motor de físicas
        engine = PhysicsEngine(800, 600)
        
        # Crear cuerpos
        body1 = PhysicsBody(x=100, y=400, facing_right=True)
        body2 = PhysicsBody(x=300, y=400, facing_right=False)
        
        # Añadir al motor
        engine.add_body(body1)
        engine.add_body(body2)
        
        # Probar movimiento
        body1.move_right()
        body2.move_left()
        
        # Actualizar física
        engine.update(1.0)
        
        print(f"✅ Sistema de físicas funcionando:")
        print(f"   - Body1 posición: ({body1.x:.1f}, {body1.y:.1f})")
        print(f"   - Body2 posición: ({body2.x:.1f}, {body2.y:.1f})")
        print(f"   - Distancia entre cuerpos: {engine.get_distance_between_bodies(body1, body2):.1f}")
        return True
    except Exception as e:
        print(f"❌ Error en sistema de físicas: {e}")
        return False

def test_background_manager():
    """Prueba el BackgroundManager."""
    print("\n🎨 Probando BackgroundManager...")
    try:
        from app.Agent.background_manager import background_manager
        from app.domain.character import Character
        
        # Crear personajes de prueba
        player = Character(name="TestPlayer", damage=10, resistence=5, weapon="espada")
        enemy = Character(name="TestEnemy", damage=8, resistence=3, weapon="hacha")
        
        # Probar obtención de fondo
        bg_path = background_manager.get_combat_background(player, enemy)
        print(f"✅ BackgroundManager funcionando:")
        print(f"   - Ruta de fondo: {bg_path}")
        print(f"   - Tipo de enemigo detectado: {background_manager._get_enemy_type(enemy)}")
        print(f"   - Rareza del enemigo: {background_manager._get_enemy_rarity(enemy)}")
        return True
    except Exception as e:
        print(f"❌ Error en BackgroundManager: {e}")
        return False

def test_enemy_ai():
    """Prueba la IA de enemigos."""
    print("\n🤖 Probando IA de enemigos...")
    try:
        from app.Agent.agent_enemy_ai import create_enemy_ai
        from app.domain.physics import PhysicsBody
        from app.domain.character import Character
        
        # Crear enemigo y cuerpo físico
        enemy = Character(name="TestEnemy", damage=10, resistence=5, weapon="espada")
        enemy_body = PhysicsBody(x=300, y=400)
        
        # Crear IA
        ai = create_enemy_ai(enemy, enemy_body, "NORMAL")
        
        # Probar actualización
        actions = ai.update(1.0, None)
        
        print(f"✅ IA de enemigos funcionando:")
        print(f"   - Estado actual: {ai.state.value}")
        print(f"   - Agresividad: {ai.aggressiveness:.2f}")
        print(f"   - Acciones: {actions}")
        return True
    except Exception as e:
        print(f"❌ Error en IA de enemigos: {e}")
        return False

def test_sprite_generator():
    """Prueba el generador de sprites."""
    print("\n🎭 Probando generador de sprites...")
    try:
        from app.Agent.agent_sprite_generator import create_sprite_specification
        from app.domain.character import Character
        
        # Crear personaje de prueba
        character = Character(name="TestCharacter", damage=10, resistence=5, weapon="espada")
        
        # Probar creación de especificación
        spec = create_sprite_specification(character, "idle")
        
        print(f"✅ Generador de sprites funcionando:")
        print(f"   - Especificación creada para: {spec.get('character_name')}")
        print(f"   - Tipo de sprite: {spec.get('sprite_type')}")
        print(f"   - Paleta de colores: {spec.get('color_palette')}")
        return True
    except Exception as e:
        print(f"❌ Error en generador de sprites: {e}")
        return False

def test_sprite_renderer():
    """Prueba el renderizador de sprites."""
    print("\n🎨 Probando renderizador de sprites...")
    try:
        from app.UI.sprite_renderer import sprite_renderer
        from app.domain.physics import ActionState
        from app.domain.character import Character
        
        # Crear personaje de prueba
        character = Character(name="TestCharacter", damage=10, resistence=5, weapon="espada")
        
        # Probar carga de sprites (sin sprites reales)
        success = sprite_renderer.load_character_sprites(character)
        
        print(f"✅ Renderizador de sprites funcionando:")
        print(f"   - Carga de sprites: {'Exitoso' if success else 'Sin sprites disponibles'}")
        print(f"   - Cache de sprites: {len(sprite_renderer.sprite_cache)} sprites")
        return True
    except Exception as e:
        print(f"❌ Error en renderizador de sprites: {e}")
        return False

def main():
    """Ejecuta todas las pruebas."""
    print("🚀 Iniciando pruebas de integración...\n")
    
    tests = [
        test_settings,
        test_physics,
        test_background_manager,
        test_enemy_ai,
        test_sprite_generator,
        test_sprite_renderer
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Error ejecutando {test.__name__}: {e}")
    
    print(f"\n📊 Resultados: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
