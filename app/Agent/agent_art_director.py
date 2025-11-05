import os
from dataclasses import dataclass
from typing import List, Dict, Any
from dotenv import load_dotenv
from app.Agent.agents import Agent, Runner
from app.domain.character import Character
from app.Agent.prompts.prompts_art_director import PromptsArtDirector

# Intentar importar LangSmith (opcional)
try:
    from langsmith import traceable
except ImportError:
    def traceable(name=None):
        def decorator(func):
            return func
        return decorator

load_dotenv()

@dataclass
class PortraitSpec:
    name: str
    prompt: str          # prompt principal para la imagen
    style: str           # estilo/arte
    notes: str | None = None  # notas opcionales

# ---------------- Agente base ----------------
_ART_DIRECTOR = Agent(
    name="ArtDirector",
    instructions=PromptsArtDirector.sistema(),
    model=None,  # Se obtendrá del proveedor
    temperature=0.6,
)

# ---------------- JSON Schemas ----------------
def _schema_for(count: int) -> Dict[str, Any]:
    # Array de briefs con misma longitud que personajes
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "briefs": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name":  {"type": "string", "minLength": 1},
                        "prompt":{"type": "string", "minLength": 10},
                        "style": {"type": "string", "minLength": 5},
                        "notes": {"type": "string"}
                    },
                    "required": ["name", "prompt", "style"]
                }
            }
        },
        "required": ["briefs"]
    }

# ---------------- API ----------------
@traceable(name="create_portrait_briefs")
def create_portrait_briefs(characters: List[Character]) -> List[PortraitSpec]:
    """
    Crea briefs visuales para retratos de personajes.
    
    Args:
        characters: Lista de personajes para crear briefs
    
    Returns:
        List[PortraitSpec]: Lista de briefs de retratos
    """
    if not characters:
        print("[agent_art_director] ⚠️ No hay personajes para crear briefs")
        return []
    
    print(f"[agent_art_director] Creando briefs para {len(characters)} personajes")
    
    try:
        prompts = PromptsArtDirector()
        schema = _schema_for(len(characters))
        
        user_prompt = prompts.create_portrait_briefs(characters)
        print(f"[agent_art_director] Prompt generado: {len(user_prompt)} caracteres")
        
        res = Runner.run_structured(
            _ART_DIRECTOR,
            prompt=user_prompt,
            tool_name="make_portrait_briefs",
            parameters_schema=schema,
            tool_description="Devuelve 'briefs': especificaciones visuales para retratos.",
        )
        
        print(f"[agent_art_director] Respuesta recibida, arguments keys: {list(res.arguments.keys())}")
        
        raw_briefs = res.arguments.get("briefs", [])
        print(f"[agent_art_director] Briefs en respuesta: {len(raw_briefs)}")
        
        briefs: List[PortraitSpec] = []
        for i, b in enumerate(raw_briefs):
            try:
                briefs.append(PortraitSpec(
                    name=b["name"].strip(),
                    prompt=b["prompt"].strip(),
                    style=b["style"].strip(),
                    notes=(b.get("notes") or "").strip() or None
                ))
                print(f"[agent_art_director] Brief {i+1} creado: {b.get('name', 'sin nombre')}")
            except Exception as e:
                print(f"[agent_art_director] ⚠️ Error procesando brief {i+1}: {e}")
                print(f"[agent_art_director] Brief data: {b}")
                continue
        
        print(f"[agent_art_director] Total briefs creados: {len(briefs)}")
        return briefs
        
    except Exception as e:
        print(f"[agent_art_director] ❌ Error en create_portrait_briefs: {e}")
        import traceback
        traceback.print_exc()
        return []
