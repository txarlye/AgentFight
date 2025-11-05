"""
Prompts especializados para el agente creador de personajes.
Contiene los prompts para crear enemigos y personajes.
"""


class PromptsCharacterCreator:
    """Prompts especializados para creación de personajes"""
    
    @staticmethod
    def sistema():
        """
        Obtiene las instrucciones del sistema para el agente
        
        Returns:
            str: Prompt del sistema con instrucciones generales
        """
        return """Eres un creador de enemigos para un juego 1v1. 
Respondes SOLO con campos estructurados en español."""
    
    @staticmethod
    def create_character(banned_norm_names: list = None):
        """
        Construye el prompt para crear un enemigo
        
        Args:
            banned_norm_names: Lista de nombres normalizados a evitar
        
        Returns:
            str: Prompt completo para el usuario
        """
        banned_list = ", ".join(sorted(banned_norm_names)) if banned_norm_names else "—"
        
        return f"""Crea un enemigo y devuelve SOLO los campos estructurados. 
Evita cualquier nombre cuya forma normalizada (sin acentos y en minúsculas) 
coincida con alguno de esta lista: [{banned_list}]. 
Varía arma/atributos respecto a los ya usados."""
    
    @staticmethod
    def create_candidates(n: int):
        """
        Construye el prompt para crear múltiples enemigos
        
        Args:
            n: Número de enemigos a crear
        
        Returns:
            str: Prompt completo para el usuario
        """
        return f"""Devuelve EXACTAMENTE {n} enemigos en el array 'candidates'. 
TODOS deben tener nombres distintos (comparados sin acentos y en minúsculas) 
Los nombres pueden ser inventados y compuestos, dar miedo o provocar risa
y cierta variedad en arma/atributos."""

