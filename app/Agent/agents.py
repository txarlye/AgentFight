# agents.py
from dataclasses import dataclass
from typing import Dict, Any
import os, json
from settings.settings import settings
from app.Agent.Utils.provider_factory import ProviderFactory


@dataclass
class Agent:
    name: str = "Assistant"
    instructions: str = "You are a helpful assistant"
    model: str = None  # Se obtendrá del proveedor
    temperature: float = 0.7


@dataclass
class Result:
    final_output: str
    raw: object


@dataclass
class StructuredResult:
    arguments: Dict[str, Any]
    raw: object


class Runner:
    """
    Clase para ejecutar agentes usando el sistema de proveedores.
    Mantiene compatibilidad con la API anterior pero internamente usa proveedores.
    """
    
    _provider = None
    
    @staticmethod
    def _get_provider():
        """
        Obtiene el proveedor configurado (lazy initialization)
        
        Returns:
            BaseIAProvider: Proveedor configurado
        """
        if Runner._provider is None:
            Runner._provider = ProviderFactory.crear_provider(settings)
        return Runner._provider
    
    @staticmethod
    def run_sync(agent: Agent, prompt: str) -> Result:
        """
        Ejecuta un agente de forma síncrona
        
        Args:
            agent: Agente a ejecutar
            prompt: Prompt del usuario
        
        Returns:
            Result: Resultado con la respuesta generada
        """
        provider = Runner._get_provider()
        
        # Verificar límite antes de procesar
        if not provider.verificar_limite():
            raise RuntimeError("Límite de consumo de IA alcanzado")
        
        # Generar respuesta usando el proveedor
        system_prompt = agent.instructions
        resultado = provider.generate(
            system_prompt,
            prompt,
            temperature=agent.temperature
        )
        
        # Incrementar contador
        provider.incrementar_consumo()
        
        # Crear objeto Result compatible con la API anterior
        return Result(final_output=resultado, raw={"provider": provider.get_model_name()})
    
    @staticmethod
    def run_structured(
        agent: Agent,
        prompt: str,
        *,
        tool_name: str,
        parameters_schema: Dict[str, Any],
        tool_description: str = ""
    ) -> StructuredResult:
        """
        Fuerza al modelo a responder mediante una 'function call' con argumentos
        que cumplen el JSON Schema dado.
        
        Args:
            agent: Agente a ejecutar
            prompt: Prompt del usuario
            tool_name: Nombre de la función/tool
            parameters_schema: Esquema JSON de los parámetros
            tool_description: Descripción de la función
        
        Returns:
            StructuredResult: Resultado con argumentos parseados
        """
        provider = Runner._get_provider()
        
        # Verificar límite antes de procesar
        if not provider.verificar_limite():
            raise RuntimeError("Límite de consumo de IA alcanzado")
        
        # Generar respuesta estructurada usando el proveedor
        system_prompt = agent.instructions
        args = provider.generate_structured(
            system_prompt,
            prompt,
            tool_name,
            parameters_schema,
            tool_description,
            temperature=agent.temperature
        )
        
        # Incrementar contador
        provider.incrementar_consumo()
        
        # Crear objeto StructuredResult compatible con la API anterior
        return StructuredResult(arguments=args, raw={"provider": provider.get_model_name()})

# Diagnóstico rápido al importar (puedes borrar estas líneas si quieres)
if __name__ == "__main__":
    print("agents file:", __file__)
    print("Runner methods:", [m for m in dir(Runner) if not m.startswith("_")])
