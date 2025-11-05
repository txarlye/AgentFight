import pygame as pg
from settings.settings  import settings
from app.UI.scenes      import make_scene
from app.Agent.orchestrator import get_orchestrator 

class PygameApp:
    def __init__(self):
        pg.init()
        self.screen  = pg.display.set_mode((settings.WIDTH, settings.HEIGHT))
        pg.display.set_caption(settings.TITLE)
        self.clock   = pg.time.Clock()
        self.running = True
        self.scene   = None
        
        # Inicializar el orchestrator
        self.orchestrator = get_orchestrator(self)
 
        self.set_scene(settings.UI_first_selected_menu)

    def set_scene(self, scene_name: str):
        if self.scene and hasattr(self.scene, "exit"):
            self.scene.exit()
        try:
            self.scene = make_scene(scene_name, self)
        except KeyError:
            self.scene = make_scene("show_principal_menu", self)

        settings.UI_selected_menu = scene_name
        if hasattr(self.scene, "enter"):
            self.scene.enter()

    def run(self):
        while self.running:
            dt = self.clock.tick(settings.DF) / 1000.0
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(e)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pg.display.flip()
        pg.quit()
