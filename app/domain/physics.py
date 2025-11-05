import pygame as pg
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class ActionState(Enum):
    IDLE        = "idle"
    WALKING     = "walking"
    RUNNING     = "running"
    JUMPING     = "jumping"
    ATTACKING   = "attacking"
    ATTACKING2  = "attacking2"
    ATTACKING3  = "attacking3"
    BLOCKING    = "blocking"
    HURT        = "hurt"
    DEAD        = "dead"

@dataclass
class PhysicsBody:
    """Representa el cuerpo físico de un personaje simplificado."""
    x: float = 0.0
    y: float = 0.0
    width: float = 64.0
    height: float = 128.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    on_ground: bool = True
    facing_right: bool = True
    
    # Constantes físicas simplificadas
    GRAVITY: float = 2.0     
    FRICTION: float = 0.9   
    MAX_SPEED: float = 10.0    
    JUMP_FORCE: float = -30.0  
    GROUND_Y: float = 500.0
    
    def update(self, dt: float = 1.0, screen_width: int = 800):
        """Actualiza la física del cuerpo de manera simplificada."""
        # Aplicar gravedad
        if not self.on_ground:
            self.velocity_y += self.GRAVITY
        
        # Aplicar fricción en el suelo
        if self.on_ground:
            self.velocity_x *= self.FRICTION
        
        # Limitar velocidad máxima
        self.velocity_x = max(-self.MAX_SPEED, min(self.MAX_SPEED, self.velocity_x))
        
        # Actualizar posición
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Colisión con el suelo
        if self.y >= self.GROUND_Y - self.height:
            self.y = self.GROUND_Y - self.height
            self.velocity_y = 0
            self.on_ground = True
        else:
            self.on_ground = False
        
        # Limitar en pantalla
        if self.x < 0:
            self.x = 0
            self.velocity_x = 0
        elif self.x + self.width > screen_width:
            self.x = screen_width - self.width
            self.velocity_x = 0
    
    def jump(self):
        """Hace que el personaje salte."""
        if self.on_ground:
            self.velocity_y = self.JUMP_FORCE
            self.on_ground = False
    
    def move_left(self, speed: float = 1.0):
        """Mueve el personaje hacia la izquierda."""
        self.velocity_x = -speed
        self.facing_right = False
    
    def move_right(self, speed: float = 1.0):
        """Mueve el personaje hacia la derecha."""
        self.velocity_x = speed
        self.facing_right = True
    
    def get_rect(self) -> pg.Rect:
        return pg.Rect(self.x, self.y, self.width, self.height)
    
    def get_center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    
class Hitbox:
    """Representa una zona de ataque o defensa."""
    
    def __init__(self, x: float, y: float, width: float, height: float, damage: int = 0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.damage = damage
        self.active = False
    
    def get_rect(self) -> pg.Rect:
        """Obtiene el rectángulo de la hitbox."""
        return pg.Rect(self.x, self.y, self.width, self.height)
    
    def collides_with(self, other: 'Hitbox') -> bool:
        """Verifica colisión con otra hitbox."""
        return self.get_rect().colliderect(other.get_rect())

class PhysicsEngine:
    """Motor de físicas simplificado."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.bodies: list[PhysicsBody] = []
        self.ground_level = screen_height - 100  # Nivel del suelo
    
    def add_body(self, body: PhysicsBody):
        """Añade un cuerpo físico al motor."""
        body.GROUND_Y = self.ground_level  # Actualizar nivel del suelo
        self.bodies.append(body)
    
    def update(self, dt: float = 1.0):
        """Actualiza toda la física."""
        for body in self.bodies:
            body.update(dt, self.screen_width)
    
    def get_collision_between_bodies(self, body1: PhysicsBody, body2: PhysicsBody) -> bool:
        return body1.get_rect().colliderect(body2.get_rect())
    
    def get_distance_between_bodies(self, body1: PhysicsBody, body2: PhysicsBody) -> float:
        """Calcula la distancia entre dos cuerpos (método necesario para la IA)."""
        center1 = body1.get_center()
        center2 = body2.get_center()
        return ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5
