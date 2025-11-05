import os
import unicodedata
from dotenv import load_dotenv
from app.Agent.agents import Agent, Runner
from app.domain.character import Character
from app.Agent.prompts.prompts_character_creator import PromptsCharacterCreator
from app.Agent.Utils.function_utils import normalize_name, clip_value

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
prompts_char = PromptsCharacterCreator()
_AGENT = Agent(
    name="Enemy_creator",
    instructions=prompts_char.sistema(),
    model=None,  # Se obtendrá del proveedor
    temperature=0.7,   # un poco más alto para variedad
)

# ---------------- JSON Schemas ----------------
_ITEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name":        {"type": "string",  "minLength": 1},
        "damage":      {"type": "integer", "minimum": 1, "maximum": 10},
        "resistence":  {"type": "integer", "minimum": 1, "maximum": 10},
        "weapon":      {"type": "string",  "minLength": 1},
        "description": {"type": "string",  "minLength": 1},
    },
    "required": ["name", "damage", "resistence", "weapon", "description"],
}

def _candidates_schema(count: int):
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "candidates": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "uniqueItems": True,    # ← el modelo intentará que no repita
                "items": _ITEM_SCHEMA
            }
        },
        "required": ["candidates"]
    }

# ---------------- API ----------------
@traceable(name="create_character")
def create_character(banned_norm_names: set[str] | None = None) -> Character:
    """Crea 1 enemigo (evitando nombres en banned_norm_names si se pasa)."""
    banned_norm_names = banned_norm_names or set()
    
    prompts = PromptsCharacterCreator()
    user_prompt = prompts.create_character(list(banned_norm_names))
    
    res = Runner.run_structured(
        _AGENT,
        prompt=user_prompt,
        tool_name="create_enemy",
        parameters_schema=_ITEM_SCHEMA,
        tool_description="Devuelve un enemigo jugable.",
    )
    
    d = res.arguments
    return Character(
        name=(d["name"] or "").strip(),
        damage=clip_value(d.get("damage", 5)),
        resistence=clip_value(d.get("resistence", 5)),
        weapon=(d["weapon"] or "").strip(),
        description=(d["description"] or "").strip(),
        portrait="",  # Se asignará después en char_select_scene
    )

@traceable(name="create_candidates")
def create_candidates(n: int = 4) -> list[Character]:
    """
    Crea EXACTAMENTE n enemigos:
    - 1 llamada en lote con uniqueItems
    - deduplicación local por nombre normalizado
    - relleno con llamadas unitarias si hiciera falta
    """
    prompts = PromptsCharacterCreator()
    schema = _candidates_schema(n)
    user_prompt = prompts.create_candidates(n)
    
    res = Runner.run_structured(
        _AGENT,
        prompt=user_prompt,
        tool_name="create_enemies",
        parameters_schema=schema,
        tool_description="Devuelve 'candidates': lista de enemigos.",
    )

    raw_list = res.arguments.get("candidates", [])
    out: list[Character] = []
    seen: set[str] = set()

    for d in raw_list:
        name = (d.get("name") or "").strip()
        key  = normalize_name(name)
        if not name or key in seen:
            continue
        seen.add(key)
        out.append(
            Character(
                name=name,
                damage=clip_value(d.get("damage", 5)),
                resistence=clip_value(d.get("resistence", 5)),
                weapon=(d.get("weapon") or "").strip(),
                description=(d.get("description") or "").strip(),
                portrait="",  # Se asignará después en char_select_scene
            )
        )

    # 2) si faltan, rellenar evitando duplicados
    attempts = 0
    while len(out) < n and attempts < n * 3:
        attempts += 1
        ch = create_character(banned_norm_names=seen)
        key = normalize_name(ch.name)
        if key in seen or not ch.name.strip():
            continue
        seen.add(key)
        out.append(ch)

    # 3) seguridad: si aún faltaran por algún motivo extremo
    while len(out) < n:
        k = len(out) + 1
        out.append(Character(
            name=f"Enemigo_{k}",
            damage=5,
            resistence=5,
            weapon="arma",
            description="placeholder",
            portrait=""  # Se asignará después en char_select_scene
        ))

    return out
