"""
Factory para crear proveedores de IA según configuración.
Permite cambiar entre proveedores sin modificar código de agentes.
"""

from .base_provider import BaseIAProvider


class ProviderFactory:
    """Factory para crear proveedores de IA según configuración"""
    
    @staticmethod
    def crear_provider(settings) -> BaseIAProvider:
        """
        Crear proveedor según configuración
        
        Args:
            settings: Objeto de configuración con proveedor_ia o AI_PROVIDER
        
        Returns:
            BaseIAProvider: Instancia del proveedor configurado
        
        Raises:
            ValueError: Si el proveedor no está soportado
        """
        # Obtener proveedor desde settings
        ai_config = getattr(settings, 'AI_PROVIDER_CONFIG', {})
        proveedor = ai_config.get('provider', 'openai').lower()
        
        # Fallback a atributo antiguo si existe
        if not proveedor or proveedor == 'openai':
            proveedor = getattr(settings, 'proveedor_ia', 'openai').lower()
        
        if proveedor == "openai":
            from .openai_provider import OpenAIProvider
            return OpenAIProvider(settings)
        elif proveedor == "ollama":
            from .ollama_provider import OllamaProvider
            return OllamaProvider(settings)
        else:
            raise ValueError(f"Proveedor no soportado: {proveedor}. Soportados: openai, ollama")
    
    @staticmethod
    def get_available_providers():
        """
        Obtener lista de proveedores disponibles
        
        Returns:
            list: Lista de nombres de proveedores
        """
        return ["openai", "ollama"]

