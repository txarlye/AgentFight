"""
Prompts especializados para el agente de dirección artística.
Contiene los prompts para crear briefs visuales de retratos.
"""

from typing import List
from app.domain.character import Character


class PromptsArtDirector:
    """Prompts especializados para dirección artística"""
    
    @staticmethod
    def sistema():
        """
        Obtiene las instrucciones del sistema para el agente
        
        Returns:
            str: Prompt del sistema con instrucciones generales
        """
        return """Actúas como director de arte. Recibes una lista de personajes con 
name, damage, resistence, weapon y description. Para cada uno, 
devuelves un brief visual MUY BREVE (máximo 60 palabras) para generar su retrato.

IMPORTANTE: Debes devolver un objeto JSON con un array "briefs" donde cada elemento tiene EXACTAMENTE estos campos:
- "name": el nombre del personaje (string)
- "prompt": descripción visual breve del personaje, pose y arma visible (máximo 60 palabras, string)
- "style": estilo visual (ej: "pixel art, retro game, 2D sprite", string)
- "notes": notas adicionales opcionales (string, puede estar vacío)

Usa un estilo consistente de videojuego 2D. Español."""
    
    @staticmethod
    def create_portrait_briefs(characters: List[Character]):
        """
        Construye el prompt para crear briefs de retratos
        
        Args:
            characters: Lista de personajes para crear briefs
        
        Returns:
            str: Prompt completo para el usuario
        """
        packed = [
            {
                "name": c.name,
                "damage": c.damage,
                "resistence": c.resistence,
                "weapon": c.weapon,
                "description": c.description[:220]
            }
            for c in characters
        ]
        
        return f"""Genera un brief visual MUY BREVE por personaje (máximo 60 palabras cada uno en el campo "prompt"). 
Cada brief debe tener:
- "name": el nombre del personaje
- "prompt": descripción visual breve (personaje, pose, arma visible). Medio cuerpo, fondo transparente
- "style": estilo visual (ej: "pixel art, retro game, 2D sprite")
- "notes": opcional

Personajes: {packed}"""

