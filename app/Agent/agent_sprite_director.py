import os
from dotenv import load_dotenv
from app.Agent.agents import Agent, Runner
from app.domain.character import Character
from app.Agent.prompts.prompts_sprite_director import PromptsSpriteDirector
from typing import Dict, Any, List

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
prompts_sprite = PromptsSpriteDirector()
_SPRITE_AGENT = Agent(
    name="Sprite_Director",
    instructions=prompts_sprite.sistema(),
    model=None,  # Se obtendrá del proveedor
    temperature=0.7,  # Creativo pero coherente
)

# ---------------- JSON Schemas ----------------
_SPRITE_BRIEF_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "character_style": {"type": "string", "minLength": 30},
        "weapon_integration": {"type": "string", "minLength": 30},
        "animation_style": {"type": "string", "minLength": 20},
        "color_scheme": {"type": "string", "minLength": 20},
        "pose_dynamics": {"type": "string", "minLength": 30},
        "special_effects": {"type": "string", "minLength": 20},
    },
    "required": ["character_style", "weapon_integration", "animation_style", "color_scheme", "pose_dynamics", "special_effects"],
}

_ANIMATION_BRIEF_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "animation_name": {"type": "string", "minLength": 1},
        "description": {"type": "string", "minLength": 50},
        "key_frames": {"type": "string", "minLength": 30},
        "weapon_usage": {"type": "string", "minLength": 30},
        "effects": {"type": "string", "minLength": 20},
    },
    "required": ["animation_name", "description", "key_frames", "weapon_usage", "effects"],
}

# ---------------- API ----------------
@traceable(name="create_character_sprite_brief")
def create_character_sprite_brief(character: Character) -> Dict[str, str]:
    """
    Crea un brief para generar sprites de un personaje.
    """
    prompts = PromptsSpriteDirector()
    user_prompt = prompts.create_character_sprite_brief(character)
    
    res = Runner.run_structured(
        _SPRITE_AGENT,
        prompt=user_prompt,
        tool_name="create_character_sprite",
        parameters_schema=_SPRITE_BRIEF_SCHEMA,
        tool_description="Crea un brief para sprites de personaje.",
    )
    
    return res.arguments

@traceable(name="create_animation_brief")
def create_animation_brief(
    character: Character,
    animation_type: str
) -> Dict[str, str]:
    """
    Crea un brief para una animación específica.
    """
    prompts = PromptsSpriteDirector()
    user_prompt = prompts.create_animation_brief(character, animation_type)
    
    res = Runner.run_structured(
        _SPRITE_AGENT,
        prompt=user_prompt,
        tool_name="create_animation_brief",
        parameters_schema=_ANIMATION_BRIEF_SCHEMA,
        tool_description="Crea un brief para animación específica.",
    )
    
    return res.arguments

def create_character_sprite_set(character: Character) -> Dict[str, Dict[str, str]]:
    """
    Crea un conjunto completo de briefs para todas las animaciones de un personaje.
    """
    animations = [
        "idle", "walk_forward", "walk_backward", "jump", "crouch",
        "attack_standing", "attack_crouching", "attack_jumping",
        "throw_weapon", "block", "dodge", "victory", "defeat"
    ]
    
    sprite_set = {}
    
    # Brief general del personaje
    try:
        sprite_set["character"] = create_character_sprite_brief(character)
    except Exception as e:
        print(f"Error creando brief de personaje: {e}")
        sprite_set["character"] = {}
    
    # Briefs de animaciones
    for anim in animations:
        try:
            sprite_set[anim] = create_animation_brief(character, anim)
        except Exception as e:
            print(f"Error creando brief de animación {anim}: {e}")
            sprite_set[anim] = {}
    
    return sprite_set

def get_weapon_properties(character: Character) -> Dict[str, Any]:
    """
    Determina las propiedades del arma del personaje.
    """
    weapon = character.weapon.lower()
    
    # Armas lanzables
    throwable_weapons = ["daga", "cuchillo", "lanza", "flecha", "shuriken", "bomba", "proyectil"]
    is_throwable = any(w in weapon for w in throwable_weapons)
    
    # Armas de largo alcance
    ranged_weapons = ["arco", "ballesta", "magia", "hechizo", "proyectil"]
    is_ranged = any(w in weapon for w in ranged_weapons)
    
    # Armas de cuerpo a cuerpo
    melee_weapons = ["espada", "hacha", "martillo", "maza", "lanza", "dagas"]
    is_melee = any(w in weapon for w in melee_weapons)
    
    # Armas con munición limitada
    limited_ammo = ["flecha", "bomba", "proyectil", "shuriken"]
    has_limited_ammo = any(w in weapon for w in limited_ammo)
    
    return {
        "is_throwable": is_throwable,
        "is_ranged": is_ranged,
        "is_melee": is_melee,
        "has_limited_ammo": has_limited_ammo,
        "ammo_type": next((w for w in limited_ammo if w in weapon), None)
    }
