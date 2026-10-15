# GBLOXKOS_CODER

**Expert AI Coding Assistant & Chat Engine**

Version 2.0.0 | Developer: **GBLOXK_OS LLC**

---

## Overview

GBLOXKOS_CODER is a powerful, privacy-focused desktop AI coding assistant built with Python and PyQt5. It connects to [Ollama](https://ollama.com) to run local LLMs (including code-specialized models like Qwen2.5-Coder, Llama 3.1, and DeepSeek-Coder) and provides a rich, modern GUI for natural conversations, code generation, system control, and web research — all running entirely on your machine.

No cloud. No data leaving your computer. Just pure, local AI power.

### Key Features

- **Local AI Chat** — Run Ollama models locally (qwen2.5-coder, llama3.1, gemma2, deepseek-coder, and more)
- **Multi-turn Conversations** — Persistent chat sessions with full history
- **AI-Powered Code Generation** — Write, refactor, explain, and debug code in any language
- **System Tool Execution** — Your AI can run shell commands, manage files, list/kill processes, and query system resources
- **Web Search & Browsing** — DuckDuckGo, Startpage, and Bing search; full-page content extraction
- **Rich Code Display** — Syntax-highlighted code blocks with per-block copy buttons
- **Dual Theme Support** — Professional dark and light themes
- **Splash Screen** — Polished startup experience with progress tracking
- **Persistent Configuration** — Window size, theme, and model preferences saved automatically
- **Keyboard Shortcuts** — Ctrl+N (new chat), Ctrl+Q (quit), Ctrl+F (search), Ctrl+C/V/A (standard)
- **Crash Handling** — Global exception handler with user-friendly error dialogs and logging

### Screenshots

```
+----------------------------------------------------------+
| GBLOXKOS_CODER v2.0.0                                    | X
+------+--------------------------------------------------+
|Chat  |  [Your message]                                   |
|Tools |  -----------------------------------------        |
|System|  AI: Here's the Python code you requested...      |
|Hist  |  ```python                                       |
|      |  def hello():                                     |
|      |      print("Hello!")                              |
|      |  ```                                              |
|      |  [Copy Code]                                      |
|      |                                                   |
|      |  -----------------------------------------        |
|      |  You: How do I install requests?                  |
|      |  -----------------------------------------        |
|      |  AI: Run: pip install requests                   |
|      |                                                   |
|      |  [Input box...]                        [Send][Stop]|
+------+--------------------------------------------------+
| [canvas collapsed]                                     |
+----------------------------------------------------------+
```

---

## Architecture

```
GBLOXKOS_CODER/
├── app.py                  # Entry point: splash screen, font setup, theme palette, app launch
├── config.py               # Centralized configuration: themes, model detection, Config singleton
├── ai_engine.py            # AI engine: chat loop, tool execution, code review/debug/refactor
├── ollama_client.py        # Ollama API client: chat, generate, pull, delete, health checks
├── protocol_parser.py      # Tool-call protocol parser: //tool="name" head="..." value="..."
├── tools.py                # Cross-platform system tools registry and implementations
├── web_search.py           # Web search (DuckDuckGo/Startpage/Bing) and URL browsing
├── session_manager.py      # Chat session persistence: save/load/rename/delete/export sessions
├── dashboard.py            # PyQt5 GUI: main window, chat bubbles, sidebar, canvas, settings
├── requirements.txt        # Python dependencies
├── __init__.py             # Package metadata
├── assets/                 # Fonts (Geomini, GoogleSans, GoogleSansCode, Honk, Michroma, Outfit, SourGummy)
├── chat_history/           # Session storage (sessions.json, model_config.json)
└── logs/                   # Rotating log file (gbloxkos.log)
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `app.py` | Bootstrap; splash screen; Qt style/palette; Ollama detection at launch; crash handler |
| `config.py` | Singleton `Config` class; theme definitions; model auto-detection from Ollama; constants |
| `ai_engine.py` | `AIEngine` class; streaming chat; tool-call extraction & execution; retry logic; code review/generate/refactor/debug |
| `ollama_client.py` | `OllamaClient` singleton; HTTP API to Ollama; health checks, model listing, pull, delete |
| `protocol_parser.py` | Parse `//tool="name" head="..." value="..."` protocol from model output |
| `tools.py` | 30+ system tools (filesystem, processes, system info, web, UI control, media) |
| `web_search.py` | Search engine integration; HTML content extraction; security (blocks private IPs) |
| `session_manager.py` | Session lifecycle; JSON persistence; export to JSON/text; search; stats |
| `dashboard.py` | Full PyQt5 GUI with chat bubbles, code rendering, sidebar navigation, canvas panel |

---

## AI Tool Protocol

GBLOXKOS_CODER's AI model outputs tool calls using a custom protocol:

```
//tool="tool_name" head="optional_description" value="parameters"
```

**Example AI output:**
```
Let me check the system's CPU info:

//tool="sys_cpu" head="CPU Info" value=""

And here's the result.
```

**Available Tools:**

| Category | Tools |
|---|---|
| **File System** | `fs_read`, `fs_write`, `fs_append`, `fs_delete`, `fs_list`, `fs_find`, `fs_copy`, `fs_move` |
| **Commands** | `cmd_exec`, `powershell`, `open_app` |
| **Processes** | `proc_list`, `proc_kill` |
| **System Info** | `sys_cpu`, `sys_ram`, `sys_gpu`, `sys_disk` |
| **Web** | `web_search`, `web_browse`, `web_open`, `net_ping` |
| **UI Control** | `type_text`, `hotkey`, `screenshot`, `ui_windows`, `ui_focus` |
| **Media** | `media_volume`, `media_key` |
| **AI Output** | `canvas` (send code to editor), `msg` (display text) |

---

## Requirements

### System Requirements

- **OS:** Linux, macOS, or Windows
- **Python:** 3.8+
- **Display:** X11/Wayland (Linux), any (Windows/macOS)

### Python Dependencies

All listed in [`requirements.txt`](requirements.txt):

| Package | Purpose |
|---|---|
| `PyQt5 >= 5.15` | GUI framework |
| `requests >= 2.28` | HTTP client for Ollama API and web search |
| `psutil >= 5.9` | System resource monitoring |

### External Requirements

- **Ollama** — Must be installed and running for AI features. The GUI works without Ollama but AI chat is disabled.
- **Optional for Linux:** `xdotool` (keyboard/media control), `scrot`/`maim`/`gnome-screenshot` (screenshots), `wmctrl` (window management), `amixer`/`pactl` (volume control)

---

## Installation

See **[INSTALL_AND_SETUP.md](INSTALL_AND_SETUP.md)** for detailed installation and configuration instructions.

Quick start:

```bash
git clone <repo-url>
cd GBLOXKOS_CODE_AI
python -m venv venv
source venv/bin/activate        # Linux/macOS
# or: venv\Scripts\activate      # Windows
pip install -r requirements.txt
ollama pull qwen2.5-coder       # Pull a code model
python app.py
```

---

## Usage

See **[USER_GUIDE.md](USER_GUIDE.md)** for a complete user guide.

```bash
python app.py
```

---

## Configuration

Configuration is stored in `chat_history/model_config.json`:

| Setting | Default | Description |
|---|---|---|
| `model_tag` | auto-detected | Currently selected Ollama model |
| `model_title` | auto-detected | Human-readable model name |
| `theme` | `"dark"` | `"dark"` or `"light"` |
| `ollama_url` | `http://127.0.0.1:11434` | Ollama API base URL |
| `window_width` | `1400` | Window width in pixels |
| `window_height` | `900` | Window height in pixels |
| `sidebar_width` | `260` | Sidebar width in pixels |
| `font_size` | `13` | Chat font size |

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Override the Ollama API endpoint at startup |

---

## Recommended Ollama Models

| Model | Size | Best For |
|---|---|---|
| `qwen2.5-coder` | 7B / 14B / 32B | Coding, debugging, refactoring (primary) |
| `qwen2.5` | 7B / 14B / 32B | General chat and reasoning |
| `llama3.1` | 8B / 70B | General-purpose assistant |
| `gemma2` | 7B / 9B | Lightweight chat |
| `deepseek-coder` | 6.7B / 33B | Code generation |
| `phi3` | 3.8B | Low-resource, fast response |
| `mistral` | 7B | General reasoning |

```bash
ollama pull qwen2.5-coder    # Recommended: best code model
```

---

## Development

### Project Structure

The application follows a modular, layered architecture:

1. **Entry Layer** (`app.py`) — Bootstrapping, UI theme setup, launch sequence
2. **Service Layer** — `ollama_client.py`, `ai_engine.py`, `web_search.py`, `tools.py`, `protocol_parser.py`, `session_manager.py`
3. **Configuration Layer** (`config.py`) — Themes, constants, model management
4. **Presentation Layer** (`dashboard.py`) — All GUI components

### Logging

Logs are written to `logs/gbloxkos.log` with rotation (5 MB max, 3 backups). Log level is set to `INFO`.

To view logs in real-time:

```bash
tail -f logs/gbloxkos.log
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Ollama not detected" on startup | Start Ollama: `ollama serve` (Linux/macOS) or start the Ollama app (Windows) |
| AI chat returns "No AI models available" | Pull a model: `ollama pull qwen2.5-coder` |
| Slow responses | Use a smaller model (e.g., `qwen2.5-coder:3b` or `phi3`) |
| Web search not working | Check firewall/proxy settings; try a different search engine |
| GUI appears garbled | Ensure PyQt5 is up to date: `pip install --upgrade PyQt5` |
| Fonts not loading | Ensure `assets/` directory is present alongside source files |

---

## License

Developed by **GBLOXK_OS LLC**

This project is provided as-is for educational and personal use. See source headers for details.

---

## Credits

- **Developer:** GBLOXK_OS LLC
- **LLM Backend:** [Ollama](https://ollama.com)
- **GUI Framework:** [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- **Fonts:** Google Fonts, Honk, Michroma, SourGummy, Geomini
- **Search Engines:** DuckDuckGo, Startpage, Bing
