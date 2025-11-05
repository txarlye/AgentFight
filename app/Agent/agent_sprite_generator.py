import os
import traceback
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from app.domain.character import Character
from settings.settings import settings
from app.Agent.agents import Agent, Runner
from app.Agent.prompts.prompts_sprite_generator import PromptsSpriteGenerator
from app.Agent.Utils.path_utils import get_project_root
from app.Agent.Utils.image_provider import ImageProvider

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
prompts_gen = PromptsSpriteGenerator()
_SPRITE_AGENT = Agent(
    name="Sprite_Generator",
    instructions=prompts_gen.sistema(),
    model=None,  # Se obtendrá del proveedor
    temperature=0.7,
)

# ---------------- JSON Schemas ----------------
_SPRITE_SPEC_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "character_name": {"type": "string", "minLength": 2},
        "sprite_type": {"type": "string", "enum": ["idle", "walk", "run", "jump", "attack", "block", "hurt", "death"]},
        "description": {"type": "string", "minLength": 50},
        "color_palette": {"type": "string", "minLength": 20},
        "pose_details": {"type": "string", "minLength": 30},
        "animation_frames": {"type": "integer", "minimum": 1, "maximum": 8},
        "reference_style": {"type": "string", "minLength": 20},
    },
    "required": ["character_name", "sprite_type", "description", "color_palette", "pose_details", "animation_frames", "reference_style"],
}

# ---------------- Referencias de sprites ----------------
SPRITE_REFERENCES = {
    "warrior": {
        "description": "Guerrero clásico con armadura y espada",
        "style": "pixel art 16x16, colores vibrantes, animaciones fluidas",
        "poses": ["idle_sword", "walk_sword", "attack_slash", "block_shield"]
    },
    "mage": {
        "description": "Mago con túnica y bastón mágico",
        "style": "pixel art 16x16, colores mágicos, efectos de partículas",
        "poses": ["idle_staff", "cast_spell", "walk_robe", "magic_attack"]
    },
    "archer": {
        "description": "Arquero con arco y flechas",
        "style": "pixel art 16x16, colores naturales, movimientos ágiles",
        "poses": ["idle_bow", "draw_arrow", "shoot", "dodge"]
    }
}

# ---------------- Image Provider ----------------
_image_provider = None

def _get_image_provider():
    """Obtiene el proveedor de imágenes (lazy initialization)"""
    global _image_provider
    if _image_provider is None:
        _image_provider = ImageProvider(settings)
    return _image_provider

# ---------------- API ----------------
@traceable(name="create_sprite_specification")
def create_sprite_specification(
    character: Character,
    sprite_type: str,
    reference_style: str = "warrior"
) -> Dict[str, str]:
    """
    Crea una especificación detallada para generar un sprite.
    """
    prompts = PromptsSpriteGenerator()
    user_prompt = prompts.create_sprite_specification(character, sprite_type, reference_style)
    
    res = Runner.run_structured(
        _SPRITE_AGENT,
        prompt=user_prompt,
        tool_name="create_sprite_spec",
        parameters_schema=_SPRITE_SPEC_SCHEMA,
        tool_description="Crea especificación para sprite de personaje.",
    )
    
    return res.arguments

@traceable(name="generate_sprite_image")
def generate_sprite_image(
    sprite_spec: Dict[str, str],
    output_dir: Path,
    size: str = None
) -> Optional[str]:
    """
    Genera una imagen de sprite basada en la especificación.
    """
    size = size or settings.CHARACTER_SPRITE_SIZE
    
    # Crear nombre de archivo
    from app.Agent.Utils.function_utils import slugify
    filename = f"{slugify(sprite_spec['character_name'])}_{sprite_spec['sprite_type']}.png"
    output_path = output_dir / filename
    
    # Cache check
    if output_path.exists():
        print(f"[sprite_generator] cache hit: {output_path}")
        return str(output_path)
    
    # Construir prompt
    type_to_frames = {
        "idle": 10, "walk": 8, "run": 8, "jump": 3,
        "attack": 7, "block": 3, "hurt": 3, "death": 7,
    }
    forced_frames = type_to_frames.get(sprite_spec["sprite_type"], sprite_spec.get("animation_frames", 6))
    prompt = (
        f"SpriteSheet horizontal de {sprite_spec['character_name']} - {sprite_spec['sprite_type']}. "
        f"Descripción: {sprite_spec['description']}. "
        f"Paleta: {sprite_spec['color_palette']}. "
        f"Pose: {sprite_spec['pose_details']}. "
        f"Estilo: {sprite_spec['reference_style']}. "
        f"Debe ser un spritesheet de UNA SOLA FILA con {forced_frames} frames iguales en anchura. "
        "Cada frame mide 162x162 px, fondo completamente transparente (RGBA). "
        "Sin bordes ni márgenes entre frames. Estilo pixel art para juego de lucha."
    )
    
    try:
        print(f"[sprite_generator] generating: {output_path}")
        
        provider = _get_image_provider()
        image = provider.generate_image(
            prompt=prompt,
            size="162x162"
        )
        
        if image is None:
            print(f"[sprite_generator] ERROR: No se pudo generar el sprite")
            return None
        
        # Hacer fondo transparente si el proveedor lo soporta
        image = provider.make_transparent_background(image)
        
        # Guardar imagen
        provider.save_image(image, output_path)
        print(f"[sprite_generator] saved: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"[sprite_generator] ERROR generating sprite: {e}")
        traceback.print_exc()
        return None

def generate_character_sprite_set(
    character: Character,
    output_dir: Path,
    sprite_types: List[str] = None
) -> Dict[str, str]:
    """
    Genera un conjunto completo de sprites para un personaje.
    """
    if sprite_types is None:
        sprite_types = ["idle", "walk", "attack", "block", "hurt"]
    
    results = {}
    
    for sprite_type in sprite_types:
        try:
            # Crear especificación
            sprite_spec = create_sprite_specification(character, sprite_type)
            
            # Generar imagen
            sprite_path = generate_sprite_image(sprite_spec, output_dir)
            
            if sprite_path:
                results[sprite_type] = sprite_path
                
        except Exception as e:
            print(f"[sprite_generator] Error generating {sprite_type} sprite: {e}")
    
    return results

def download_reference_sprites():
    """
    Descarga sprites de referencia del repositorio brawler_tut.
    Esta función simula la descarga de sprites de referencia.
    """
    reference_dir = Path("app/UI/assets/images/reference_sprites")
    reference_dir.mkdir(parents=True, exist_ok=True)
    
    # Crear archivos de referencia básicos si no existen
    reference_files = ["idle.txt", "walk.txt", "attack.txt", "block.txt", "hurt.txt", "jump.txt"]
    
    for filename in reference_files:
        file_path = reference_dir / filename
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Reference sprite: {filename}\n")
                f.write(f"# This is a reference file for sprite generation\n")
                f.write(f"# Style: pixel art fighting game character\n")
            print(f"[sprite_generator] Created reference: {file_path}")
    
    print(f"[SpriteGenerator] Referencias creadas en: {reference_dir}")
    return reference_dir

def analyze_reference_sprites(reference_dir: Path) -> Dict[str, Dict]:
    """
    Analiza los sprites de referencia para extraer patrones de estilo.
    """
    analysis = {}
    
    for sprite_file in reference_dir.glob("*.png"):
        if sprite_file.is_file():
            # En un caso real, aquí se analizaría la imagen
            # Por ahora, creamos análisis simulado
            sprite_name = sprite_file.stem
            analysis[sprite_name] = {
                "style": "pixel art 16x16",
                "colors": "vibrant palette",
                "animation": "smooth transitions",
                "pose": "dynamic fighting stance"
            }
    
    return analysis

# Inicializar referencias al importar el módulo
REFERENCE_DIR = download_reference_sprites()
REFERENCE_ANALYSIS = analyze_reference_sprites(REFERENCE_DIR)
