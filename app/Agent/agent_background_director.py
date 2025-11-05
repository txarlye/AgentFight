import os
from dotenv import load_dotenv
from app.Agent.agents import Agent, Runner
from app.domain.character import Character
from app.Agent.prompts.prompts_background_director import PromptsBackgroundDirector
from typing import Dict, Any, Optional

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
prompts_bg = PromptsBackgroundDirector()
_BACKGROUND_AGENT = Agent(
    name="Background_Director",
    instructions=prompts_bg.sistema(),
    model=None,  # Se obtendrá del proveedor
    temperature=0.7,  # Creativo pero coherente
)

# ---------------- JSON Schemas ----------------
_BACKGROUND_BRIEF_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "setting": {"type": "string", "minLength": 30},
        "mood": {"type": "string", "minLength": 20},
        "lighting": {"type": "string", "minLength": 20},
        "style": {"type": "string", "minLength": 20},
        "elements": {"type": "string", "minLength": 30},
        "color_palette": {"type": "string", "minLength": 20},
    },
    "required": ["setting", "mood", "lighting", "style", "elements", "color_palette"],
}

# ---------------- API ----------------
@traceable(name="create_background_brief")
def create_background_brief(
    story_context: Dict[str, Any],
    player: Optional[Character] = None,
    enemy: Optional[Character] = None
) -> Dict[str, str]:
    """
    Crea un brief para generar una imagen de fondo basada en el contexto de la historia.
    """
    prompts = PromptsBackgroundDirector()
    user_prompt = prompts.create_background_brief(story_context, player, enemy)
    
    res = Runner.run_structured(
        _BACKGROUND_AGENT,
        prompt=user_prompt,
        tool_name="create_background_brief",
        parameters_schema=_BACKGROUND_BRIEF_SCHEMA,
        tool_description="Crea un brief para generar imagen de fondo.",
    )
    
    return res.arguments

@traceable(name="create_combat_background_brief")
def create_combat_background_brief(
    player: Character,
    enemy: Character,
    combat_context: str = ""
) -> Dict[str, str]:
    """
    Crea un brief específico para el fondo de un combate.
    """
    prompts = PromptsBackgroundDirector()
    user_prompt = prompts.create_combat_background_brief(player, enemy, combat_context)
    
    res = Runner.run_structured(
        _BACKGROUND_AGENT,
        prompt=user_prompt,
        tool_name="create_combat_background",
        parameters_schema=_BACKGROUND_BRIEF_SCHEMA,
        tool_description="Crea un brief para fondo de combate.",
    )
    
    return res.arguments

@traceable(name="create_story_background_brief")
def create_story_background_brief(
    story_data: Dict[str, str],
    player: Optional[Character] = None
) -> Dict[str, str]:
    """
    Crea un brief para el fondo de una escena narrativa.
    """
    prompts = PromptsBackgroundDirector()
    user_prompt = prompts.create_story_background_brief(story_data, player)
    
    res = Runner.run_structured(
        _BACKGROUND_AGENT,
        prompt=user_prompt,
        tool_name="create_story_background",
        parameters_schema=_BACKGROUND_BRIEF_SCHEMA,
        tool_description="Crea un brief para fondo narrativo.",
    )
    
    return res.arguments
