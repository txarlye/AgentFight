"""
Abstracción para generación de imágenes.
Usa la implementación existente de image_providers.py que soporta
Stable Diffusion (por defecto) y OpenAI como fallback.
"""

from typing import Optional
from pathlib import Path
from PIL import Image


class ImageProvider:
    """
    Wrapper para el sistema de generación de imágenes existente.
    Usa image_providers.py que ya tiene Stable Diffusion implementado.
    """
    
    def __init__(self, settings):
        """
        Inicializar proveedor de imágenes usando la implementación existente
        
        Args:
            settings: Objeto de configuración
        """
        self.settings = settings
        
        # Importar el factory existente de image_providers
        from app.Agent.image_providers import get_image_provider
        
        # Obtener el proveedor configurado (Stable Diffusion por defecto)
        self.provider = get_image_provider()
        
        # Detectar tipo de proveedor
        self.is_openai = hasattr(self.provider, 'client') or 'OpenAI' in type(self.provider).__name__
        self.is_stable_diffusion = 'StableDiffusion' in type(self.provider).__name__
    
    def generate_image(
        self,
        prompt: str,
        size: str = "512x512",
        background: Optional[str] = None,
        **kwargs
    ) -> Optional[Image.Image]:
        """
        Genera una imagen usando el proveedor configurado
        
        Args:
            prompt: Descripción de la imagen a generar
            size: Tamaño de la imagen (512x512, 1024x1024, etc.)
            background: Color de fondo (solo para OpenAI)
            **kwargs: Parámetros adicionales
        
        Returns:
            Image.Image: Imagen generada, o None si falla
        """
        try:
            # Usar el proveedor existente
            if self.is_openai:
                # OpenAI acepta parámetro background
                image = self.provider.generate_image(
                    prompt=prompt,
                    size=size,
                    background=background
                )
            else:
                # Stable Diffusion u otros no aceptan background
                image = self.provider.generate_image(
                    prompt=prompt,
                    size=size,
                    **kwargs
                )
            
            return image
            
        except Exception as e:
            print(f"[ImageProvider] Error generating image: {e}")
            return None
    
    def save_image(self, image: Image.Image, output_path: Path) -> bool:
        """
        Guarda una imagen PIL
        
        Args:
            image: Imagen PIL a guardar
            output_path: Ruta donde guardar la imagen
        
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            if image:
                image.save(output_path, "PNG")
                return True
            return False
        except Exception as e:
            print(f"[ImageProvider] Error saving image: {e}")
            return False
    
    def make_transparent_background(self, image: Image.Image) -> Image.Image:
        """
        Hace el fondo de una imagen transparente (si el proveedor lo soporta)
        
        Args:
            image: Imagen PIL
        
        Returns:
            Image.Image: Imagen con fondo transparente
        """
        if hasattr(self.provider, 'make_transparent_background'):
            return self.provider.make_transparent_background(image)
        return image

