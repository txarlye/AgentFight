"""
Clase base abstracta para proveedores de IA.
Define la interfaz común que deben implementar todos los proveedores.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Intentar importar LangSmith (opcional)
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    # LangSmith no está instalado, crear decorador dummy
    def traceable(name=None):
        def decorator(func):
            return func
        return decorator
    LANGSMITH_AVAILABLE = False


class BaseIAProvider(ABC):
    """Clase base abstracta para proveedores de IA"""
    
    def __init__(self, settings):
        """
        Inicializar proveedor
        
        Args:
            settings: Objeto de configuración con parámetros del proveedor
        """
        self.settings = settings
    
    @traceable(name="ai_provider_generate")
    @abstractmethod
    def generate(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        **kwargs
    ) -> str:
        """
        Método abstracto para generar respuesta
        Decorado con @traceable para rastreo en LangSmith
        
        Args:
            system_prompt: Prompt del sistema
            user_prompt: Prompt del usuario
            **kwargs: Parámetros adicionales (temperature, max_tokens, etc.)
        
        Returns:
            str: Respuesta generada por la IA
        """
        pass
    
    @traceable(name="ai_provider_generate_structured")
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        tool_name: str,
        parameters_schema: Dict[str, Any],
        tool_description: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Método abstracto para generar respuesta estructurada (function calling)
        Decorado con @traceable para rastreo en LangSmith
        
        Args:
            system_prompt: Prompt del sistema
            user_prompt: Prompt del usuario
            tool_name: Nombre de la función/tool
            parameters_schema: Esquema JSON de los parámetros
            tool_description: Descripción de la función
            **kwargs: Parámetros adicionales
        
        Returns:
            Dict: Argumentos parseados de la función
        """
        pass
    
    def verificar_limite(self) -> bool:
        """
        Verificar límite de consumo antes de hacer llamada
        
        Returns:
            bool: True si se puede hacer la llamada, False si se alcanzó el límite
        """
        # Por defecto, siempre permitir (puede sobrescribirse)
        if hasattr(self.settings, 'verificar_limite_consumo'):
            return self.settings.verificar_limite_consumo()
        return True
    
    def incrementar_consumo(self):
        """Incrementar contador de consumo después de llamada"""
        if hasattr(self.settings, 'incrementar_consumo'):
            self.settings.incrementar_consumo()
    
    def get_model_name(self) -> str:
        """
        Obtener nombre del modelo usado
        
        Returns:
            str: Nombre del modelo
        """
        return getattr(self, 'model', 'unknown')
    
    def is_available(self) -> bool:
        """
        Verificar si el proveedor está disponible
        
        Returns:
            bool: True si está disponible
        """
        return True

