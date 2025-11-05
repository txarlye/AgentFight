import os
import base64
import traceback
import threading
from typing import Optional, Tuple
from pathlib import Path
from PIL import Image
import numpy as np
from dotenv import load_dotenv
from settings.settings import settings

# Intentar importar LangSmith para trazabilidad de generación de imágenes
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    # LangSmith no está instalado, crear decorador dummy
    def traceable(name=None):
        def decorator(func):
            return func
        return decorator
    LANGSMITH_AVAILABLE = False

load_dotenv()

# ============= STABLE DIFFUSION PROVIDER =============
class StableDiffusionProvider:
    """Proveedor de imágenes usando Stable Diffusion local"""
    
    _pipeline = None
    _model_name = None
    _lock = threading.Lock()  # Lock para sincronizar carga del pipeline
    
    def __init__(self):
        self.model_name = settings.STABLE_DIFFUSION_MODEL
        self.steps = settings.STABLE_DIFFUSION_STEPS
        
    def _get_pipeline(self):
        """Carga el pipeline de Stable Diffusion (lazy loading) - Thread-safe"""
        # Verificar primero sin lock (fast path)
        if self._pipeline is not None and self._model_name == self.model_name:
            return self._pipeline
        
        # Si necesitamos cargar, usar lock para evitar cargas concurrentes
        with self._lock:
            # Verificar de nuevo dentro del lock (double-check pattern)
            if self._pipeline is not None and self._model_name == self.model_name:
                return self._pipeline
            
            # Cargar el pipeline
            try:
                import torch
                import diffusers
                
                # Intentar importar los pipelines disponibles de forma robusta
                StableDiffusionPipeline = None
                StableDiffusionXLPipeline = None
                
                # Intentar importar StableDiffusionPipeline (el estándar)
                try:
                    StableDiffusionPipeline = getattr(diffusers, 'StableDiffusionPipeline', None)
                    if StableDiffusionPipeline is None:
                        from diffusers import StableDiffusionPipeline
                    print("[StableDiffusion] StableDiffusionPipeline disponible")
                except (ImportError, AttributeError) as e:
                    print(f"[StableDiffusion] ⚠️ No se pudo importar StableDiffusionPipeline: {e}")
                    # Intentar importar usando importlib como fallback
                    try:
                        import importlib
                        diffusers_module = importlib.import_module('diffusers')
                        StableDiffusionPipeline = getattr(diffusers_module, 'StableDiffusionPipeline', None)
                        if StableDiffusionPipeline is None:
                            raise ImportError("StableDiffusionPipeline no está disponible en diffusers")
                    except Exception as e2:
                        raise ImportError(
                            f"diffusers no tiene StableDiffusionPipeline disponible. "
                            f"Error: {e2}. "
                            f"Verifica que diffusers esté correctamente instalado: uv pip install diffusers"
                        )
                
                # Intentar importar StableDiffusionXLPipeline si está disponible
                try:
                    StableDiffusionXLPipeline = getattr(diffusers, 'StableDiffusionXLPipeline', None)
                    if StableDiffusionXLPipeline is None:
                        from diffusers import StableDiffusionXLPipeline
                    print("[StableDiffusion] StableDiffusionXLPipeline disponible")
                except (ImportError, AttributeError):
                    print("[StableDiffusion] StableDiffusionXLPipeline no disponible, usando StableDiffusionPipeline")
                    StableDiffusionXLPipeline = None
                
                if StableDiffusionPipeline is None:
                    raise ImportError("StableDiffusionPipeline no está disponible")
                
                print(f"[StableDiffusion] Cargando modelo: {self.model_name}")
                
                # Intentar usar SDXL solo si está disponible y el modelo es SDXL
                use_sdxl = False
                if StableDiffusionXLPipeline is not None:
                    if "xl" in self.model_name.lower() or "sdxl" in self.model_name.lower():
                        try:
                            print("[StableDiffusion] Intentando cargar con StableDiffusionXLPipeline...")
                            self._pipeline = StableDiffusionXLPipeline.from_pretrained(
                                self.model_name,
                                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                                use_safetensors=True,
                                variant="fp16" if torch.cuda.is_available() else None,
                                safety_checker=None,  # Desactivar safety checker (muy estricto)
                                requires_safety_checker=False
                            )
                            # Desactivar safety checker también después de cargar
                            self._pipeline.safety_checker = None
                            self._pipeline.feature_extractor = None
                            use_sdxl = True
                            print("[StableDiffusion] Modelo cargado con StableDiffusionXLPipeline (safety_checker desactivado)")
                        except Exception as e:
                            print(f"[StableDiffusion] ⚠️ No se pudo cargar con StableDiffusionXLPipeline: {e}")
                            print("[StableDiffusion] Intentando con StableDiffusionPipeline como fallback...")
                            use_sdxl = False
                
                # Si no se usó SDXL, usar el pipeline estándar
                if not use_sdxl:
                    self._pipeline = StableDiffusionPipeline.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                        use_safetensors=True,
                        variant="fp16" if torch.cuda.is_available() else None,
                        safety_checker=None,  # Desactivar safety checker (muy estricto)
                        requires_safety_checker=False
                    )
                    # Desactivar safety checker también después de cargar
                    self._pipeline.safety_checker = None
                    self._pipeline.feature_extractor = None
                    print("[StableDiffusion] Modelo cargado con StableDiffusionPipeline (safety_checker desactivado)")
                
                if torch.cuda.is_available():
                    self._pipeline = self._pipeline.to("cuda")
                    print(f"[StableDiffusion] Modelo cargado en GPU")
                else:
                    print(f"[StableDiffusion] Modelo cargado en CPU")
                
                self._model_name = self.model_name
                
            except ImportError as e:
                error_msg = str(e)
                if "transformers" in error_msg.lower():
                    raise ImportError(
                        "transformers no está instalado. "
                        "Ejecuta: uv pip install transformers"
                    )
                elif "diffusers" in error_msg.lower() or "StableDiffusion" in error_msg:
                    raise ImportError(
                        f"Error importando diffusers: {error_msg}. "
                        f"Ejecuta: uv pip install --upgrade diffusers torch torchvision accelerate transformers"
                    )
                else:
                    raise ImportError(
                        f"diffusers, torch o transformers no están instalados. "
                        f"Error: {error_msg}. "
                        f"Ejecuta: uv pip install diffusers torch torchvision accelerate transformers"
                    )
            except Exception as e:
                print(f"[StableDiffusion] Error cargando modelo: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        return self._pipeline
    
    @traceable(name="stable_diffusion_generate_image")
    def generate_image(
        self,
        prompt: str,
        size: str = "512x512",
        negative_prompt: Optional[str] = None
    ) -> Optional[Image.Image]:
        """Genera una imagen usando Stable Diffusion - Rastreado en LangSmith"""
        try:
            pipeline = self._get_pipeline()
            
            # Parsear tamaño
            width, height = self._parse_size(size)
            
            # Prompt negativo optimizado para pixel art
            if negative_prompt is None:
                negative_prompt = "blurry, low quality, distorted, text, watermark, photorealistic, 3d render, smooth gradients, realistic textures, high resolution, detailed shading"
            
            # Validar número de steps (algunos schedulers tienen límites)
            # SDXL Turbo funciona mejor con 10-20 steps para EulerAncestralDiscrete
            # El scheduler EulerAncestralDiscrete tiene problemas con menos de 10 steps
            if "turbo" in self.model_name.lower():
                num_steps = min(self.steps, 20)  # Máximo 20 steps para Turbo
                num_steps = max(num_steps, 10)   # Mínimo 10 steps para Turbo (evita errores de scheduler)
            else:
                num_steps = min(self.steps, 50)  # Máximo 50 steps para otros modelos
                num_steps = max(num_steps, 10)   # Mínimo 10 steps para otros modelos
            
            print(f"[StableDiffusion] Generando imagen: {width}x{height}, steps={num_steps}")
            
            # Generar imagen (desactivar safety_checker en la llamada también)
            result = pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_steps,
                guidance_scale=2.0 if "turbo" in self.model_name.lower() else (7.5 if "xl" not in self.model_name.lower() else 9.0),
            )
            
            # Asegurar que no hay safety_checker activo
            if hasattr(result, 'images') and len(result.images) > 0:
                image = result.images[0]
            else:
                # Fallback si el resultado tiene estructura diferente
                image = result[0] if isinstance(result, (list, tuple)) else result
            
            return image
            
        except Exception as e:
            print(f"[StableDiffusion] Error generando imagen: {e}")
            traceback.print_exc()
            return None
    
    def _parse_size(self, size: str) -> Tuple[int, int]:
        """Convierte string '512x512' a tupla (512, 512)"""
        try:
            parts = size.split('x')
            return (int(parts[0]), int(parts[1]))
        except:
            return (512, 512)
    
    def make_transparent_background(self, image: Image.Image) -> Image.Image:
        """Hace el fondo transparente (blanco/negro -> transparente)"""
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        data = np.array(image)
        r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
        
        # Detectar fondo blanco o muy claro
        white_areas = (r > 240) & (g > 240) & (b > 240)
        # Detectar fondo negro o muy oscuro
        black_areas = (r < 15) & (g < 15) & (b < 15)
        
        # Hacer transparente
        a[white_areas] = 0
        a[black_areas] = 0
        
        return Image.fromarray(data)


# ============= OPENAI PROVIDER =============
class OpenAIProvider:
    """Proveedor de imágenes usando OpenAI API"""
    
    def __init__(self):
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY no encontrada en .env")
            self._client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai no está instalado. Ejecuta: pip install openai")
    
    @traceable(name="openai_generate_image")
    def generate_image(
        self,
        prompt: str,
        size: str = "512x512",
        background: Optional[str] = None
    ) -> Optional[Image.Image]:
        """Genera una imagen usando OpenAI - Rastreado en LangSmith"""
        try:
            # Intentar con background transparente
            try:
                resp = self._client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    size=size,
                    background="transparent" if background else None,
                )
            except TypeError:
                resp = self._client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    size=size,
                )
            
            b64 = resp.data[0].b64_json
            image_bytes = base64.b64decode(b64)
            
            from io import BytesIO
            image = Image.open(BytesIO(image_bytes))
            return image
            
        except Exception as e:
            print(f"[OpenAI] Error generando imagen: {e}")
            traceback.print_exc()
            return None


# ============= FACTORY =============
def get_image_provider():
    """Factory que devuelve el proveedor configurado"""
    provider_name = getattr(settings, 'IMAGE_PROVIDER', 'stable_diffusion')
    
    if provider_name == 'openai':
        try:
            return OpenAIProvider()
        except Exception as e:
            print(f"[ImageProvider] Error inicializando OpenAI: {e}")
            if settings.USE_OPENAI_FALLBACK:
                print("[ImageProvider] Fallback a Stable Diffusion...")
                return StableDiffusionProvider()
            raise
    
    # Por defecto: Stable Diffusion
    return StableDiffusionProvider()

