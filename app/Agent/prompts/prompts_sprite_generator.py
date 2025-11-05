"""
Prompts especializados para el agente generador de sprites.
Contiene los prompts para crear especificaciones de sprites.
"""

from typing import Dict
from app.domain.character import Character


class PromptsSpriteGenerator:
    """Prompts especializados para generación de sprites"""
    
    @staticmethod
    def sistema():
        """
        Obtiene las instrucciones del sistema para el agente
        
        Returns:
            str: Prompt del sistema con instrucciones generales
        """
        return """Eres un artista experto en sprites de videojuegos de lucha. 
Creas sprites pixel art de alta calidad basándote en referencias existentes. 
Mantienes consistencia visual y animaciones fluidas. 
Respondes SOLO con campos estructurados en español."""
    
    @staticmethod
    def create_sprite_specification(
        character: Character,
        sprite_type: str,
        reference_style: str = "warrior"
    ):
        """
        Construye el prompt para crear especificación de sprite
        
        Args:
            character: Personaje para el sprite
            sprite_type: Tipo de sprite
            reference_style: Estilo de referencia
        
        Returns:
            str: Prompt completo para el usuario
        """
        context = f"Personaje: {character.name} con {character.weapon}. "
        context += f"Stats: Daño={character.damage}, Resistencia={character.resistence}, Vida={character.health}. "
        
        reference_descriptions = {
            "warrior": "Guerrero clásico con armadura y espada",
            "mage": "Mago con túnica y bastón mágico",
            "archer": "Arquero con arco y flechas"
        }
        
        reference = reference_descriptions.get(reference_style, reference_descriptions["warrior"])
        
        return f"""Crea una especificación para un sprite de {sprite_type}. {context}
Estilo de referencia: {reference}. 
El sprite debe ser coherente con el arma y personalidad del personaje. 
Incluye detalles sobre colores, pose, animación y estilo visual."""

