import random
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum
from app.domain.physics import PhysicsBody, ActionState, Hitbox
from app.domain.character import Character

class AIState(Enum):
    IDLE = "idle"
    APPROACHING = "approaching"
    ATTACKING = "attacking"
    DEFENDING = "defending"
    RETREATING = "retreating"
    SPECIAL_ATTACK = "special_attack"

class EnemyAI:
    """
    Sistema de IA para enemigos que maneja comportamiento inteligente
    basado en el estado del combate y las características del enemigo.
    """
    
    def __init__(self, enemy: Character, physics_body: PhysicsBody):
        self.enemy = enemy
        self.body = physics_body
        self.state = AIState.IDLE
        self.target: Optional[PhysicsBody] = None
        self.last_decision_time = time.time()
        self.decision_cooldown = 0.5  # Segundos entre decisiones
        self.attack_cooldown = 0.0
        self.special_cooldown = 0.0
        
        # Personalidad del enemigo basada en sus stats
        self.aggressiveness = min(1.0, (enemy.damage + enemy.resistence) / 200.0)
        self.defensiveness = min(1.0, enemy.resistence / 100.0)
        self.intelligence = min(1.0, (enemy.damage + enemy.health) / 200.0)
        
        # Distancias de comportamiento
        self.attack_range = 80.0
        self.safe_distance = 120.0
        self.retreat_threshold = 0.3  # % de vida para retirarse
        
    def set_target(self, target: PhysicsBody):
        """Establece el objetivo de la IA."""
        self.target = target
    
    def update(self, dt: float, physics_engine) -> Dict[str, bool]:
        """
        Actualiza la IA y retorna las acciones a realizar.
        Retorna dict con acciones: {'attack': bool, 'block': bool, 'move_left': bool, etc.}
        """
        if not self.target:
            return self._idle_behavior()
        
        # Actualizar cooldowns
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.special_cooldown = max(0, self.special_cooldown - dt)
        
        # Tomar decisión cada cierto tiempo
        current_time = time.time()
        if current_time - self.last_decision_time > self.decision_cooldown:
            self._make_decision(physics_engine)
            self.last_decision_time = current_time
        
        # Ejecutar comportamiento actual
        return self._execute_current_state()
    
    def _make_decision(self, physics_engine):
        """Toma una decisión basada en el estado actual del combate."""
        if not self.target:
            return
        
        distance = physics_engine.get_distance_between_bodies(self.body, self.target)
        health_ratio = self.enemy.health / 100.0  # Asumiendo vida máxima de 100
        
        # Evaluar situación
        if health_ratio < self.retreat_threshold and random.random() < self.defensiveness:
            self.state = AIState.RETREATING
        elif distance <= self.attack_range and self.attack_cooldown <= 0:
            if random.random() < self.aggressiveness:
                self.state = AIState.ATTACKING
            else:
                self.state = AIState.DEFENDING
        elif distance > self.safe_distance:
            self.state = AIState.APPROACHING
        elif random.random() < 0.1:  # 10% chance de ataque especial
            self.state = AIState.SPECIAL_ATTACK
        else:
            self.state = AIState.IDLE
    
    def _execute_current_state(self) -> Dict[str, bool]:
        """Ejecuta el comportamiento del estado actual."""
        actions = {
            'attack': False,
            'block': False,
            'move_left': False,
            'move_right': False,
            'jump': False,
            'special': False
        }
        
        if not self.target:
            return actions
        
        distance = abs(self.body.x - self.target.x)
        
        if self.state == AIState.IDLE:
            # Comportamiento pasivo
            if random.random() < 0.1:
                actions['jump'] = True
        
        elif self.state == AIState.APPROACHING:
            # Acercarse al objetivo
            if self.body.x < self.target.x:
                actions['move_right'] = True
            else:
                actions['move_left'] = True
            
            # Saltar si hay obstáculo
            if random.random() < 0.05:
                actions['jump'] = True
        
        elif self.state == AIState.ATTACKING:
            # Atacar al objetivo
            if distance <= self.attack_range:
                actions['attack'] = True
                self.attack_cooldown = 1.0  # Cooldown de ataque
        
        elif self.state == AIState.DEFENDING:
            # Defender
            actions['block'] = True
            
            # Movimiento defensivo
            if random.random() < 0.3:
                if self.body.x < self.target.x:
                    actions['move_left'] = True
                else:
                    actions['move_right'] = True
        
        elif self.state == AIState.RETREATING:
            # Retirarse del combate
            if self.body.x < self.target.x:
                actions['move_left'] = True
            else:
                actions['move_right'] = True
            
            # Saltar para evadir
            if random.random() < 0.2:
                actions['jump'] = True
        
        elif self.state == AIState.SPECIAL_ATTACK:
            # Ataque especial
            if self.special_cooldown <= 0:
                actions['special'] = True
                self.special_cooldown = 5.0  # Cooldown largo para especial
        
        return actions
    
    def _idle_behavior(self) -> Dict[str, bool]:
        """Comportamiento cuando no hay objetivo."""
        return {
            'attack': False,
            'block': False,
            'move_left': False,
            'move_right': False,
            'jump': False,
            'special': False
        }
    
    def take_damage(self, damage: int):
        """Se llama cuando el enemigo recibe daño."""
        self.enemy.health = max(0, self.enemy.health - damage)
        
        # Reaccionar al daño
        if damage > 10:  # Daño significativo
            self.state = AIState.DEFENDING
            self.last_decision_time = time.time() - self.decision_cooldown  # Forzar nueva decisión
    
    def get_attack_hitbox(self) -> Optional[Hitbox]:
        """Crea una hitbox de ataque basada en el estado actual."""
        if self.state != AIState.ATTACKING:
            return None
        
        # Posición de la hitbox según la dirección
        if self.body.facing_right:
            hitbox_x = self.body.x + self.body.width
        else:
            hitbox_x = self.body.x - 40
        
        hitbox_y = self.body.y + 50  # Aproximadamente a la altura del pecho
        
        # Daño basado en el daño del enemigo
        damage = int(self.enemy.damage * 0.8)  # 80% del daño como daño base
        
        hitbox = Hitbox(hitbox_x, hitbox_y, 40, 60, damage)
        hitbox.active = True
        
        return hitbox

class AIDifficulty:
    """Configuración de dificultad para la IA."""
    
    EASY = {
        'decision_cooldown': 1.0,
        'attack_cooldown_multiplier': 1.5,
        'aggressiveness_multiplier': 0.7,
        'intelligence_multiplier': 0.6
    }
    
    NORMAL = {
        'decision_cooldown': 0.5,
        'attack_cooldown_multiplier': 1.0,
        'aggressiveness_multiplier': 1.0,
        'intelligence_multiplier': 1.0
    }
    
    HARD = {
        'decision_cooldown': 0.3,
        'attack_cooldown_multiplier': 0.7,
        'aggressiveness_multiplier': 1.3,
        'intelligence_multiplier': 1.4
    }

def create_enemy_ai(enemy: Character, physics_body: PhysicsBody, difficulty: str = "NORMAL") -> EnemyAI:
    """Crea una instancia de IA para un enemigo con la dificultad especificada."""
    ai = EnemyAI(enemy, physics_body)
    
    # Aplicar configuración de dificultad
    config = getattr(AIDifficulty, difficulty.upper(), AIDifficulty.NORMAL)
    
    ai.decision_cooldown *= config['decision_cooldown']
    ai.aggressiveness *= config['aggressiveness_multiplier']
    ai.intelligence *= config['intelligence_multiplier']
    
    return ai
