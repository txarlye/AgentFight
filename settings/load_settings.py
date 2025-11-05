import os,json
def load_config(path      = "config.json",
                objective = None): 
    if not os.path.exists(path):
        print("⚠️No se encontró config.json , usando valores por defecto.")
    with open (path, "r", encoding="utf-8") as f:
        return json.load(f).get(objective, {}) 