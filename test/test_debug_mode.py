#!/usr/bin/env python3
"""
Script de prueba para verificar el modo debug de lucha.
"""

import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

def test_debug_assets_manager():
    """Prueba el DebugAssetsManager."""
    print("🔧 Probando DebugAssetsManager...")
    try:
        from app.UI.debug_assets_manager import debug_assets_manager
        
        # Obtener información de assets
        info = debug_assets_manager.get_asset_info()
        print(f"✅ DebugAssetsManager funcionando:")
        print(f"   - Personajes disponibles: {info['characters']}")
        print(f"   - Fondos disponibles: {info['backgrounds']}")
        print(f"   - Personajes con sprites: {info['characters_with_sprites']}")
        
        # Probar obtención de personaje aleatorio
        character = debug_assets_manager.get_random_character()
        if character:
            print(f"   - Personaje aleatorio: {character.name}")
            print(f"   - Stats: DMG={character.damage}, DEF={character.resistence}")
        else:
            print("   - No hay personajes disponibles")
        
        # Probar obtención de fondo aleatorio
        background = debug_assets_manager.get_random_background()
        if background:
            print(f"   - Fondo aleatorio: {Path(background).name}")
        else:
            print("   - No hay fondos disponibles")
        
        return True
    except Exception as e:
        print(f"❌ Error en DebugAssetsManager: {e}")
        return False

def test_debug_fight_scene():
    """Prueba la creación de la escena de debug de lucha."""
    print("\n⚔️ Probando DebugFightScene...")
    try:
        from app.UI.scenes.debug_fight_scene import DebugFightScene
        
        # Crear una aplicación mock para la prueba
        class MockApp:
            def __init__(self):
                self.orchestrator = None
            
            def set_scene(self, scene_name):
                print(f"   - Cambiando a escena: {scene_name}")
        
        mock_app = MockApp()
        
        # Crear la escena
        scene = DebugFightScene(mock_app)
        
        print(f"✅ DebugFightScene creada exitosamente:")
        print(f"   - Escena inicializada: {scene is not None}")
        print(f"   - Sistema de físicas: {scene.physics_engine is not None}")
        print(f"   - Debug info habilitado: {scene.show_debug_info}")
        
        return True
    except Exception as e:
        print(f"❌ Error en DebugFightScene: {e}")
        return False

def test_settings_integration():
    """Prueba la integración con las configuraciones."""
    print("\n⚙️ Probando integración de configuraciones...")
    try:
        from settings.settings import settings
        
        print(f"✅ Configuraciones de debug:")
        print(f"   - debug_fight_mode: {settings.debug_fight_mode}")
        print(f"   - use_existing_assets: {settings.use_existing_assets}")
        print(f"   - generate_backgrounds: {settings.generate_backgrounds}")
        print(f"   - generate_character_sprites: {settings.generate_character_sprites}")
        
        return True
    except Exception as e:
        print(f"❌ Error en configuraciones: {e}")
        return False

def test_assets_loading():
    """Prueba la carga de assets existentes."""
    print("\n📁 Probando carga de assets existentes...")
    try:
        from pathlib import Path
        from settings.settings import settings
        
        # Verificar directorios
        portrait_dir = Path(settings.PORTRAIT_DIR)
        sprites_dir = Path("app/UI/assets/images/sprites")
        backgrounds_dir = Path(settings.BG_FIGHT_DIR)
        
        print(f"✅ Directorios de assets:")
        print(f"   - Retratos: {portrait_dir} ({'Existe' if portrait_dir.exists() else 'No existe'})")
        print(f"   - Sprites: {sprites_dir} ({'Existe' if sprites_dir.exists() else 'No existe'})")
        print(f"   - Fondos: {backgrounds_dir} ({'Existe' if backgrounds_dir.exists() else 'No existe'})")
        
        # Contar archivos
        if portrait_dir.exists():
            portrait_count = len(list(portrait_dir.glob("*.png")))
            print(f"   - Retratos encontrados: {portrait_count}")
        
        if backgrounds_dir.exists():
            bg_count = len(list(backgrounds_dir.glob("*.png")))
            print(f"   - Fondos encontrados: {bg_count}")
        
        return True
    except Exception as e:
        print(f"❌ Error verificando assets: {e}")
        return False

def main():
    """Ejecuta todas las pruebas del modo debug."""
    print("🚀 Iniciando pruebas del modo debug de lucha...\n")
    
    tests = [
        test_settings_integration,
        test_assets_loading,
        test_debug_assets_manager,
        test_debug_fight_scene
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
        print("🎉 ¡Todas las pruebas pasaron! El modo debug está listo.")
        print("\n💡 Para usar el modo debug:")
        print("   1. Ejecuta el juego principal: python main.py")
        print("   2. En el menú principal, presiona [3] para Debug Fight")
        print("   3. Usa las flechas para mover, SPACE para atacar")
        print("   4. Presiona N para nueva lucha, R para reset")
        print("   5. Presiona D para mostrar/ocultar información de debug")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los errores arriba.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
