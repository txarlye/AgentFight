"""
Prompts especializados para el agente narrador.
Contiene los prompts para crear historias, narrativas de combate y desenlaces.
"""

from typing import Dict, Any, Optional
from app.domain.character import Character


class PromptsStoryWeaver:
    """Prompts especializados para narración"""
    
    @staticmethod
    def sistema():
        """
        Obtiene las instrucciones del sistema para el agente
        
        Returns:
            str: Prompt del sistema con instrucciones generales
        """
        return """Eres un narrador experto que crea historias coherentes para un juego de combate. 
Adaptas la narrativa a las elecciones del jugador y los resultados de los combates. 
Respondes SOLO con campos estructurados en español."""
    
    @staticmethod
    def create_introduction_story(player: Optional[Character] = None):
        """
        Construye el prompt para crear introducción narrativa
        
        Args:
            player: Personaje del jugador
        
        Returns:
            str: Prompt completo para el usuario
        """
        context = ""
        if player:
            rarity = player.get_rarity_description()
            context = f"El héroe elegido es {player.name}, un guerrero {rarity.lower()} que domina {player.weapon}. "
            context += f"Con {player.damage} de daño y {player.resistence} de resistencia, "
            context += f"este {rarity.lower()} se prepara para la batalla. "
        
        return f"""Crea una introducción épica y personalizada para un juego de combate. {context}
La historia debe ser emocionante, adaptada al personaje elegido, y preparar al jugador para la aventura. 
Incluye detalles específicos sobre el arma, las habilidades y la personalidad del héroe. 
El conflicto debe ser claro y el escenario debe ser atractivo y coherente con el personaje."""
    
    @staticmethod
    def create_combat_narrative(
        player: Character,
        enemy: Character,
        combat_result: Dict[str, Any],
        story_context: Optional[Dict[str, Any]] = None
    ):
        """
        Construye el prompt para crear narrativa de combate
        
        Args:
            player: Personaje del jugador
            enemy: Personaje enemigo
            combat_result: Resultado del combate
            story_context: Contexto de la historia
        
        Returns:
            str: Prompt completo para el usuario
        """
        victory = combat_result.get("victory", False)
        performance = "victorioso" if victory else "derrotado"
        
        context = f"El jugador {player.name} ({player.weapon}) se enfrenta a {enemy.name} ({enemy.weapon}). "
        context += f"El resultado fue {performance}. "
        
        if story_context:
            context += f"Contexto previo: {story_context.get('last_event', '')} "
        
        return f"""Crea una narrativa épica para este combate: {context}
La historia debe ser dinámica y emocionante, adaptándose al resultado del combate. 
Incluye detalles sobre las armas, el ambiente y la intensidad del enfrentamiento."""
    
    @staticmethod
    def create_ending_story(
        player: Character,
        performance: Dict[str, Any],
        story_context: Optional[Dict[str, Any]] = None
    ):
        """
        Construye el prompt para crear desenlace narrativo
        
        Args:
            player: Personaje del jugador
            performance: Rendimiento del jugador
            story_context: Contexto de la historia
        
        Returns:
            str: Prompt completo para el usuario
        """
        wins = performance.get("wins", 0)
        total = performance.get("total_combats", 0)
        win_rate = performance.get("win_rate", 0)
        
        context = f"El jugador {player.name} completó {total} combates con {wins} victorias. "
        context += f"Tasa de victoria: {win_rate:.1%}. "
        
        if story_context:
            context += f"Contexto de la aventura: {story_context.get('journey_summary', '')} "
        
        return f"""Crea un desenlace épico para esta aventura: {context}
La conclusión debe reflejar el rendimiento del jugador y cerrar la historia de manera satisfactoria. 
Incluye una moraleja o lección aprendida."""
    
    @staticmethod
    def create_story_beat(
        event_type: str,
        player: Optional[Character] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Construye el prompt para crear un beat narrativo
        
        Args:
            event_type: Tipo de evento
            player: Personaje del jugador
            context: Contexto adicional
        
        Returns:
            str: Prompt completo para el usuario
        """
        event_descriptions = {
            "character_selection": "selección de personaje",
            "combat_start": "inicio de combate",
            "combat_end": "fin de combate",
            "level_up": "subida de nivel",
            "item_found": "objeto encontrado",
            "decision_made": "decisión tomada"
        }
        
        event_desc = event_descriptions.get(event_type, event_type)
        
        context_str = ""
        if player:
            context_str = f"El héroe {player.name} "
        if context:
            context_str += f"Contexto: {context} "
        
        return f"""Crea un beat narrativo corto y emocionante para: {event_desc}. {context_str}"""

