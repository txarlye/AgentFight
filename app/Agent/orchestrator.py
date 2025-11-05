from typing import Optional, Dict, Any, TYPE_CHECKING
from app.domain.character import Character

if TYPE_CHECKING:
    from app.UI.PygameApp import PygameApp

class Orchestrator:
    """
    Coordinador central del juego que maneja:
    - Transiciones entre escenas
    - Contexto de la historia
    - Estado del jugador
    - Flujo narrativo
    """
    
    def __init__(self, app: 'PygameApp'):
        self.app = app
        self.current_scene = None
        self.story_context: Dict[str, Any] = {}
        self.player_character: Optional[Character] = None
        self.game_state = "menu"  # menu, character_select, combat, ending
        
        # Historial de la partida
        self.combat_results = []
        self.choices_made = []
        
    def set_player(self, character: Character):
        """Establece el personaje elegido por el jugador"""
        self.player_character = character
        self.story_context["player_name"] = character.name
        self.story_context["player_weapon"] = character.weapon
        self.story_context["player_stats"] = {
            "damage": character.damage,
            "resistence": character.resistence
        }
        print(f"Orchestrator: Jugador establecido - {character.name}")
    
    def start_new_game(self):
        """Inicia una nueva partida"""
        self.story_context.clear()
        self.combat_results.clear()
        self.choices_made.clear()
        self.player_character = None
        self.game_state = "menu"
        print("Orchestrator: Nueva partida iniciada")
    
    def go_to_character_select(self):
        """Transición a la selección de personajes"""
        self.game_state = "character_select"
        self.app.set_scene("char_select")
        print("Orchestrator: Transición a selección de personajes")
    
    def go_to_combat(self):
        """Transición al combate"""
        if not self.player_character:
            print("Orchestrator: Error - No hay personaje seleccionado")
            return False
        
        self.game_state = "combat"
        # TODO: Implementar escena de combate
        # self.app.set_scene("combat")
        print("Orchestrator: Transición a combate")
        return True
    
    def go_to_ending(self):
        """Transición al desenlace"""
        self.game_state = "ending"
        # TODO: Implementar escena de desenlace
        # self.app.set_scene("ending")
        print("Orchestrator: Transición a desenlace")
    
    def go_to_menu(self):
        """Transición al menú principal"""
        self.game_state = "menu"
        self.app.set_scene("show_principal_menu")
        print("Orchestrator: Transición a menú principal")
    
    def add_combat_result(self, result: Dict[str, Any]):
        """Registra el resultado de un combate"""
        self.combat_results.append(result)
        self.story_context["last_combat"] = result
        print(f"Orchestrator: Resultado de combate registrado - {result}")
    
    def add_choice(self, choice: str, context: str):
        """Registra una elección del jugador"""
        choice_record = {
            "choice": choice,
            "context": context,
            "scene": self.current_scene
        }
        self.choices_made.append(choice_record)
        print(f"Orchestrator: Elección registrada - {choice} en {context}")
    
    def get_story_context(self) -> Dict[str, Any]:
        """Obtiene el contexto actual de la historia"""
        return {
            "player": self.player_character,
            "combat_results": self.combat_results,
            "choices": self.choices_made,
            "game_state": self.game_state,
            **self.story_context
        }
    
    def is_game_complete(self) -> bool:
        """Verifica si la partida está completa"""
        return len(self.combat_results) > 0 and self.game_state == "ending"
    
    def get_player_performance(self) -> Dict[str, Any]:
        """Calcula el rendimiento del jugador"""
        if not self.combat_results:
            return {"wins": 0, "losses": 0, "total_combats": 0}
        
        wins = sum(1 for result in self.combat_results if result.get("victory", False))
        total = len(self.combat_results)
        
        return {
            "wins": wins,
            "losses": total - wins,
            "total_combats": total,
            "win_rate": wins / total if total > 0 else 0
        }
    
    def prefetch_next_pack(self):
        """Prefetch del siguiente pack de contenido (enemigos, fondos, etc.)"""
        if not self.player_character:
            print("Orchestrator: No hay personaje para prefetch")
            return
        
        print(f"Orchestrator: Iniciando prefetch para {self.player_character.name}")
        
        # Aquí se pueden agregar más elementos para prefetch
        # Por ejemplo: generar enemigos, fondos, etc.
        
        # Por ahora, solo marcamos que el prefetch está activo
        self.story_context["prefetch_active"] = True

# Instancia global del orchestrator
_orchestrator: Optional[Orchestrator] = None

def get_orchestrator(app: 'PygameApp' = None) -> Orchestrator:
    """Obtiene la instancia global del orchestrator"""
    global _orchestrator
    if _orchestrator is None and app is not None:
        _orchestrator = Orchestrator(app)
    return _orchestrator

def set_orchestrator(orchestrator: Orchestrator):
    """Establece la instancia global del orchestrator"""
    global _orchestrator
    _orchestrator = orchestrator
