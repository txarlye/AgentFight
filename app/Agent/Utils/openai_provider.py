"""
Proveedor de IA usando OpenAI.
Implementa BaseIAProvider para OpenAI.
"""

import os
import json
from typing import Dict, Any
from openai import OpenAI
from .base_provider import BaseIAProvider
from .langsmith_config import setup_langsmith

# Configurar LangSmith al importar
setup_langsmith()


class OpenAIProvider(BaseIAProvider):
    """Proveedor de IA usando OpenAI"""
    
    def __init__(self, settings):
        """
        Inicializar proveedor OpenAI
        
        Args:
            settings: Objeto de configuración
        """
        super().__init__(settings)
        
        # Obtener configuración de OpenAI
        ai_config = getattr(settings, 'AI_PROVIDER_CONFIG', {})
        openai_config = ai_config.get('openai', {})
        
        # API key desde variable de entorno o settings
        api_key_env = openai_config.get('api_key_env', 'OPENAI_API_KEY')
        api_key = os.getenv(api_key_env) or getattr(settings, 'OPENAI_API_KEY', None)
        
        if not api_key:
            raise ValueError(f"{api_key_env} not found. Check your .env file.")
        if not api_key.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = openai_config.get('model', os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    
    def generate(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        **kwargs
    ) -> str:
        """
        Generar respuesta usando OpenAI
        
        Args:
            system_prompt: Prompt del sistema
            user_prompt: Prompt del usuario
            **kwargs: Parámetros adicionales (temperature, max_tokens, etc.)
        
        Returns:
            str: Respuesta generada
        """
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', None)
        
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        content = resp.choices[0].message.content or ""
        return content
    
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
        Generar respuesta estructurada usando function calling de OpenAI
        
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
        temperature = kwargs.get('temperature', 0.7)
        
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_description or "Return structured fields.",
                    "parameters": parameters_schema,
                },
            }],
            tool_choice={"type": "function", "function": {"name": tool_name}},
        )
        
        msg = resp.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None) or []
        selected = None
        
        for tc in tool_calls:
            if getattr(tc, "type", None) == "function" and tc.function.name == tool_name:
                selected = tc
                break
        
        if not selected:
            raise RuntimeError("No tool call returned by the model.")
        
        try:
            args_text = selected.function.arguments or "{}"
            args = json.loads(args_text)
            if not isinstance(args, dict):
                raise ValueError("Parsed arguments are not a JSON object.")
        except Exception as e:
            raise RuntimeError(f"Failed to parse tool arguments: {e}")
        
        return args

