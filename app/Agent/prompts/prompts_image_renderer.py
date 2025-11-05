"""
Prompts especializados para el renderizado de imágenes.
Contiene los prompts para generar retratos y sprites con Stable Diffusion.
"""


class PromptsImageRenderer:
    """Prompts especializados para generación de imágenes con IA"""
    
    @staticmethod
    def portrait_prompt(spec_prompt: str, spec_style: str) -> str:
        """
        Construye el prompt final para generar un retrato con Stable Diffusion
        (Máximo 77 tokens para CLIP - muy optimizado)
        
        Args:
            spec_prompt: Prompt del brief generado por el director de arte
            spec_style: Estilo del brief generado por el director de arte
        
        Returns:
            str: Prompt completo para Stable Diffusion (máximo 77 tokens)
        """
        # Acortar el prompt del brief más agresivamente (máximo ~100 caracteres = ~15-20 tokens)
        max_brief_length = 100
        if len(spec_prompt) > max_brief_length:
            # Intentar cortar en un punto lógico (después de un punto, coma, o espacio)
            truncated = spec_prompt[:max_brief_length]
            last_period = truncated.rfind('.')
            last_comma = truncated.rfind(',')
            last_space = truncated.rfind(' ')
            
            # Usar el último punto, coma o espacio encontrado
            cut_point = max(last_period, last_comma, last_space)
            if cut_point > max_brief_length * 0.7:  # Solo si no es muy corto
                spec_prompt = truncated[:cut_point]
            else:
                spec_prompt = truncated
        
        # Acortar el estilo también (máximo 2-3 palabras clave)
        style_words = spec_style.split()[:3]  # Máximo 3 palabras
        style_short = ' '.join(style_words) if style_words else ''
        
        # Prompt optimizado para pixel art: brief + estilo corto + sufijo mejorado
        # Keywords específicas para pixel art que funcionan mejor con SD 2.1 (máximo 20 tokens)
        suffix = "8-bit pixel art, retro game sprite, fighting game character, transparent background, pixelated, clean lines"
        
        # Construir prompt final (máximo ~70 tokens)
        if style_short:
            prompt = f"{spec_prompt}, {style_short}. {suffix}"
        else:
            prompt = f"{spec_prompt}. {suffix}"
        
        return prompt
    
    @staticmethod
    def background_prompt(background_brief: dict) -> str:
        """
        Construye el prompt final para generar un fondo con Stable Diffusion
        
        Args:
            background_brief: Diccionario con el brief del fondo (description, mood, style)
        
        Returns:
            str: Prompt completo para Stable Diffusion
        """
        description = background_brief.get('description', '')
        mood = background_brief.get('mood', '')
        style = background_brief.get('style', '')
        
        return (
            f"{description}. "
            f"Mood: {mood}. "
            f"Estilo: {style}. "
            "8-bit pixel art, retro game background, fighting game arena, no characters, pixelated, atmospheric."
        )

