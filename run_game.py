#!/usr/bin/env python3
"""
Script de inicio rápido para SimpleFight v3
"""

import sys
import os
from pathlib import Path

def main():
    """Ejecuta el juego con configuración automática."""
    print("🚀 Iniciando SimpleFight v3...")
    
    # Añadir el directorio raíz al path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Verificar dependencias
    try:
        import pygame
        print("✅ Pygame encontrado")
    except ImportError:
        print("❌ Pygame no encontrado. Instalando...")
        os.system("pip install pygame")
        try:
            import pygame
            print("✅ Pygame instalado correctamente")
        except ImportError:
            print("❌ Error instalando pygame")
            return
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv encontrado")
    except ImportError:
        print("❌ python-dotenv no encontrado. Instalando...")
        os.system("pip install python-dotenv")
    
    try:
        from openai import OpenAI
        print("✅ OpenAI encontrado")
    except ImportError:
        print("❌ OpenAI no encontrado. Instalando...")
        os.system("pip install openai")
    
    print("\n🎮 Iniciando juego...")
    print("💡 Controles:")
    print("   - [1] Seleccionar personaje")
    print("   - [2] Iniciar aventura")
    print("   - [3] Debug Fight (si está habilitado)")
    print("   - [0] Salir")
    print("\n" + "="*50)
    
    # Importar y ejecutar el juego
    try:
        from main import main as game_main
        game_main()
    except Exception as e:
        print(f"❌ Error ejecutando el juego: {e}")
        print("💡 Intenta ejecutar: python main.py")

if __name__ == "__main__":
    main()
