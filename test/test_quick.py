#!/usr/bin/env python3
"""
Script de prueba rápida para verificar que el sistema funciona.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def test_character_attributes():
    """Prueba que los atributos de Character funcionen correctamente."""
    print("🔧 Probando atributos de Character...")
    
    try:
        from app.domain.character import Character
        
        # Crear un personaje de prueba
        char = Character(
            name="TestChar",
            damage=10,
            resistence=5,
            weapon="espada",
            description="Personaje de prueba",
            portrait="test.png"
        )
        
        print(f"✅ Character creado: {char.name}")
        print(f"   - Damage: {char.damage}")
        print(f"   - Resistence: {char.resistence}")
        print(f"   - Health: {char.health}")
        print(f"   - Weapon: {char.weapon}")
        
        return True
    except Exception as e:
        print(f"❌ Error en Character: {e}")
        return False

def test_enemy_ai():
    """Prueba que la IA del enemigo funcione con los atributos correctos."""
    print("\n🤖 Probando IA del enemigo...")
    
    try:
        from app.domain.character import Character
        from app.domain.physics import PhysicsBody
        from app.Agent.agent_enemy_ai import create_enemy_ai
        
        # Crear personaje y cuerpo físico
        enemy = Character(
            name="TestEnemy",
            damage=8,
            resistence=6,
            weapon="hacha",
            description="Enemigo de prueba",
            portrait="enemy.png"
        )
        
        body = PhysicsBody(x=100, y=100, width=80, height=160)
        
        # Crear IA
        ai = create_enemy_ai(enemy, body, "NORMAL")
        
        print(f"✅ IA creada para: {enemy.name}")
        print(f"   - Agresividad: {ai.aggressiveness:.2f}")
        print(f"   - Defensividad: {ai.defensiveness:.2f}")
        print(f"   - Inteligencia: {ai.intelligence:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Error en IA del enemigo: {e}")
        return False

def test_debug_assets():
    """Prueba que el DebugAssetsManager funcione."""
    print("\n📁 Probando DebugAssetsManager...")
    
    try:
        from app.UI.debug_assets_manager import debug_assets_manager
        
        info = debug_assets_manager.get_asset_info()
        print(f"✅ Assets cargados:")
        print(f"   - Personajes: {info['characters']}")
        print(f"   - Fondos: {info['backgrounds']}")
        print(f"   - Con sprites: {info['characters_with_sprites']}")
        
        # Probar obtención de personaje
        char = debug_assets_manager.get_random_character()
        if char:
            print(f"   - Personaje aleatorio: {char.name}")
        
        return True
    except Exception as e:
        print(f"❌ Error en DebugAssetsManager: {e}")
        return False

def main():
    """Ejecuta todas las pruebas."""
    print("🚀 Iniciando pruebas rápidas...\n")
    
    tests = [
        test_character_attributes,
        test_enemy_ai,
        test_debug_assets
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
        print("\n💡 Ahora puedes ejecutar el juego con:")
        print("   python run_game.py")
        print("   o")
        print("   python main.py")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
