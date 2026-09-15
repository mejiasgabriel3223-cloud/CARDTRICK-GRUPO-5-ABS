import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "menu"


class GestorConfig:
    @staticmethod
    def _default_config():
        return {
            "card_skin": "dark",
            "recursos": {
                "fondo": "assets/fondo_menu.png",
                "fondo_menu": "assets/fondo_menu.png",
                "fondo_juego": "assets/fondo_menu.png",
                "titulo": "",
                "video": "assets/fondo_menu.mp4",
            },
            "estilos": {
                "fuente_titulo_tamano": 82,
                "fuente_opcion_tamano": 46,
                "fuente_instruccion_tamano": 26,
                "color_titulo": [255, 255, 255],
                "color_instruccion": [220, 220, 220],
                "color_texto_input": [255, 220, 100],
                "color_fondo": [15, 25, 45],
            },
            "opciones_principal": [
                {"texto": "JUGAR", "accion": "JUGAR"},
                {"texto": "CONFIG", "accion": "PANTALLA_CONFIGURACION"},
                {"texto": "CREDITOS", "accion": "PANTALLA_TEXTO", "contenido": ["Creditos"]},
                {"texto": "SALIR", "accion": "SALIR"},
            ],
        }

    @staticmethod
    def resolver_ruta(ruta):
        if not ruta:
            return ""

        ruta_path = Path(str(ruta).replace("\\", "/"))
        if ruta_path.is_absolute():
            return str(ruta_path)

        return str((BASE_DIR / ruta_path).resolve())

    @staticmethod
    def cargar_configuracion():
        ruta_json = CONFIG_DIR / "menu_config.json"
        if not ruta_json.exists():
            return GestorConfig._default_config()
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return GestorConfig._default_config()
            config = GestorConfig._default_config()
            config.update(data)
            if isinstance(data.get("recursos"), dict):
                config["recursos"].update(data["recursos"])
            if isinstance(data.get("estilos"), dict):
                config["estilos"].update(data["estilos"])
            return config
        except Exception as e:
            print(f"Error cargando {ruta_json}: {e}")
            return GestorConfig._default_config()

    @staticmethod
    def guardar_configuracion(config):
        ruta_json = CONFIG_DIR / "menu_config.json"
        try:
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    @staticmethod
    def obtener_fondo_menu():
        config = GestorConfig.cargar_configuracion()
        recursos = config.get("recursos", {}) if isinstance(config.get("recursos", {}), dict) else {}
        for clave in ("fondo_menu", "fondo", "background_menu"):
            valor = recursos.get(clave)
            if valor:
                return GestorConfig.resolver_ruta(valor)
        return GestorConfig.resolver_ruta(config.get("fondo_menu") or config.get("fondo") or "")

    @staticmethod
    def obtener_fondo_juego():
        config = GestorConfig.cargar_configuracion()
        recursos = config.get("recursos", {}) if isinstance(config.get("recursos", {}), dict) else {}
        for clave in ("fondo_juego", "background_game", "fondo", "background"):
            valor = recursos.get(clave)
            if valor:
                return GestorConfig.resolver_ruta(valor)
        return GestorConfig.resolver_ruta(config.get("fondo_juego") or "")

    @staticmethod
    def obtener_skin_activa():
        config = GestorConfig.cargar_configuracion()
        skin = str(config.get("card_skin", "dark")).strip().lower()
        if skin in {"dark", "negra", "black", "oscura"}:
            return "dark"
        if skin in {"light", "blanca", "white", "clara"}:
            return "light"
        return "dark"

    @staticmethod
    def cambiar_skin(nueva_skin):
        config = GestorConfig.cargar_configuracion()
        valor = str(nueva_skin).strip().lower()
        config["card_skin"] = "dark" if valor in {"dark", "negra", "black", "oscura"} else "light"
        return GestorConfig.guardar_configuracion(config)
