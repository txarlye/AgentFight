# app/domain/fight_pack.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from app.domain.character import Character

@dataclass
class BackgroundBrief:
    biome: str
    time: str
    mood: str
    palette: List[str]
    visual_hooks: List[str]
    composition: str
    ref_path: Optional[str] = None
    floor_y_norm: float = 0.82
    walk_band_norm: Tuple[float, float] = (0.76, 0.86)

@dataclass
class StoryBeat:
    pre_fight_lines: List[str]
    intro_paragraph: str
    taunts: List[str]
    victory_blurb: str
    defeat_blurb: str
    conflict_motive: str
    arc_state_delta: Dict[str, object] = field(default_factory=dict)

@dataclass
class FightPack:
    enemy: Character
    enemy_portrait_path: Optional[str]
    background_path: Optional[str]
    background_meta: Optional[BackgroundBrief]
    story: Optional[StoryBeat]
    attack_profile: Dict[str, object] = field(default_factory=dict)
    # Por si quieres transportar algo del jugador
    player_portrait_path: Optional[str] = None
