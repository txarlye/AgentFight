from dataclasses import dataclass

@dataclass
class Character:
    name        : str
    damage      : int                
    resistence  : int           
    weapon      : str
    description : str
    
    portrait    : str
    health      : int = 100    # base
    
    def summary(self) -> str:
        return f"{self.name}  dmg:{self.damage} def:{self.resistence}  arma:{self.weapon}"
    
    def get_name(self)  -> str:
        return self.name
    
    def take_damage(self, amount: int) -> int:
        eff = max(1, int(amount) - self.resistence)
        self.health = max(0, self.health - eff)
        return eff

    def is_alive(self) -> bool:
        return self.health > 0
    
    def compute_rarity(self) -> int:
        """
        Calcula la rareza del personaje basada en sus estadísticas.
        Rango: 1-100, donde 100 es extremadamente raro.
        """
        import random
        
        # Base de rareza basada en stats
        total_stats = self.damage + self.resistence
        base_rarity = (total_stats / 20.0) * 100.0  # Máximo 20 stats = 100 rareza
        
        # Añadir variabilidad aleatoria
        random_factor = random.randint(-15, 15)
        
        # Asegurar que esté en el rango 1-100
        rarity = max(1, min(100, round(base_rarity + random_factor)))
        
        return rarity
    
    def get_rarity_description(self) -> str:
        """Obtiene una descripción de la rareza del personaje"""
        # Usar rareza cacheada si existe, sino calcularla una vez
        if not hasattr(self, '_cached_rarity'):
            self._cached_rarity = self.compute_rarity()
        
        rarity = self._cached_rarity
        
        if rarity >= 90:
            return "Legendario"
        elif rarity >= 75:
            return "Épico"
        elif rarity >= 60:
            return "Raro"
        elif rarity >= 40:
            return "Común"
        else:
            return "Básico"
    
    
enemy_schema = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "nombre":      {"type": "string",  "minLength": 1},
        "danio":       {"type": "integer", "minimum": 1, "maximum": 10},
        "resistencia": {"type": "integer", "minimum": 1, "maximum": 10},
        "arma":        {"type": "string",  "minLength": 1},
        "descripcion": {"type": "string",  "minLength": 1},
    },
    "required": ["nombre", "danio", "resistencia", "arma", "descripcion"],
}