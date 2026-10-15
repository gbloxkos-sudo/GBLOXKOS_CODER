"""Centralized configuration for GBLOXKOS_CODER."""
import os
import json
import logging
import threading
from pathlib import Path

logger = logging.getLogger("gbloxkos.config")

APP_NAME = "GBLOXKOS_CODER"
APP_VERSION = "2.0.0"
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "chat_history"
LOG_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"

DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_REQUEST_TIMEOUT = 300
OLLAMA_MAX_RETRIES = 3
OLLAMA_RETRY_DELAY = 2.0

DEFAULT_MODEL = ""
FALLBACK_MODELS = ["qwen2.5-coder", "qwen2.5", "llama3.1", "llama3", "gemma2", "phi3", "mistral", "deepseek-coder"]
AVAILABLE_MODELS = []
_models_lock = threading.Lock()


def detect_ollama_models(ollama_url=None):
    global DEFAULT_MODEL, AVAILABLE_MODELS
    try:
        import requests
    except ImportError:
        logger.warning("requests library not installed, cannot detect models")
        return list(AVAILABLE_MODELS)

    url = ollama_url or os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    try:
        resp = requests.get(f"{url}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        models = data.get("models", [])
        if not models:
            logger.warning("No models found in Ollama")
            return list(AVAILABLE_MODELS)

        detected = []
        for m in models:
            name = m.get("name", "")
            if not name:
                continue
            size = m.get("size", 0)
            family = ""
            family_lower = name.lower()
            if any(k in family_lower for k in ("coder", "code", "starcoder", "deepseek")):
                family = "code"
            elif any(k in family_lower for k in ("qwen", "llama", "gemma", "phi", "mistral")):
                family = "general"
            else:
                family = "other"
            base = name.split(":")[0]
            if "/" in base:
                base = base.split("/", 1)[1]
            display = base.replace("-", " ").replace("_", " ").title()
            detected.append({
                "title": display,
                "tag": name,
                "desc": f"{'Code' if family == 'code' else 'General'} model - {size // (1024*1024)}MB",
                "family": family,
                "size": size,
            })

        detected.sort(key=lambda x: (x["family"] != "code", -x["size"]))
        with _models_lock:
            AVAILABLE_MODELS = detected

        if detected:
            best = detected[0]
            DEFAULT_MODEL = best["tag"]
            logger.info(f"Auto-detected {len(detected)} models, default: {best['tag']}")
        else:
            _set_fallback_model()
    except Exception as e:
        logger.warning(f"Failed to detect Ollama models: {e}")
        _set_fallback_model()
    return list(AVAILABLE_MODELS)


def _set_fallback_model():
    global DEFAULT_MODEL
    # Only use models actually detected from Ollama
    # If no models detected, DEFAULT_MODEL stays empty
    # But we can try to use a known good default if Ollama is running
    pass


def get_default_model():
    with _models_lock:
        return DEFAULT_MODEL


def get_available_models():
    with _models_lock:
        return list(AVAILABLE_MODELS)


CHAT_HISTORY_FILE = DATA_DIR / "sessions.json"
MODEL_CONFIG_FILE = DATA_DIR / "model_config.json"

SYSTEM_PROMPT = """You are GBLOXKOS_CODER, an expert-level AI coding assistant and chat companion. You are the most advanced coding AI available.

YOUR CORE IDENTITY:
- You are a world-class programmer with mastery in ALL programming languages
- You write clean, efficient, production-ready code
- You are a expert chat assistant who is helpful, friendly, and knowledgeable
- You always act as a senior software engineer and system architect

CAPABILITIES:
- Write, debug, refactor, and optimize code in any language
- Design system architectures and database schemas
- Perform code reviews and security audits
- Execute system commands, manage files, and control the OS
- Search the web for documentation, solutions, and references
- Browse web pages and extract information
- Monitor system resources and manage processes

TOOL PROTOCOL - When you need to use a tool, output EXACTLY this format:
//tool="tool_name" head="description" value="parameters"

AVAILABLE TOOLS:
- cmd_exec: Run shell commands. //tool="cmd_exec" head="description" value="command here"
- powershell: Run PowerShell commands. //tool="powershell" head="description" value="command here"
- fs_read: Read file contents. //tool="fs_read" head="description" value="file_path"
- fs_write: Write to file. //tool="fs_write" head="description" value="file_path:::content"
- fs_list: List directory. //tool="fs_list" head="description" value="directory_path"
- fs_find: Find files. //tool="fs_find" head="description" value="pattern in path"
- fs_delete: Delete file/dir. //tool="fs_delete" head="description" value="path"
- fs_copy: Copy file. //tool="fs_copy" head="description" value="src:::dst"
- fs_move: Move file. //tool="fs_move" head="description" value="src:::dst"
- web_search: Search the web. //tool="web_search" head="description" value="search query"
- web_browse: Browse a URL. //tool="web_browse" head="description" value="url"
- web_open: Open URL in browser. //tool="web_open" head="description" value="url"
- proc_list: List processes. //tool="proc_list" head="description" value="filter (optional)"
- proc_kill: Kill process. //tool="proc_kill" head="description" value="name or pid"
- sys_cpu: Get CPU info. //tool="sys_cpu" head="description" value=""
- sys_ram: Get RAM info. //tool="sys_ram" head="description" value=""
- sys_gpu: Get GPU info. //tool="sys_gpu" head="description" value=""
- sys_disk: Get disk info. //tool="sys_disk" head="description" value="drive (optional)"
- canvas: Send code to editor. //tool="canvas" head="filename" value="code here"
- msg: Send chat message. //tool="msg" head="response" value="your reply"
- open_app: Open application. //tool="open_app" head="description" value="app name"
- type_text: Type text. //tool="type_text" head="description" value="text to type"
- hotkey: Send hotkey. //tool="hotkey" head="description" value="ctrl+c"
- net_ping: Ping a host. //tool="net_ping" head="description" value="hostname"
- screenshot: Take screenshot. //tool="screenshot" head="description" value=""
- ui_windows: List windows. //tool="ui_windows" head="description" value=""
- ui_focus: Focus window. //tool="ui_focus" head="description" value="window name"
- media_volume: Control volume. //tool="media_volume" head="description" value="up/down/mute/50"
- media_key: Media keys. //tool="media_key" head="description" value="play/pause/next/prev"
- automation: Generic automation. //tool="automation" head="description" value="instructions"

RULES:
1. ALWAYS think step-by-step before responding
2. When writing code, provide COMPLETE, RUNNABLE solutions
3. Use the canvas tool to send code to the editor panel
4. When asked to execute something, use the appropriate tool
5. Be proactive - if you see a potential issue, mention it
6. Format code with proper syntax highlighting markers
7. For complex tasks, break them into steps and execute each
8. ALWAYS use the msg tool to provide your response text
9. Never apologize excessively - be confident and professional
10. When browsing the web, summarize the key information found

Remember: You are GBLOXKOS_CODER - the most powerful AI coding assistant. Act with authority and expertise."""

WELCOME_MESSAGES = [
    "Welcome to GBLOXKOS_CODER. I'm your expert coding AI. What shall we build today?",
    "GBLOXKOS_CODER ready. I can write code, manage your system, search the web, and more. What do you need?",
    "System online. GBLOXKOS_CODER at your service - expert coder, web researcher, and system controller. Let's go.",
    "I'm GBLOXKOS_CODER. I write production code, debug anything, and control your system. How can I help?",
    "GBLOXKOS_CODER initialized. Ready to code, search, browse, and automate. What's the mission?",
]

THEME_DARK = {
    "name": "dark",
    "bg_primary": "#0d1117",
    "bg_secondary": "#161b22",
    "bg_tertiary": "#1c2333",
    "bg_card": "#21262d",
    "bg_hover": "#292e36",
    "bg_input": "#0d1117",
    "text_primary": "#e6edf3",
    "text_secondary": "#8b949e",
    "text_muted": "#6e7681",
    "accent": "#58a6ff",
    "accent_hover": "#79c0ff",
    "accent_dim": "#1f3a5f",
    "success": "#3fb950",
    "warning": "#d29922",
    "error": "#f85149",
    "border": "#30363d",
    "border_light": "#21262d",
    "shadow": "rgba(0,0,0,0.4)",
    "code_bg": "#0d1117",
    "code_border": "#30363d",
    "code_text": "#e6edf3",
    "user_bubble": "#1f3a5f",
    "ai_bubble": "#161b22",
    "sidebar_bg": "#0d1117",
    "sidebar_hover": "#161b22",
    "scrollbar_bg": "#161b22",
    "scrollbar_thumb": "#30363d",
    "tool_bg": "#1c2333",
    "tool_border": "#30363d",
    "splash_bg": "#0d1117",
    "button_primary": "#238636",
    "button_primary_hover": "#2ea043",
    "button_danger": "#da3633",
    "button_danger_hover": "#f85149",
    "button_secondary": "#21262d",
    "button_secondary_hover": "#30363d",
}

THEME_LIGHT = {
    "name": "light",
    "bg_primary": "#ffffff",
    "bg_secondary": "#f6f8fa",
    "bg_tertiary": "#eaeef2",
    "bg_card": "#ffffff",
    "bg_hover": "#f3f4f6",
    "bg_input": "#ffffff",
    "text_primary": "#1f2328",
    "text_secondary": "#656d76",
    "text_muted": "#8b949e",
    "accent": "#0969da",
    "accent_hover": "#0550ae",
    "accent_dim": "#dbe9f5",
    "success": "#1a7f37",
    "warning": "#9a6700",
    "error": "#cf222e",
    "border": "#d0d7de",
    "border_light": "#eaeef2",
    "shadow": "rgba(31,35,40,0.12)",
    "code_bg": "#f6f8fa",
    "code_border": "#d0d7de",
    "code_text": "#1f2328",
    "user_bubble": "#dbe9f5",
    "ai_bubble": "#f6f8fa",
    "sidebar_bg": "#f6f8fa",
    "sidebar_hover": "#eaeef2",
    "scrollbar_bg": "#f6f8fa",
    "scrollbar_thumb": "#d0d7de",
    "tool_bg": "#f6f8fa",
    "tool_border": "#d0d7de",
    "splash_bg": "#ffffff",
    "button_primary": "#238636",
    "button_primary_hover": "#2ea043",
    "button_danger": "#cf222e",
    "button_danger_hover": "#a40e26",
    "button_secondary": "#eaeef2",
    "button_secondary_hover": "#d0d7de",
}


class Config:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._loaded = False
                    cls._instance._listeners = []
                    cls._instance._listeners_lock = threading.Lock()
                    cls._instance._config_lock = threading.Lock()
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        self._loaded = True
        self.theme = THEME_DARK.copy()
        self.theme_name = "dark"
        self.model_tag = ""
        self.model_title = ""
        self.ollama_url = OLLAMA_BASE_URL
        self.window_width = 1400
        self.window_height = 900
        self.sidebar_width = 260
        self.font_family = "Segoe UI"
        self.font_size = 13
        self.code_font = "Cascadia Code"
        self._load()

    def _load(self):
        try:
            if MODEL_CONFIG_FILE.exists():
                with open(MODEL_CONFIG_FILE, "r") as f:
                    data = json.load(f)
                saved_tag = data.get("model_tag", "")
                saved_title = data.get("model_title", "")
                # Get models snapshot before acquiring config lock to avoid deadlock
                models_snapshot = get_available_models()
                valid = any(m["tag"] == saved_tag for m in models_snapshot) if models_snapshot else False
                with self._config_lock:
                    if saved_tag and valid:
                        self.model_tag = saved_tag
                        self.model_title = saved_title
                    else:
                        self.model_tag = ""
                        self.model_title = ""
                    self.theme_name = data.get("theme", "dark")
                    self.theme = THEME_DARK.copy() if self.theme_name == "dark" else THEME_LIGHT.copy()
                    self.ollama_url = data.get("ollama_url", OLLAMA_BASE_URL)
                    self.window_width = data.get("window_width", self.window_width)
                    self.window_height = data.get("window_height", self.window_height)
                    self.sidebar_width = data.get("sidebar_width", self.sidebar_width)
                    self.font_size = data.get("font_size", self.font_size)
            else:
                with self._config_lock:
                    self.model_tag = ""
                    self.model_title = ""
        except json.JSONDecodeError as e:
            logger.warning(f"Corrupt config file, using defaults: {e}")
            self._create_default_config()
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")

    def _create_default_config(self):
        with self._config_lock:
            self.model_tag = ""
            self.model_title = ""
        self.save()

    def refresh_model_from_detection(self):
        """Update model from auto-detected models after Ollama detection."""
        models = get_available_models()
        default = get_default_model()
        if default and (not self.model_tag or self.model_tag not in [m["tag"] for m in models]):
            with self._config_lock:
                self.model_tag = default
                match = next((m["title"] for m in models if m["tag"] == default), None)
                self.model_title = match if match else default.split(":")[0].replace("-", " ").title()
            self.save()
            self._notify("model")
            logger.info(f"Config refreshed with detected model: {default}")
        return bool(default)

    def save(self):
        try:
            with self._config_lock:
                data = {
                    "model_tag": self.model_tag,
                    "model_title": self.model_title,
                    "theme": self.theme_name,
                    "ollama_url": self.ollama_url,
                    "window_width": self.window_width,
                    "window_height": self.window_height,
                    "sidebar_width": self.sidebar_width,
                    "font_size": self.font_size,
                }
            MODEL_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = MODEL_CONFIG_FILE.with_suffix(".tmp")
            with open(tmp_path, "w") as f:
                json.dump(data, f, indent=2)
            tmp_path.replace(MODEL_CONFIG_FILE)
            logger.debug("Config saved successfully")
        except Exception as e:
            logger.warning(f"Failed to save config: {e}")

    def set_theme(self, name):
        with self._config_lock:
            if name == "dark":
                self.theme = THEME_DARK.copy()
            else:
                self.theme = THEME_LIGHT.copy()
            self.theme_name = name
        self.save()
        self._notify("theme")

    def set_model(self, tag, title):
        with self._config_lock:
            self.model_tag = tag
            self.model_title = title
        self.save()
        self._notify("model")

    def subscribe(self, callback):
        with self._listeners_lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def unsubscribe(self, callback):
        with self._listeners_lock:
            try:
                self._listeners.remove(callback)
            except ValueError:
                pass

    def _notify(self, event):
        with self._listeners_lock:
            listeners = list(self._listeners)
        for cb in listeners:
            try:
                cb(event)
            except Exception:
                pass

    def t(self, key):
        with self._config_lock:
            return self.theme.get(key, "#000000")
