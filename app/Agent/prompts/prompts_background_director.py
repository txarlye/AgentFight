"""
Prompts especializados para el agente de dirección de fondos.
Contiene los prompts para crear briefs de fondos de combate y narrativa.
"""

from typing import Dict, Any, Optional
from app.domain.character import Character


class PromptsBackgroundDirector:
    """Prompts especializados para dirección de fondos"""
    
    @staticmethod
    def sistema():
        """
        Obtiene las instrucciones del sistema para el agente
        
        Returns:
            str: Prompt del sistema con instrucciones generales
        """
        return """Eres un director artístico experto que crea briefs para imágenes de fondo. 
Adaptas el estilo visual al contexto de la historia y los personajes. 
Respondes SOLO con campos estructurados en español."""
    
    @staticmethod
    def create_background_brief(
        story_context: Dict[str, Any],
        player: Optional[Character] = None,
        enemy: Optional[Character] = None
    ):
        """
        Construye el prompt para crear brief de fondo
        
        Args:
            story_context: Contexto de la historia
            player: Personaje del jugador
            enemy: Personaje enemigo
        
        Returns:
            str: Prompt completo para el usuario
        """
        context = ""
        if player:
            context += f"El héroe {player.name} usa {player.weapon}. "
        if enemy:
            context += f"El enemigo {enemy.name} usa {enemy.weapon}. "
        
        story_title = story_context.get("title", "")
        story_setting = story_context.get("setting", "")
        story_conflict = story_context.get("conflict", "")
        
        context += f"Título: {story_title}. Escenario: {story_setting}. Conflicto: {story_conflict}. "
        
        return f"""Crea un brief artístico para una imagen de fondo épica. {context}
La imagen debe ser atmosférica y preparar visualmente para el combate. 
Incluye detalles sobre el ambiente, iluminación, estilo artístico y paleta de colores. 
El fondo debe ser coherente con la narrativa y crear tensión dramática."""
    
    @staticmethod
    def create_combat_background_brief(
        player: Character,
        enemy: Character,
        combat_context: str = ""
    ):
        """
        Construye el prompt para crear brief de fondo de combate
        
        Args:
            player: Personaje del jugador
            enemy: Personaje enemigo
            combat_context: Contexto del combate
        
        Returns:
            str: Prompt completo para el usuario
        """
        context = f"Combate entre {player.name} ({player.weapon}) y {enemy.name} ({enemy.weapon}). "
        context += f"Contexto: {combat_context}. "
        
        return f"""Crea un brief para el fondo de un combate épico. {context}
El fondo debe ser dinámico y tenso, preparando para la acción. 
Incluye elementos que reflejen las armas y personalidades de los combatientes. 
La atmósfera debe ser intensa y dramática."""
    
    @staticmethod
    def create_story_background_brief(
        story_data: Dict[str, str],
        player: Optional[Character] = None
    ):
        """
        Construye el prompt para crear brief de fondo narrativo
        
        Args:
            story_data: Datos de la historia
            player: Personaje del jugador
        
        Returns:
            str: Prompt completo para el usuario
        """
        context = ""
        if player:
            context += f"Protagonista: {player.name} con {player.weapon}. "
        
        context += f"Historia: {story_data.get('title', '')} - {story_data.get('setting', '')}. "
        
        return f"""Crea un brief para ilustrar una escena narrativa. {context}
La imagen debe ser evocadora y complementar la narrativa. 
Incluye elementos visuales que refuercen la historia y el personaje. 
El estilo debe ser coherente con el tono de la narrativa."""

