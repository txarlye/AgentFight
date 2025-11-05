"""
Prompts especializados para el agente de dirección de sprites.
Contiene los prompts para crear briefs de sprites y animaciones.
"""

from typing import Dict, Any
from app.domain.character import Character


class PromptsSpriteDirector:
    """Prompts especializados para dirección de sprites"""
    
    @staticmethod
    def sistema():
        """
        Obtiene las instrucciones del sistema para el agente
        
        Returns:
            str: Prompt del sistema con instrucciones generales
        """
        return """Eres un director artístico experto que crea briefs para sprites de personajes. 
Adaptas el estilo visual al personaje y sus armas. 
Respondes SOLO con campos estructurados en español."""
    
    @staticmethod
    def create_character_sprite_brief(character: Character):
        """
        Construye el prompt para crear brief de sprite de personaje
        
        Args:
            character: Personaje para crear el brief
        
        Returns:
            str: Prompt completo para el usuario
        """
        context = f"Personaje: {character.name}, Arma: {character.weapon}, Rareza: {character.get_rarity_description()}. "
        context += f"Descripción: {character.description}. "
        
        return f"""Crea un brief artístico para sprites de personaje: {context}
El sprite debe ser coherente con el arma y la personalidad del personaje. 
Incluye detalles sobre el estilo visual, integración del arma, y dinámicas de pose. 
El diseño debe ser atractivo y funcional para animaciones de combate."""
    
    @staticmethod
    def create_animation_brief(character: Character, animation_type: str):
        """
        Construye el prompt para crear brief de animación
        
        Args:
            character: Personaje para la animación
            animation_type: Tipo de animación
        
        Returns:
            str: Prompt completo para el usuario
        """
        animation_descriptions = {
            "idle": "posición de espera",
            "walk_forward": "caminar hacia adelante",
            "walk_backward": "caminar hacia atrás",
            "jump": "salto",
            "crouch": "agacharse",
            "attack_standing": "ataque de pie",
            "attack_crouching": "ataque agachado",
            "attack_jumping": "ataque saltando",
            "throw_weapon": "lanzar arma",
            "block": "bloquear",
            "dodge": "esquivar",
            "victory": "victoria",
            "defeat": "derrota"
        }
        
        anim_desc = animation_descriptions.get(animation_type, animation_type)
        
        context = f"Personaje: {character.name}, Arma: {character.weapon}. "
        context += f"Animación: {anim_desc}. "
        
        throwable_weapons = ["daga", "cuchillo", "lanza", "flecha", "shuriken", "bomba"]
        is_throwable = any(weapon in character.weapon.lower() for weapon in throwable_weapons)
        
        if animation_type == "throw_weapon" and is_throwable:
            context += "El arma es lanzable y debe mostrar la acción de lanzamiento. "
        elif animation_type == "throw_weapon" and not is_throwable:
            context += "El arma no es lanzable, mostrar movimiento de ataque a distancia. "
        
        return f"""Crea un brief para animación de combate: {context}
La animación debe ser dinámica y coherente con el arma del personaje. 
Incluye detalles sobre los key frames, uso del arma y efectos visuales. 
La animación debe ser fluida y expresiva."""

