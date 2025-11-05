from .menu_scene import MenuScene
from .char_select_scene import CharSelectScene
from .intro_scene import IntroScene
from .vs_scene import VSScene
from .fight_scene import FightScene

SCENE_REGISTRY = {
    "show_principal_menu"           : MenuScene,
    "show_menu_select_character"    : CharSelectScene,
    "char_select"                   : CharSelectScene,
    "intro"                         : IntroScene,
    "vs"                            : VSScene,
    "fight"                         : FightScene,
}

def make_scene(name: str, app):
    return SCENE_REGISTRY[name](app)
