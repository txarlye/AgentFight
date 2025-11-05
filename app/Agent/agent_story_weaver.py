# app/Agent/agent_story_weaver.py
from __future__ import annotations
import os
from dotenv import load_dotenv
from app.Agent.agents import Agent, Runner
from app.domain.character import Character
from app.Agent.prompts.prompts_story_weaver import PromptsStoryWeaver
from typing import Dict, Any, List, Optional

# Intentar importar LangSmith (opcional)
try:
    from langsmith import traceable
except ImportError:
    def traceable(name=None):
        def decorator(func):
            return func
        return decorator

load_dotenv()

# ---------------- Agente base ----------------
prompts_story = PromptsStoryWeaver()
_STORY_AGENT = Agent(
    name="Story_Weaver",
    instructions=prompts_story.sistema(),
    model=None,  # Se obtendrá del proveedor
    temperature=0.8,  # Más creativo para narrativa
)

# ---------------- JSON Schemas ----------------
_INTRO_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "introduction": {"type": "string", "minLength": 50},
        "conflict": {"type": "string", "minLength": 30},
        "setting": {"type": "string", "minLength": 30},
    },
    "required": ["title", "introduction", "conflict", "setting"],
}

_COMBAT_NARRATIVE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "setup": {"type": "string", "minLength": 30},
        "action": {"type": "string", "minLength": 50},
        "climax": {"type": "string", "minLength": 30},
        "outcome": {"type": "string", "minLength": 30},
    },
    "required": ["setup", "action", "climax", "outcome"],
}

_ENDING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "epilogue": {"type": "string", "minLength": 50},
        "conclusion": {"type": "string", "minLength": 30},
        "moral": {"type": "string", "minLength": 20},
    },
    "required": ["epilogue", "conclusion", "moral"],
}

# ---------------- API ----------------
@traceable(name="create_introduction_story")
def create_introduction_story(player: Character = None) -> Dict[str, str]:
    """
    Crea la introducción narrativa de la partida.
    Si se proporciona un jugador, personaliza la historia.
    """
    prompts = PromptsStoryWeaver()
    user_prompt = prompts.create_introduction_story(player)
    
    res = Runner.run_structured(
        _STORY_AGENT,
        prompt=user_prompt,
        tool_name="create_introduction",
        parameters_schema=_INTRO_SCHEMA,
        tool_description="Crea la introducción narrativa personalizada del juego.",
    )
    
    return res.arguments

@traceable(name="create_combat_narrative")
def create_combat_narrative(
    player: Character, 
    enemy: Character, 
    combat_result: Dict[str, Any],
    story_context: Dict[str, Any] = None
) -> Dict[str, str]:
    """
    Crea la narrativa de un combate específico.
    """
    prompts = PromptsStoryWeaver()
    user_prompt = prompts.create_combat_narrative(player, enemy, combat_result, story_context)
    
    res = Runner.run_structured(
        _STORY_AGENT,
        prompt=user_prompt,
        tool_name="create_combat_narrative",
        parameters_schema=_COMBAT_NARRATIVE_SCHEMA,
        tool_description="Crea la narrativa de un combate específico.",
    )
    
    return res.arguments

@traceable(name="create_ending_story")
def create_ending_story(
    player: Character,
    performance: Dict[str, Any],
    story_context: Dict[str, Any] = None
) -> Dict[str, str]:
    """
    Crea el desenlace narrativo basado en el rendimiento del jugador.
    """
    prompts = PromptsStoryWeaver()
    user_prompt = prompts.create_ending_story(player, performance, story_context)
    
    res = Runner.run_structured(
        _STORY_AGENT,
        prompt=user_prompt,
        tool_name="create_ending",
        parameters_schema=_ENDING_SCHEMA,
        tool_description="Crea el desenlace narrativo de la partida.",
    )
    
    return res.arguments

@traceable(name="create_story_beat")
def create_story_beat(
    event_type: str,
    player: Character = None,
    context: Dict[str, Any] = None
) -> str:
    """
    Crea un beat narrativo específico para un evento.
    """
    prompts = PromptsStoryWeaver()
    user_prompt = prompts.create_story_beat(event_type, player, context)
    
    try:
        res = Runner.run_structured(
            _STORY_AGENT,
            prompt=user_prompt,
            tool_name="create_story_beat",
            parameters_schema={
                "type": "object",
                "properties": {"beat": {"type": "string", "minLength": 20}},
                "required": ["beat"]
            },
            tool_description="Crea un beat narrativo específico.",
        )
        return res.arguments.get("beat", "")
    except Exception:
        return f"Un momento épico ocurre en la aventura de {player.name if player else 'el héroe'}."

# ---------------- Funciones de utilidad ----------------
def summarize_journey(combat_results: List[Dict[str, Any]], choices: List[Dict[str, Any]]) -> str:
    """
    Crea un resumen de la jornada del jugador.
    """
    if not combat_results and not choices:
        return "Una aventura apenas comenzaba..."
    
    summary_parts = []
    
    if choices:
        character_choice = next((c for c in choices if c.get("context") == "character_selection"), None)
        if character_choice:
            summary_parts.append(f"El héroe {character_choice['choice']} comenzó su viaje.")
    
    if combat_results:
        victories = sum(1 for r in combat_results if r.get("victory", False))
        total_combats = len(combat_results)
        summary_parts.append(f"Enfrentó {total_combats} desafíos, emergiendo victorioso en {victories} ocasiones.")
    
    return " ".join(summary_parts) if summary_parts else "Una aventura legendaria tuvo lugar."
