"""
Proveedor de IA usando Ollama.
Implementa BaseIAProvider para Ollama (local).
"""

import os
import json
import random
import requests
from typing import Dict, Any
from .base_provider import BaseIAProvider
from .langsmith_config import setup_langsmith

# Configurar LangSmith al importar
setup_langsmith()


class OllamaProvider(BaseIAProvider):
    """Proveedor de IA usando Ollama"""
    
    def __init__(self, settings):
        """
        Inicializar proveedor Ollama
        
        Args:
            settings: Objeto de configuración
        """
        super().__init__(settings)
        
        # Obtener configuración de Ollama
        ai_config = getattr(settings, 'AI_PROVIDER_CONFIG', {})
        ollama_config = ai_config.get('ollama', {})
        
        self.base_url = ollama_config.get('base_url', 'http://localhost:11434')
        self.model = ollama_config.get('model', 'llama3.1')
        self.timeout = ollama_config.get('timeout', 240)  # Timeout por defecto: 240s
        self.temperature_default = ollama_config.get('temperature', 0.3)
        self.num_predict_default = ollama_config.get('num_predict', 500)
    
    def generate(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        **kwargs
    ) -> str:
        """
        Generar respuesta usando Ollama
        
        Args:
            system_prompt: Prompt del sistema
            user_prompt: Prompt del usuario
            **kwargs: Parámetros adicionales
        
        Returns:
            str: Respuesta generada
        """
        # Usar /api/generate que es más compatible con todas las versiones de Ollama
        url = f"{self.base_url}/api/generate"
        
        # ⚠️ IMPORTANTE: Estructura correcta del payload según textoagentes.md
        # Combinar system y user prompt en un solo prompt
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Obtener parámetros con valores por defecto (desde configuración o kwargs)
        temperature = kwargs.get('temperature', self.temperature_default)
        max_tokens = kwargs.get('max_tokens', self.num_predict_default)
        timeout = self.timeout
        
        # Generar seed aleatorio para variabilidad (si no se proporciona uno)
        seed = kwargs.get('seed', random.randint(-2147483648, 2147483647))
        
        # ⚠️ CRÍTICO: Las opciones van dentro de "options"
        # Usar num_predict en lugar de max_tokens
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,  # ✅ Siempre False para agentes (no streaming)
            "options": {  # ⚠️ CRÍTICO: Las opciones van dentro de "options"
                "temperature": temperature,
                "num_predict": max_tokens,  # ✅ Usar num_predict, NO max_tokens
                "seed": seed,  # ✅ Seed aleatorio para variabilidad
            }
        }
        
        # Añadir otras opciones de kwargs si existen
        for key, value in kwargs.items():
            if key not in ['temperature', 'max_tokens', 'seed']:
                payload['options'][key] = value
        
        try:
            # ✅ Añadir timeout a la petición
            response = requests.post(url, json=payload, timeout=timeout)
            
            # ✅ Manejo específico de errores HTTP 500 (memoria insuficiente)
            if response.status_code == 500:
                try:
                    error_detail = response.json().get('error', response.text)
                except:
                    error_detail = response.text
                
                if 'unable to allocate' in error_detail.lower() or 'allocate CPU buffer' in error_detail.lower():
                    raise RuntimeError(
                        f"Ollama no puede cargar el modelo '{self.model}'. "
                        f"Error: {error_detail}. "
                        f"Solución: Usa un modelo más pequeño (ej: llama3.1:8b) o aumenta la RAM disponible."
                    )
                else:
                    raise RuntimeError(f"Error en Ollama API (HTTP 500): {error_detail}")
            
            response.raise_for_status()
            result = response.json()
            
            # Ollama devuelve la respuesta en result["response"]
            return result.get("response", "").strip()
                
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Timeout esperando respuesta de Ollama (>{timeout}s). "
                             f"El modelo '{self.model}' puede ser demasiado lento. "
                             f"Considera usar un modelo más pequeño o aumentar el timeout.")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"No se puede conectar a Ollama en {self.base_url}. "
                             f"Asegúrate de que Ollama está corriendo.")
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            if hasattr(e.response, 'text'):
                try:
                    error_detail = f" - {e.response.json().get('error', e.response.text)}"
                except:
                    error_detail = f" - {e.response.text}"
            raise RuntimeError(f"Error calling Ollama API (HTTP {e.response.status_code}){error_detail}")
        except RuntimeError:
            # Re-lanzar RuntimeError sin modificar
            raise
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error calling Ollama API: {e}")
    
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        tool_name: str,
        parameters_schema: Dict[str, Any],
        tool_description: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generar respuesta estructurada usando Ollama.
        
        Nota: Ollama puede no soportar function calling nativo como OpenAI.
        Esta implementación intenta forzar el formato JSON mediante prompts.
        
        Args:
            system_prompt: Prompt del sistema
            user_prompt: Prompt del usuario
            tool_name: Nombre de la función/tool
            parameters_schema: Esquema JSON de los parámetros
            tool_description: Descripción de la función
            **kwargs: Parámetros adicionales
        
        Returns:
            Dict: Argumentos parseados de la función
        """
        # Extraer información del esquema de forma más clara
        properties = parameters_schema.get('properties', {})
        required = parameters_schema.get('required', [])
        
        # Construir descripción más clara del formato esperado
        schema_desc = []
        for key, value in properties.items():
            prop_type = value.get('type', 'string')
            is_required = key in required
            
            # Detectar si es array
            if prop_type == 'array':
                items = value.get('items', {})
                items_type = items.get('type', 'object')
                min_items = value.get('minItems', 0)
                max_items = value.get('maxItems', 'infinito')
                
                # Si es array de objetos, mostrar propiedades de cada objeto
                if items_type == 'object' and 'properties' in items:
                    item_props = items.get('properties', {})
                    item_required = items.get('required', [])
                    prop_details = []
                    for prop_key, prop_value in item_props.items():
                        prop_req = prop_key in item_required
                        prop_details.append(f"    - {prop_key}: {prop_value.get('type', 'string')}{' (REQUERIDO)' if prop_req else ' (opcional)'}")
                    schema_desc.append(f"- {key}: array de objetos (mínimo {min_items}, máximo {max_items}){'(REQUERIDO)' if is_required else '(opcional)'}")
                    schema_desc.extend(prop_details)
                else:
                    schema_desc.append(f"- {key}: array de {items_type} (mínimo {min_items}, máximo {max_items}){'(REQUERIDO)' if is_required else '(opcional)'}")
            else:
                req_mark = " (REQUERIDO)" if is_required else " (opcional)"
                schema_desc.append(f"- {key}: {prop_type}{req_mark}")
        
        schema_text = "\n".join(schema_desc)
        
        # Construir prompt que fuerza formato JSON
        enhanced_system = f"""{system_prompt}

IMPORTANTE: Debes responder SOLO con un objeto JSON válido (sin texto adicional, sin explicaciones, sin markdown).

Formato esperado:
{schema_text}

NO devuelvas el esquema, devuelve los DATOS reales basados en el prompt del usuario."""
        
        enhanced_user = f"""{user_prompt}

Responde ÚNICAMENTE con un objeto JSON válido (sin texto, sin explicaciones, sin markdown)."""
        
        # Generar respuesta
        response_text = self.generate(enhanced_system, enhanced_user, **kwargs)
        
        # Log para debugging
        print(f"[OllamaProvider] Respuesta recibida (primeros 200 chars): {response_text[:200]}")
        
        # Intentar extraer JSON de la respuesta
        try:
            # Buscar JSON en la respuesta (puede haber texto adicional)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                print(f"[OllamaProvider] JSON extraído (primeros 300 chars): {json_text[:300]}")
                args = json.loads(json_text)
                
                if not isinstance(args, dict):
                    raise ValueError("Parsed arguments are not a JSON object.")
                
                # Verificar que no devolvió el esquema
                if 'type' in args and 'properties' in args and 'required' in args:
                    print("[OllamaProvider] ⚠️ ADVERTENCIA: La respuesta parece ser el esquema, no los datos")
                    print(f"[OllamaProvider] Keys en respuesta: {list(args.keys())}")
                
                print(f"[OllamaProvider] ✅ JSON parseado correctamente. Keys: {list(args.keys())}")
                return args
            else:
                raise ValueError(f"No JSON object found in response. Response length: {len(response_text)}")
        except json.JSONDecodeError as e:
            print(f"[OllamaProvider] ❌ Error parseando JSON: {e}")
            print(f"[OllamaProvider] Respuesta completa: {response_text}")
            raise RuntimeError(f"Failed to parse tool arguments from Ollama response: {e}. Response: {response_text[:500]}")
        except Exception as e:
            print(f"[OllamaProvider] ❌ Error inesperado: {e}")
            print(f"[OllamaProvider] Respuesta completa: {response_text}")
            raise RuntimeError(f"Failed to parse tool arguments from Ollama response: {e}. Response: {response_text[:500]}")

