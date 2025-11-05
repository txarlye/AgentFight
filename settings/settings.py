import json,datetime,re
from typing                 import Optional
from settings.load_settings import load_config
from app.domain.character   import Character

class Settings:
    
    _instance = None  
    
    def __new__(cls,*args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance 
    
    def __init__(self,config_path):
        if hasattr(self,"_initialized") and self._initialized:
            return 
        self._initialized = True
        self.load_configuration(config_path)
        
    def load_configuration(self, path):
        # Configurations
        config_UI       = load_config(path,"UI")
        config_Player   = load_config(path,"Player")
        config_Debug    = load_config(path,"Debug")
        config_ImageGen = load_config(path,"ImageGeneration")
        config_Controls = load_config(path,"Controls")
        config_AIProvider = load_config(path,"AIProvider")
        
        # UI Settings:  
        self.WIDTH                  = config_UI.get("WIDTH")
        self.HEIGHT                 = config_UI.get("HEIGHT")
        self.FONT_NAME              = config_UI.get("FONT_NAME")
        self.DF                     = config_UI.get("DF")
        self.TITLE                  = config_UI.get("TITLE")
        self.BG_MENU                = config_UI.get("BG_MENU")
        self.BG_SELECT              = config_UI.get("BG_SELECT")
        self.BG_FIGHT_DIR           = config_UI.get("BG_FIGHT_DIR")
        self.BG_GEN_DIR             = config_UI.get("BG_GEN_DIR")
        self.BG_SEED_PATH           = config_UI.get("BG_SEED_PATH")
        self.PORTRAIT_DIR           = config_UI.get("PORTRAIT_DIR")
        self.PORTRAIT_SIZE          = config_UI.get("PORTRAIT_SIZE")
        
        # Image Generation Settings
        self.IMAGE_PROVIDER = config_ImageGen.get("provider", "stable_diffusion")
        self.STABLE_DIFFUSION_MODEL = config_ImageGen.get("stable_diffusion_model", "stabilityai/sdxl-turbo")
        self.STABLE_DIFFUSION_STEPS = config_ImageGen.get("stable_diffusion_steps", 4)
        self.USE_OPENAI_FALLBACK = config_ImageGen.get("use_openai_fallback", False)
        self.CHARACTER_SPRITE_SIZE  = config_ImageGen.get("character_sprite_size", "256x256")
        self.BACKGROUND_SIZE        = config_ImageGen.get("background_size", "512x512")
        self.PORTRAIT_SIZE_GEN      = config_ImageGen.get("portrait_size", "512x512")
        self.MAX_DAILY_GENERATIONS  = config_ImageGen.get("max_daily_generations", 50)
        self.BACKGROUND_CACHE_ENABLED = config_ImageGen.get("background_cache_enabled", True)
        self.SPRITE_CACHE_ENABLED   = config_ImageGen.get("sprite_cache_enabled", True)
        
        # Debug Settings
        self.use_local_characters_for_test  = config_Debug.get("use_local_characters_for_test")
        self.use_local_enemy_for_test       = config_Debug.get("use_local_enemy_for_test")
        self.generate_backgrounds           = config_Debug.get("generate_backgrounds")
        self.generate_character_sprites     = config_Debug.get("generate_character_sprites")
        self.generate_history               = config_Debug.get("generate_history")
        self.debug_fight_mode               = config_Debug.get("debug_fight_mode")
        self.use_existing_assets            = config_Debug.get("use_existing_assets")
        
        # Controls Settings
        self.MOVE_LEFT                      = config_Controls.get("move_left", "A")
        self.MOVE_RIGHT                     = config_Controls.get("move_right", "D")
        self.MOVE_UP                        = config_Controls.get("move_up", "W")
        self.MOVE_DOWN                      = config_Controls.get("move_down", "S")
        self.ATTACK1                        = config_Controls.get("attack1", "SPACE")
        self.ATTACK2                        = config_Controls.get("attack2", "Q")
        self.ATTACK3                        = config_Controls.get("attack3", "E")
        self.JUMP                           = config_Controls.get("jump", "W")
        self.BLOCK                          = config_Controls.get("block", "S")
        
        # AI Provider Settings
        self.AI_PROVIDER_CONFIG = config_AIProvider or {
            "provider": "openai",
            "openai": {
                "model": "gpt-4o-mini",
                "api_key_env": "OPENAI_API_KEY"
            },
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "llama3.1",
                "api_key_env": None
            }
        }
        self.AI_PROVIDER = self.AI_PROVIDER_CONFIG.get("provider", "openai")
         
        self.Player_selected_Player: Optional[Character] = None
        self.UI_first_selected_menu = config_UI.get("first_selected_menu")
        self.UI_selected_menu       = config_UI.get("selected_menu")
        
        #
        self.activated              = True
        self.Player_locked          = False
        
    @property
    def selected_player_name(self) -> str:
        ch = self.Player_selected_Player
        return ch.name.strip() if ch and getattr(ch, "name", "").strip() else "elige personaje"  
        
settings = Settings("settings/settings.json")

       

