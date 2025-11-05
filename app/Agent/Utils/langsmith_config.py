"""
Configuración de LangSmith para trazabilidad y observabilidad.
Permite rastrear todas las llamadas a IA en LangSmith.
"""

import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()


def setup_langsmith():
    """
    Configura las variables de entorno para LangSmith.
    Se ejecuta automáticamente al importar este módulo si está configurado.
    
    Returns:
        bool: True si LangSmith está configurado correctamente, False si no
    """
    # Variables básicas de LangSmith
    os.environ['LANGCHAIN_TRACING_V2'] = os.getenv('LANGCHAIN_TRACING_V2', 'false')
    os.environ['LANGCHAIN_ENDPOINT'] = os.getenv('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')
    
    # Proyecto (puede venir del .env o usar default)
    project = os.getenv('LANGCHAIN_PROJECT', 'SimpleFight_v3')
    os.environ['LANGCHAIN_PROJECT'] = project
    
    # Verificar API key
    api_key = os.getenv('LANGCHAIN_API_KEY')
    if not api_key:
        # LangSmith no está configurado, no es un error
        return False
    
    # Si está configurado, activar tracing
    if os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true':
        print(f"✅ LangSmith configurado - Proyecto: {project}")
        return True
    
    return False


def get_langsmith_info():
    """
    Obtiene información sobre la configuración actual de LangSmith
    
    Returns:
        dict: Información de configuración
    """
    return {
        'tracing_enabled': os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true',
        'endpoint': os.getenv('LANGCHAIN_ENDPOINT'),
        'api_key_configured': bool(os.getenv('LANGCHAIN_API_KEY')),
        'project': os.getenv('LANGCHAIN_PROJECT', 'SimpleFight_v3')
    }


# Configurar LangSmith automáticamente al importar
_setup_result = setup_langsmith()

