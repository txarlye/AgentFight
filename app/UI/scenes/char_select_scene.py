import re, threading, random
from pathlib import Path
import pygame as pg
# from app.game.orchestrator        import orchestrator
from app.UI.scenes.base_scene     import BaseScene
from app.domain.character         import Character
from settings.settings            import settings
from app.UI.pg_assets             import load_background_cached, draw_background, draw_photo_frame
from app.Agent.agent_art_director import create_portrait_briefs
from app.Agent.image_renderer     import render_portraits
 
try:
    from app.Agent.agent_character_creator import create_candidates
    from app.Agent.agent_sprite_director import create_character_sprite_set
    from app.Agent.agent_sprite_generator import generate_character_sprite_set
except Exception:
    create_candidates = None
    create_character_sprite_set = None
    generate_character_sprite_set = None
 
# ---------------- fallbacks ----------------
def _fake_candidates(n=4):
    names = ["Kumo", "Raven", "Sable", "Lyra", "Orion", "Vex", "Tara", "Jin"]
    weap = ["nunchaku", "hacha", "katana", "dagas", "bastón", "guantes"]
    out = []
    
    # Rutas locales relativas al directorio del proyecto
    local_portraits = [
        "app/UI/assets/test/portraits/maligno-tit-n.png",
        "app/UI/assets/test/portraits/sombra-del-terror.png",
        "app/UI/assets/test/portraits/tit-n-de-acero.png"
    ]
    
    for i in range(n):
        out.append(Character(
            name        = random.choice(names) + f"_{random.randint(1,99)}",
            damage      = random.randint(3, 9),
            resistence  = random.randint(2, 8),
            weapon      = random.choice(weap),
            description = "Combatiente placeholder.",
            portrait    = local_portraits[i % len(local_portraits)],  # Ruta relativa
        ))
    return out
 
_slug_rx = re.compile(r"[^a-z0-9]+", re.I)

def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    return _slug_rx.sub("-", s).strip("-") or "char"
 
class CharSelectScene(BaseScene):
    """
    - Carga candidatos y lanza la generación de retratos en background.
    - Cada marco intenta cargar su PNG si ya existe en disco (no esperamos a todos).
    - Navegación: ←/→ o A/D; selección con ENTER/SPACE o teclas 1..4.
    """
    def __init__(self, app):
        super().__init__(app)
        self.bg = load_background_cached(settings.BG_SELECT, 
                                         (settings.WIDTH, settings.HEIGHT)) 
        self.candidates : list[Character] = []
        self._img_cache : dict[str, pg.Surface | None] = {}
        self._thread    : threading.Thread | None = None
        self.generating : bool = False
        self.cursor     : int = 0

        # Marcos (4 slots)
        margin_x    = 60
        gap_x       = 40
        frame_w     = (settings.WIDTH - margin_x*2 - gap_x*3) // 4
        frame_h     = 190
        y           = 140
        self.frames = [pg.Rect(margin_x + i*(frame_w+gap_x), y, frame_w, frame_h) for i in range(4)]

        # Carpeta de retratos (ruta absoluta desde cwd)
        if settings.use_existing_assets or settings.use_local_characters_for_test:
            # Si estamos en modo test o usando assets existentes, usar directorio de assets locales
            self.portrait_dir = Path("app/UI/assets/test/portraits")
        else:
            # Si no, usar el directorio de retratos generados
            self.portrait_dir = Path(settings.PORTRAIT_DIR or "portraits").resolve()
    # ---------- helpers de texto ----------
    def _wrap_exact(self, font, text: str, max_w: int, max_lines: int, tail_ellipsis: bool):
        words = text.split()
        lines = []
        cur = ""
        used_all = True
        i = 0
        while i < len(words):
            w = words[i]
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_w:
                cur = test
                i += 1
            else:
                if cur:
                    lines.append(cur); cur = ""
                else:
                    cut = w
                    while cut and font.size(cut)[0] > max_w:
                        cut = cut[:-1]
                    lines.append(cut)
                    words[i] = w[len(cut):]
                    if not words[i]:
                        i += 1
                if len(lines) == max_lines:
                    used_all = False
                    break
        if cur and len(lines) < max_lines:
            lines.append(cur)
        if not used_all and tail_ellipsis and lines:
            last = lines[-1]
            while last and font.size(last + "…")[0] > max_w:
                last = last[:-1]
            lines[-1] = (last + "…") if last else "…"
        return lines, used_all

    def _name_lines_and_font(self, text: str, max_w: int):
        for size in range(22, 13, -1):
            f = pg.font.SysFont(settings.FONT_NAME, size, bold=True)
            lines, ok = self._wrap_exact(f, text, max_w, max_lines=2, tail_ellipsis=False)
            if ok:
                return f, lines
        f = pg.font.SysFont(settings.FONT_NAME, 14, bold=True)
        lines, _ = self._wrap_exact(f, text, max_w, max_lines=2, tail_ellipsis=True)
        return f, lines

    # ---------------- lifecycle ----------------
    def enter(self):
        if getattr(settings, "Player_locked", False):
            self.app.set_scene("show_principal_menu")
            return

        self.cursor     = 0
        self.candidates = []
        self._img_cache.clear()
        self.generating = True

        def loader():
            # 1) Candidatos
            if settings.use_local_enemy_for_test or create_candidates is None:
                cand = _fake_candidates(4)
            else:
                try:
                    cand = create_candidates(4)
                except Exception as e:
                    print(f"Error creando candidatos de IA: {e}")
                    cand = _fake_candidates(4)

            # 2) Rutas de retrato - Solo asignar imágenes locales si use_existing_assets está activo
            # Si NO usamos assets existentes, NO asignar imágenes todavía (se generarán después)
            for ch in cand:
                if settings.use_existing_assets:
                    # Si usamos assets existentes, asignar imágenes locales (fallback)
                    local_portraits = [
                        "app/UI/assets/test/portraits/maligno-tit-n.png",
                        "app/UI/assets/test/portraits/sombra-del-terror.png",
                        "app/UI/assets/test/portraits/tit-n-de-acero.png"
                    ]
                    # Usar el índice del candidato para asignar imagen
                    portrait_index = cand.index(ch) % len(local_portraits)
                    ch.portrait = local_portraits[portrait_index]
                else:
                    # Si NO usamos assets existentes, asignar path basado en nombre (se generará después)
                    # NO asignar imágenes de test para evitar que se muestren antes de generar
                    slug = _slugify(ch.name)
                    ch.portrait = str(self.portrait_dir / f"{slug}.png")

            # 3) Generar imágenes ANTES de publicar candidatos (para que se usen las nuevas)
            if not settings.use_existing_assets:
                try: 
                    print("[CharSelectScene] Generando retratos con IA...")
                    from app.Agent.agent_art_director import create_portrait_briefs
                    from app.Agent.image_renderer import render_portraits, attach_portraits_to_characters
                    briefs = create_portrait_briefs(cand)
                    print(f"[CharSelectScene] Briefs creados: {len(briefs)} personajes")
                    name_to_path = render_portraits(briefs, max_workers=3)
                    print(f"[CharSelectScene] Retratos generados: {len(name_to_path)} imágenes")
                    # Asociar los retratos generados a los personajes
                    if name_to_path:
                        attach_portraits_to_characters(cand, name_to_path)
                        print(f"[CharSelectScene] Retratos asociados a personajes")
                    else:
                        print("[CharSelectScene] ⚠️ No se generaron retratos, usando imágenes por defecto")
                        # Si no se generaron imágenes, usar fallback
                        local_portraits = [
                            "app/UI/assets/test/portraits/maligno-tit-n.png",
                            "app/UI/assets/test/portraits/sombra-del-terror.png",
                            "app/UI/assets/test/portraits/tit-n-de-acero.png"
                        ]
                        for i, ch in enumerate(cand):
                            ch.portrait = local_portraits[i % len(local_portraits)]
                except Exception as e:
                    print(f"[CharSelectScene] Error generating portraits: {e}")
                    import traceback
                    traceback.print_exc()
                    # En caso de error, usar fallback
                    local_portraits = [
                        "app/UI/assets/test/portraits/maligno-tit-n.png",
                        "app/UI/assets/test/portraits/sombra-del-terror.png",
                        "app/UI/assets/test/portraits/tit-n-de-acero.png"
                    ]
                    for i, ch in enumerate(cand):
                        ch.portrait = local_portraits[i % len(local_portraits)]

            # 4) Publicar candidatos DESPUÉS de generar imágenes (para que usen las nuevas)
            self.candidates = cand 

            self.generating = False 
        
        self._thread = threading.Thread(target=loader, daemon=True)
        self._thread.start()

    def handle_event(self, e):
        if e.type == pg.KEYDOWN:
            if e.key in (pg.K_0, pg.K_ESCAPE):
                self.app.set_scene("show_principal_menu")
            elif e.key in (pg.K_LEFT, pg.K_a):
                self.cursor = max(0, self.cursor - 1)
            elif e.key in (pg.K_RIGHT, pg.K_d):
                self.cursor = min(len(self.frames) - 1, self.cursor + 1)
            elif e.key in (pg.K_RETURN, pg.K_SPACE):
                self._select_by_index(self.cursor)
            elif e.key == pg.K_9:
                self.enter()
            elif e.key in (pg.K_1, pg.K_2, pg.K_3, pg.K_4):
                idx = e.key - pg.K_1
                self._select_by_index(idx)

    def _select_by_index(self, idx: int):
        if getattr(settings, "Player_locked", False):
            return
        if 0 <= idx < len(self.candidates):
            elegido = self.candidates[idx]
            settings.Player_selected_Player = elegido
            settings.Player_locked = True
            
            # Usar el orchestrator para manejar la selección
            if hasattr(self.app, 'orchestrator'):
                self.app.orchestrator.set_player(elegido)
                self.app.orchestrator.add_choice(elegido.name, "character_selection")
                self.app.orchestrator.go_to_menu()
            
            # Iniciar generación de sprites en background
            if generate_character_sprite_set and settings.generate_character_sprites:
                def generate_sprites():
                    try:
                        print(f"CharSelect: Iniciando generación de sprites para {elegido.name}")
                        
                        # Crear directorio para sprites del personaje
                        sprite_dir = Path("app/UI/assets/images/sprites") / _slugify(elegido.name)
                        sprite_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Generar conjunto completo de sprites
                        sprite_paths = generate_character_sprite_set(
                            character=elegido,
                            output_dir=sprite_dir,
                            sprite_types=["idle", "walk", "attack", "block", "hurt", "jump"]
                        )
                        
                        # Guardar rutas de sprites en el personaje
                        elegido.sprite_paths = sprite_paths
                        
                        print(f"CharSelect: Sprites generados para {elegido.name}: {len(sprite_paths)} sprites")
                        
                    except Exception as e:
                        print(f"CharSelect: Error generando sprites - {e}")
                
                sprite_thread = threading.Thread(target=generate_sprites, daemon=True)
                sprite_thread.start()
            
            # Iniciar generación de historia personalizada en background
            def generate_story():
                try:
                    print(f"CharSelect: Iniciando generación de historia personalizada para {elegido.name}")
                    from app.Agent.agent_story_weaver import create_introduction_story
                    from app.Agent.agent_background_director import create_story_background_brief
                    
                    # Generar historia personalizada
                    story_data = create_introduction_story(elegido)
                    
                    # Generar brief de fondo si está habilitado
                    background_brief = {}
                    if settings.generate_backgrounds:
                        try:
                            background_brief = create_story_background_brief(story_data, elegido)
                            print(f"CharSelect: Brief de fondo generado para {elegido.name}")
                        except Exception as e:
                            print(f"CharSelect: Error generando brief de fondo - {e}")
                    
                    # Guardar en el orchestrator para uso posterior
                    if hasattr(self.app, 'orchestrator'):
                        self.app.orchestrator.story_context["prefetched_story"] = story_data
                        self.app.orchestrator.story_context["prefetched_background_brief"] = background_brief
                        self.app.orchestrator.story_context["story_generated"] = True
                    
                    print(f"CharSelect: Historia personalizada generada para {elegido.name}")
                except Exception as e:
                    print(f"CharSelect: Error generando historia personalizada - {e}")
            
            story_thread = threading.Thread(target=generate_story, daemon=True)
            story_thread.start()
            
            # Ir al menú principal
            self.app.set_scene("show_principal_menu")

    # ---------------- draw helpers ----------------
    def _portrait_surface(self, ch: Character, rect: pg.Rect) -> pg.Surface | None:
        """Carga y cachea el retrato si el archivo YA existe. No dibuja aquí."""
        if settings.use_existing_assets or settings.use_local_characters_for_test:
            # En modo test, usar el path directo del character
            path = getattr(ch, "portrait", None)
        else:
            # En modo normal, construir path desde portrait_dir
            slug = _slugify(ch.name)
            path = str(self.portrait_dir / f"{slug}.png")
        
        
        if not path:
            return None
        key = path

        cached = self._img_cache.get(key)
        if isinstance(cached, pg.Surface):
            return cached

        p = Path(path)
        if not p.exists():
            return None

        try:
            img = pg.image.load(str(p)).convert_alpha()
            pad = 12
            w = rect.width - pad*2
            h = rect.height - pad*2
            img = pg.transform.smoothscale(img, (w, h))
            self._img_cache[key] = img
            return img
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            self._img_cache[key] = None
            return None


    def _draw_frame(self, screen, rect: pg.Rect, selected: bool):
        draw_photo_frame(screen, rect)
        if selected:
            pg.draw.rect(screen, (255, 255, 255), rect.inflate(6, 6), width=3, border_radius=12)

    def _loading_text(self) -> str:
        t = pg.time.get_ticks() // 400
        return "Loading" + "." * (t % 4)

    # ---------------- draw ----------------
    def draw(self, screen):
        draw_background(screen, self.bg, (25,25,32))

        # Título con tamaño específico (sin depender de BaseScene.text)
        # title_font = pg.font.SysFont(settings.FONT_NAME, 26, bold=True)
        # title = "[Selecciona tu personaje]  (←/→ o A/D para mover, ENTER/SPACE para elegir, 9 regenerar, 0 volver)"
        # screen.blit(title_font.render(title, True, (240,240,240)), (40, 60))
        
        self.text(
            screen,
            """[Selecciona tu personaje]  
            ←/→  A/D para mover, ENTER/SPACE para elegir,
            9 regenerar, 0 volver)""",
            (40, 60),
            size=18, bold=False  
        )


        stat_font = pg.font.SysFont(settings.FONT_NAME, 18)
        desc_font = pg.font.SysFont(settings.FONT_NAME, 16)
        loading_msg = self._loading_text()

        for i, rect in enumerate(self.frames):
            x = rect.x
            max_w = rect.width
            name_top = rect.bottom + 8

            # marco + resalte si es el cursor
            self._draw_frame(screen, rect, selected=(i == self.cursor))

            # Si aún no hay candidatos suficientes:
            if i >= len(self.candidates):
                msg = loading_msg if self.generating else "—"
                ph = self.font.render(msg, True, (210,210,210))
                screen.blit(ph, (rect.centerx - ph.get_width()//2, rect.centery - ph.get_height()//2))
                continue

            ch = self.candidates[i]

            # retrato (si el archivo ya existe)
            surf = self._portrait_surface(ch, rect)
            if surf is not None:
                pad = 12
                screen.blit(surf, (rect.x + pad, rect.y + pad))
            else:
                ph = self.font.render(loading_msg, True, (210,210,210))
                screen.blit(ph, (rect.centerx - ph.get_width()//2, rect.centery - ph.get_height()//2))

            # 1) Nombre (hasta 2 líneas)
            name_font, name_lines = self._name_lines_and_font(f"[{i+1}] {ch.name}", max_w)
            y = name_top
            for ln in name_lines:
                screen.blit(name_font.render(ln, True, (240,240,240)), (x, y))
                y += name_font.get_linesize()

            # 2) Stats
            for ln in (f"Damage {ch.damage}", f"Resistencia {ch.resistence}"):
                screen.blit(stat_font.render(ln, True, (210,210,210)), (x, y))
                y += stat_font.get_linesize()
            
            # 3) Rareza
            rarity = ch.get_rarity_description()
            rarity_color = (255, 215, 0) if rarity in ["Legendario", "Épico"] else (210, 210, 210)
            screen.blit(stat_font.render(f"Rareza: {rarity}", True, rarity_color), (x, y))
            y += stat_font.get_linesize()

            # 4) Weapon (2 líneas máx)
            weapon_lines, _ = self._wrap_exact(stat_font, f"Weapon: {ch.weapon}", max_w, max_lines=2, tail_ellipsis=True)
            for ln in weapon_lines:
                screen.blit(stat_font.render(ln, True, (210,210,210)), (x, y))
                y += stat_font.get_linesize()

            # 5) Descripción (hasta 6 líneas)
            desc_lines, _ = self._wrap_exact(desc_font, ch.description, max_w, max_lines=6, tail_ellipsis=True)
            y += 4
            for ln in desc_lines:
                screen.blit(desc_font.render(ln, True, (180,180,180)), (x, y))
                y += desc_font.get_linesize()
