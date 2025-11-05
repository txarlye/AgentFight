import os, base64, re, traceback
from pathlib import Path
from typing import Dict, List
from concurrent.futures     import ThreadPoolExecutor, as_completed
from dotenv                 import load_dotenv
from app.domain.character   import Character
from settings.settings      import settings
from app.Agent.agent_art_director import PortraitSpec
from app.Agent.image_providers import get_image_provider
from app.Agent.prompts.prompts_image_renderer import PromptsImageRenderer

# Intentar importar LangSmith (opcional)
try:
    from langsmith import traceable
except ImportError:
    def traceable(name=None):
        def decorator(func):
            return func
        return decorator

# ---------------- Config / cliente ----------------
load_dotenv()

# Inicializar proveedor de imágenes
_image_provider = None

def _get_image_provider():
    """Lazy loading del proveedor de imágenes"""
    global _image_provider
    if _image_provider is None:
        _image_provider = get_image_provider()
    return _image_provider

# Tamaños permitidos
ALLOWED_SIZES = {"1024x1024", "1024x1536", "1536x1024", "auto", "512x512", "256x256", "162x162"}

# Lee tamaños desde settings
DEFAULT_PORTRAIT_SIZE = getattr(settings, 'PORTRAIT_SIZE_GEN', "512x512")
DEFAULT_SPRITE_SIZE = getattr(settings, 'CHARACTER_SPRITE_SIZE', "256x256")
DEFAULT_BACKGROUND_SIZE = getattr(settings, 'BACKGROUND_SIZE', "512x512")

# Validar tamaños
if DEFAULT_PORTRAIT_SIZE not in ALLOWED_SIZES:
    DEFAULT_PORTRAIT_SIZE = "512x512"
if DEFAULT_SPRITE_SIZE not in ALLOWED_SIZES:
    DEFAULT_SPRITE_SIZE = "256x256"
if DEFAULT_BACKGROUND_SIZE not in ALLOWED_SIZES:
    DEFAULT_BACKGROUND_SIZE = "512x512"

print(f"[image_renderer] module file: {__file__}")
print(f"[image_renderer] provider: {settings.IMAGE_PROVIDER}")
print(f"[image_renderer] portrait size: {DEFAULT_PORTRAIT_SIZE}")
print(f"[image_renderer] sprite size: {DEFAULT_SPRITE_SIZE}")
print(f"[image_renderer] background size: {DEFAULT_BACKGROUND_SIZE}")

# ---------------- Utils ----------------
_slug_rx = re.compile(r"[^a-z0-9]+", re.I)

def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    return _slug_rx.sub("-", s).strip("-") or "char"

def _project_root() -> Path:
    # …/app/Agent/ -> sube 2 niveles hasta la raíz del proyecto
    return Path(__file__).resolve().parents[2]

def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

# ---------------- Core ----------------
@traceable(name="render_portrait_image")
def _render_one(spec: PortraitSpec, out_dir: Path, size: str | None = None) -> Path | None:
    """Genera 1 PNG y lo guarda en out_dir. Devuelve Path o None si falla."""
    size = size or DEFAULT_PORTRAIT_SIZE
    filename = _slugify(spec.name) + ".png"
    out_path = out_dir / filename

    # cache
    if out_path.exists():
        print(f"[image_renderer] cache hit: {out_path}")
        return out_path

    # Usar prompt especializado desde prompts_image_renderer
    prompts = PromptsImageRenderer()
    prompt = prompts.portrait_prompt(spec.prompt, spec.style)
    
    # Estimar tokens aproximados (1 token ≈ 0.75 palabras o 4 caracteres)
    estimated_tokens = len(prompt.split()) * 1.3  # Aproximación conservadora
    
    try:
        print(f"[image_renderer] generating: {spec.name} -> {out_path} (size={size})")
        print(f"[image_renderer] prompt ({estimated_tokens:.0f} tokens aprox): {prompt[:120]}...")  # Log del prompt
        
        provider = _get_image_provider()
        print(f"[image_renderer] provider type: {type(provider).__name__}")
        
        # Generar imagen usando el proveedor configurado
        # OpenAI acepta 'background', Stable Diffusion no
        from app.Agent.image_providers import OpenAIProvider
        if isinstance(provider, OpenAIProvider):
            # Es OpenAI
            print("[image_renderer] Using OpenAI provider")
            image = provider.generate_image(
                prompt=prompt,
                size=size,
                background="transparent"
            )
        else:
            # Es Stable Diffusion u otro
            print(f"[image_renderer] Using {type(provider).__name__} provider")
            image = provider.generate_image(
                prompt=prompt,
                size=size
            )
        
        if image is None:
            print(f"[image_renderer] ERROR: No se pudo generar la imagen")
            return None
        
        # Si es Stable Diffusion, hacer fondo transparente si es necesario
        if hasattr(provider, 'make_transparent_background'):
            # Solo para retratos, intentar hacer fondo transparente
            image = provider.make_transparent_background(image)
        
        # Guardar imagen
        image.save(out_path, "PNG")
        print(f"[image_renderer] saved: {out_path}")
        return out_path

    except Exception:
        print("[image_renderer] ERROR while generating image:")
        traceback.print_exc()
        return None

@traceable(name="render_portraits")
def render_portraits(briefs: List[PortraitSpec], max_workers: int = 3) -> Dict[str, str]:
    """
    Genera retratos para una lista de briefs.
    Devuelve dict {nombre: ruta_png} solo para los que se generaron correctamente.
    """
    print(f"[image_renderer] render_portraits called with {len(briefs)} briefs")
    
    # Ruta absoluta a partir de settings.PORTRAIT_DIR
    base = Path(settings.PORTRAIT_DIR or "portraits")
    out_dir = base if base.is_absolute() else (_project_root() / base)
    _ensure_dir(out_dir)
    print(f"[image_renderer] output dir: {out_dir}")
    print(f"[image_renderer] output dir exists: {out_dir.exists()}")

    results: Dict[str, str] = {}
    if not briefs:
        return results

    # Evita lanzar 2 renders para el mismo archivo (duplicados por nombre)
    seen_slugs: set[str] = set()
    filtered: List[PortraitSpec] = []
    for b in briefs:
        slug = _slugify(b.name)
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        filtered.append(b)

    size = DEFAULT_PORTRAIT_SIZE
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_render_one, b, out_dir, size): b for b in filtered}
        for fut in as_completed(futs):
            b = futs[fut]
            path = fut.result()
            if path:
                results[b.name] = str(path)
    return results

@traceable(name="generate_background_image")
def generate_background_image(background_brief: Dict[str, str]) -> str | None:
    """
    Genera una imagen de fondo basada en un brief.
    Devuelve la ruta del archivo generado o None si falla.
    """
    # Ruta para fondos generados
    base = Path(settings.BG_GEN_DIR or "app/UI/assets/images/background/generated")
    out_dir = base if base.is_absolute() else (_project_root() / base)
    _ensure_dir(out_dir)
    print(f"[image_renderer] background output dir: {out_dir}")

    # Crear nombre único para el fondo
    import time
    timestamp = int(time.time())
    filename = f"background_{timestamp}.png"
    out_path = out_dir / filename

    # Usar prompt especializado desde prompts_image_renderer
    prompts = PromptsImageRenderer()
    # Construir diccionario con la descripción combinada
    description = (
        f"Fondo épico para videojuego. "
        f"Escenario: {background_brief.get('setting', '')}. "
        f"Ambiente: {background_brief.get('mood', '')}. "
        f"Iluminación: {background_brief.get('lighting', '')}. "
        f"Elementos: {background_brief.get('elements', '')}. "
        f"Paleta: {background_brief.get('color_palette', '')}."
    )
    prompt = prompts.background_prompt({
        'description': description,
        'mood': background_brief.get('mood', ''),
        'style': background_brief.get('style', '')
    })

    try:
        print(f"[image_renderer] generating background: {out_path}")
        
        provider = _get_image_provider()
        
        # Generar imagen usando el proveedor configurado
        image = provider.generate_image(
            prompt=prompt,
            size=DEFAULT_BACKGROUND_SIZE
        )
        
        if image is None:
            print(f"[image_renderer] ERROR: No se pudo generar el fondo")
            return None
        
        # Guardar imagen
        image.save(out_path, "PNG")
        print(f"[image_renderer] background saved: {out_path}")
        return str(out_path)

    except Exception as e:
        print(f"[image_renderer] ERROR generating background: {e}")
        traceback.print_exc()
        return None

def attach_portraits_to_characters(characters: List[Character], name_to_path: Dict[str, str]) -> List[Character]:
    """
    Asocia portrait (o portrait_path) a cada Character usando nombre case-insensitive.
    """
    def norm(s: str) -> str:
        return (s or "").strip().lower()

    map_norm = {norm(k): v for k, v in name_to_path.items()}
    for ch in characters:
        p = map_norm.get(norm(ch.name))
        if p:
            # Asignar a portrait (campo principal) y también a portrait_path si existe
            ch.portrait = p
            if hasattr(ch, 'portrait_path'):
                ch.portrait_path = p
            print(f"[image_renderer] attach: {ch.name} -> {p}")
    return characters

