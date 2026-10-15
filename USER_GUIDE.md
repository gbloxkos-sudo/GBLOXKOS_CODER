# GBLOXKOS_CODER — User Guide

**Version 2.0.0 | Developer: GBLOXK_OS LLC**

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Main Interface](#2-main-interface)
3. [Starting a Conversation](#3-starting-a-conversation)
4. [Managing Chat Sessions](#4-managing-chat-sessions)
5. [Model Selection](#5-model-selection)
6. [The Code Editor (Canvas)](#6-the-code-editor-canvas)
7. [Themes](#7-themes)
8. [Keyboard Shortcuts](#8-keyboard-shortcuts)
9. [Navigation Panes](#9-navigation-panes)
10. [AI Assistant Features](#10-ai-assistant-features)
11. [System Tools](#11-system-tools)
12. [Web Search & Browsing](#12-web-search--browsing)
13. [Settings & Information](#13-settings--information)
14. [Exporting Conversations](#14-exporting-conversations)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Getting Started

### Launching the Application

Ensure Ollama is installed and running before launching:

```bash
# Linux/macOS — start the Ollama daemon
ollama serve

# Windows — start the Ollama app from the Start Menu
```

Then run GBLOXKOS_CODER:

```bash
python app.py
```

**Splash Screen:** When the application starts, you'll see a splash screen with a progress bar. It performs the following steps:

1. Initializing GBLOXKOS_CODER
2. Loading fonts and themes
3. Connecting to Ollama
4. Detecting installed models
5. Loading session data
6. Preparing the AI engine
7. Welcome message

> **Note:** If Ollama is not detected, a warning dialog will appear. You can still use the GUI, but AI chat will not work until Ollama is available.

### First-Time Setup

On first launch:

1. The application creates `chat_history/` and `logs/` directories
2. A default configuration is saved to `chat_history/model_config.json`
3. The application auto-detects installed Ollama models
4. A session is automatically created if none exists
5. A random welcome message is displayed in the chat area

---

## 2. Main Interface

The main window is divided into several areas:

```
+------------------+-------------------------------------------------+
| Sidebar (260px)  | Main Content Area                               |
|                  |                                                 |
|  [GBLOXKOS_CODER]|  ┌────────────────────────────────────────────┐ |
|  + New Chat      |  │ Top Bar: Status | Session Title | Theme    │ |
|  Chat            |  ├────────────────────────────────────────────┤ |
|  Tools (active)  |  │ Chat Area (scrollable message bubbles)      │ |
|  System          |  │                                             │ |
|                  |  │ User messages appear on the right           │ |
|  HISTORY         |  │ AI messages appear on the left              │ |
|  [Chat 1 (5)]    |  │ Each has a Copy button                      │ |
|  [Chat 2 (3)]    |  │                                             │ |
|                  |  ├────────────────────────────────────────────┤ |
|  Model: [Qwen..] |  │ Input Box: [Type your message here...]      │ |
|  Settings        |  │          [Send] [Stop]                      │ |
|                  |  └────────────────────────────────────────────┘ |
|                  |                                                 |
|                  |  ┌────────────────────────────────────────────┐ |
|                  |  │ Code Editor (Canvas) — collapsible         │ |
|                  |  └────────────────────────────────────────────┘ |
+------------------+-------------------------------------------------+
```

### Key UI Elements

| Element | Description |
|---|---|
| **Sidebar** | Navigation, chat history, model selector, settings |
| **Top Bar** | Status label, session title, theme toggle |
| **Chat Area** | Scrollable conversation with rich bubbles |
| **Input Box** | Type messages here; press Enter or click Send |
| **Send Button** | Submits your message to the AI |
| **Stop Button** | Aborts the current AI response |
| **Code Editor** | Collapsible panel on the right for displaying code |

---

## 3. Starting a Conversation

1. Type your message in the input box at the bottom of the window
2. Press **Enter** or click the **Send** button
3. The message appears as a **blue bubble** (user side) on the right
4. The status bar changes to "Thinking..." with a **yellow** color
5. The AI responds in a **gray bubble** (AI side) on the left
6. The status returns to "Ready" (green) when complete

### Message Features

- **Text Selection:** All message text is selectable
- **Copy Button:** Each bubble has a "Copy" button to copy the entire message
- **Code Blocks:** AI responses containing code are rendered with syntax highlighting
- **Code Copy:** Use the "Copy Code" button on individual code blocks

### Sending Messages

| Method | Action |
|---|---|
| Type + Enter | Sends the message |
| Type + Click "Send" | Sends the message |
| Paste + Enter | Pastes clipboard text and sends |
| Click "Stop" during AI response | Aborts generation |

---

## 4. Managing Chat Sessions

### What Are Sessions?

Each conversation is saved as a **session** — a persistent record of all messages between you and the AI. Sessions are automatically saved to `chat_history/sessions.json`.

### Creating a New Session

- Click the **+ New Chat** button in the sidebar
- Or use the shortcut **Ctrl+N**
- The old session remains in history; a new empty session is created

### Switching Between Sessions

- Click any session in the **HISTORY** list in the sidebar
- The current chat display clears and the selected session's messages load
- The session title appears in the **top bar**

### Session Details

Each session in the history list shows:

```
Session Title (message_count)
```

Example: `"How do I use Git?" (12)`

### Renaming Sessions

Currently, sessions are auto-named using the first ~40 characters of the AI's first response. To rename:

- Use the context menu (right-click in the chat area) — planned for future versions
- Or edit `chat_history/sessions.json` directly

### Deleting Session History

#### Clear Current Chat

- Right-click in the chat area and select **Clear Current Chat** from the context menu
- This creates a new session (doesn't delete the old one)

#### Clear ALL History

- Click **Clear All History** at the bottom of the sidebar
- A confirmation dialog appears — click **Yes** to delete all sessions permanently
- A new empty session is created automatically

> **Warning:** Clearing all history is irreversible. The `sessions.json` file is deleted.

---

## 5. Model Selection

### How Models Work

GBLOXKOS_CODER connects to Ollama to use local LLM models. The model dropdown shows all non-embedding models detected from your Ollama installation.

### Selecting a Model

1. In the sidebar, find the **Model** dropdown
2. Click the dropdown to see available models
3. Select a model — it takes effect immediately for the next message
4. The status bar briefly shows "Model: {model_title}"

### Model Display Format

Models show as:

```
Display Name  (Size)
```

Example: `Qwen2.5 Coder  (4.7 GB)`

### Auto-Detection

When GBLOXKOS_CODER starts:

1. It queries Ollama at `http://127.0.0.1:11434/api/tags`
2. Detected models are sorted with code-specialized models first
3. The best available code model is set as default
4. The selection is saved in `model_config.json`

### Pulling New Models

If you don't have any models installed:

```bash
ollama pull qwen2.5-coder
```

Then restart GBLOXKOS_CODER or click **Settings** in the sidebar and look for detected models.

### Fallback Models

If auto-detection fails, these models are checked in order:

1. `qwen2.5-coder`
2. `qwen2.5`
3. `llama3.1`
4. `llama3`
5. `gemma2`
6. `phi3`
7. `mistral`
8. `deepseek-coder`

---

## 6. The Code Editor (Canvas)

### What Is the Canvas?

The **Canvas** is a collapsible code editor panel on the right side of the window. When the AI sends code via the `//tool="canvas"` protocol, the code is displayed in this panel with:

- Monospace font (Cascadia Code, 11pt)
- Syntax-highlighted background
- Line number support
- Copy All button

### Viewing Code

When the AI sends code to the canvas:

1. The canvas panel automatically appears (if hidden)
2. Code is displayed with the filename in the title bar (if provided)
3. The canvas raises to the front

### Copying Code

- Click **Copy All** in the canvas header to copy the entire code content
- Click the **X** button in the canvas header to collapse the panel

### Collapsing/Expanding

- Click the **X** button to collapse the canvas
- The AI can send new code to re-open it

---

## 7. Themes

### Switching Themes

Click the **Theme** button in the top-right corner to toggle between:

| Theme | Preview |
|---|---|
| **Dark** (default) | Dark background (`#0d1117`), light text, blue accents |
| **Light** | White background (`#ffffff`), dark text, green accents |

### Theme Persistence

Your theme preference is saved in `model_config.json` and restored on next launch.

### Theme-Aware Elements

When the theme changes, all of the following update in real-time:

- Main background
- Sidebar background
- Chat bubbles
- Input box
- Buttons (Send, Stop, Theme)
- Status label
- History list
- Canvas panel
- Splitter handles
- Scrollbars

---

## 8. Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| **Ctrl+N** | New chat |
| **Ctrl+Q** | Quit application |
| **Ctrl+F** | Focus input box / search |
| **Ctrl+C** | Copy selection (or abort if in a text field) |
| **Ctrl+V** | Paste from clipboard |
| **Ctrl+A** | Select all text in focused field |
| **Ctrl+Shift+V** | Paste (Linux) |

### Context Menu Shortcuts

Right-click anywhere in the chat or input area to open the context menu:

- **Cut** (when text is selected)
- **Copy** (when text is selected)
- **Paste**
- **Select All** (in text fields)
- **Copy All** (in code editor)
- **New Chat**
- **Clear Current Chat**
- **Clear All History**
- **Paste to Input**

---

## 9. Navigation Panes

### Sidebar Structure

The left sidebar contains:

1. **Logo Bar** — "GBLOXKOS_CODER" header
2. **New Chat Button** — `+ New Chat`
3. **Navigation Buttons:**
   - **Chat** — Switch to chat view (default)
   - **Tools** — Displays list of available system tools
   - **System** — Displays system information and AI status
4. **History List** — All saved chat sessions
5. **Clear All History** — Wipe all sessions
6. **Model Selector** — Dropdown for Ollama model selection
7. **Settings** — Displays current settings info

### Navigation Actions

| Button | Action |
|---|---|
| **Chat** | Returns to the main chat view |
| **Tools** | Shows a bubble listing all available system tools with descriptions |
| **System** | Shows a bubble with platform info, Ollama status, current model, and session/message counts |
| **Settings** | Shows a bubble with current theme, model, Ollama URL, and detected models |

---

## 10. AI Assistant Features

### Chat Capabilities

GBLOXKOS_CODER's AI can:

- **Answer questions** — General knowledge, coding concepts, system info
- **Write code** — Generate complete, production-ready code in any language
- **Debug code** — Identify and fix bugs when you provide error messages
- **Explain code** — Line-by-line breakdowns of existing code
- **Refactor code** — Improve readability, performance, and maintainability
- **Code review** — Identify bugs, improvements, and best practices
- **Browse the web** — Search and summarize information from the internet
- **Control your system** — Run commands, manage files, check resources

### Example Prompts

```
Write a Python function to parse JSON.

Explain this JavaScript code:

function add(a, b) {
  return a + b;
}

Debug this error:
Traceback (most recent call last):
  File "app.py", line 10, in <module>
    print(x)
NameError: name 'x' is not defined

Search the web for "latest Python release".

What's my CPU model and usage?

List files in ~/Documents.
```

### AI Response Handling

When the AI generates a response, the system:

1. **Parses tool calls** — Extracts `//tool="..."` protocol blocks
2. **Executes tools** — Runs each tool with retry logic (up to 3 attempts)
3. **Streams results** — Tool outputs are relayed back to the AI
4. **Displays bubbles** — Text and tool results are shown as message bubbles
5. **Updates canvas** — Code from `canvas` tool calls is rendered in the editor

### Aborting Responses

To stop the AI mid-response:

1. Click the **Stop** button
2. The request is immediately aborted
3. The connection to Ollama is reset
4. Status returns to "Error stopped"

---

## 11. System Tools

GBLOXKOS_CODER's AI can execute system tools through the tool protocol. These are invoked when the AI outputs `//tool` commands in its response.

### Filesystem Tools

| Tool | Description | Example |
|---|---|---|
| `fs_read` | Read a file | `//tool="fs_read" head="Read config" value="/etc/hostname"` |
| `fs_write` | Write to a file | `//tool="fs_write" head="Write script" value="script.py:::print('Hello')"` |
| `fs_append` | Append to a file | `//tool="fs_append" head="Add note" value="notes.txt:::Updated on 2024-01-01"` |
| `fs_delete` | Delete a file/dir | `//tool="fs_delete" head="Remove temp" value="/tmp/old_file.txt"` |
| `fs_list` | List directory | `//tool="fs_list" head="List home" value="~"` |
| `fs_find` | Find files by pattern | `//tool="fs_find" head="Find Python files" value="*.py in ~/projects"` |
| `fs_copy` | Copy file | `//tool="fs_copy" value="src.py:::dst.py"` |
| `fs_move` | Move file | `//tool="fs_move" value="old.py:::new.py"` |

### Command Execution

| Tool | Description | Example |
|---|---|---|
| `cmd_exec` | Run a shell command | `//tool="cmd_exec" value="ls -la"` |
| `powershell` | Run PowerShell | `//tool="powershell" value="Get-Process"` |
| `open_app` | Launch an application | `//tool="open_app" value="firefox"` |

### Process Management

| Tool | Description | Example |
|---|---|---|
| `proc_list` | List processes | `//tool="proc_list" value="python"` |
| `proc_kill` | Kill a process | `//tool="proc_kill" value="python"` |

### System Information

| Tool | Description | Example |
|---|---|---|
| `sys_cpu` | CPU info | `//tool="sys_cpu" value=""` |
| `sys_ram` | RAM info | `//tool="sys_ram" value=""` |
| `sys_gpu` | GPU info | `//tool="sys_gpu" value=""` |
| `sys_disk` | Disk info | `//tool="sys_disk" value="/"` |

### Web Tools

| Tool | Description | Example |
|---|---|---|
| `web_search` | Search the web | `//tool="web_search" value="Python best practices"` |
| `web_browse` | Browse a URL | `//tool="web_browse" value="https://example.com"` |
| `web_open` | Open URL in browser | `//tool="web_open" value="https://github.com"` |
| `net_ping` | Ping a host | `//tool="net_ping" value="google.com"` |

### UI Control

| Tool | Description | Example |
|---|---|---|
| `type_text` | Type text | `//tool="type_text" value="Hello World"` |
| `hotkey` | Send hotkey | `//tool="hotkey" value="ctrl+c"` |
| `screenshot` | Take screenshot | `//tool="screenshot" value=""` |
| `ui_windows` | List windows | `//tool="ui_windows" value=""` |
| `ui_focus` | Focus a window | `//tool="ui_focus" value="Terminal"` |

### Media Control

| Tool | Description | Example |
|---|---|---|
| `media_volume` | Volume control | `//tool="media_volume" value="up"` |
| `media_key` | Media keys | `//tool="media_key" value="play"` |

### Safety Features

- `fs_delete` refuses to delete critical system paths (e.g., `/`, `/etc`, `/usr`)
- `fs_delete` refuses to delete protected directories (e.g., `~/.ssh`, `~/.config`, `~/Documents`)
- `fs_delete` is restricted to paths within the user's home directory
- File operations enforce proper error handling with descriptive messages
- Command execution enforces timeouts (default: 60 seconds)
- Web browsing blocks private/local IP ranges (SSRF protection)

---

## 12. Web Search & Browsing

### Search Engines

GBLOXKOS_CODER cycles through search engines when you ask it to search the web:

1. **DuckDuckGo** (primary — HTML-based, privacy-focused)
2. **Startpage** (privacy-focused, Google results)
3. **Bing** (Microsoft's search engine)

The first engine that returns results is used. You can view which engine was used in the AI's response.

### Asking the AI to Search

Simply ask in natural language:

```
Search for the latest Python features
What is quantum computing?
Latest news about AI
```

### Web Browsing

Ask the AI to browse specific URLs:

```
Browse https://docs.python.org/3/
What does this page say: https://example.com/article
```

The browser extracts readable text from HTML pages, strips ads/navigation, and summarizes content up to 15,000 characters.

---

## 13. Settings & Information

### Viewing Settings

Click **Settings** in the sidebar to see a bubble with:

- Current theme (Dark/Light)
- Current model name and tag
- Ollama URL
- Detected models list

### Changing Configuration

Settings are stored in `chat_history/model_config.json`. You can:

- **Toggle theme** — Click the Theme button in the top bar
- **Change model** — Select from the dropdown in the sidebar
- **Edit model_config.json** manually — Stop the app first, edit the file, restart

### System Information

Click **System** in the sidebar to see:

- Platform (OS and version)
- Machine architecture
- Python version
- Ollama connection status
- Current model
- Session and message counts

### Viewing Available Tools

Click **Tools** in the sidebar to see all available system tools categorized by function.

---

## 14. Exporting Conversations

### Export Formats

Sessions can be exported in two formats via the `SessionManager`:

| Format | Description |
|---|---|
| `json` | Full session data including metadata, timestamps, message roles |
| `text` | Human-readable conversation with timestamps and roles |

### Export Usage

Exporting is currently available programmatically:

```python
from session_manager import get_session_manager
sm = get_session_manager()

# Export current session as JSON
json_data = sm.export_session(sm.current_session_id, fmt="json")
with open("my_chat.json", "w") as f:
    f.write(json_data)

# Export as text
text_data = sm.export_session(sm.current_session_id, fmt="text")
with open("my_chat.txt", "w") as f:
    f.write(text_data)
```

### Search Sessions

You can search through all session content:

```python
results = sm.search_sessions("python")
for s in results:
    print(s["title"])
```

---

## 15. Troubleshooting

### Common Issues

#### Q: The AI says "No AI models available"
**Solution:** Install a model in Ollama:
```bash
ollama pull qwen2.5-coder
```
Then restart GBLOXKOS_CODER.

#### Q: "Ollama Not Detected" dialog on startup
**Solution:** Start the Ollama service:
```bash
# Linux/macOS
ollama serve

# Windows: Launch from Start Menu
```

#### Q: The window is too small or too large
**Solution:** The window size is saved between sessions. To reset:
1. Close the app
2. Edit `chat_history/model_config.json`
3. Set `"window_width": 1400` and `"window_height": 900`
4. Restart

#### Q: Chat history is not loading
**Solution:** Check that `chat_history/sessions.json` exists and is valid JSON. If corrupted, it will be backed up as `sessions.corrupt.{timestamp}`.

#### Q: Web search returns no results
**Solution:**
- Check your internet connection
- Some corporate firewalls block search engines
- Try browsing a specific URL directly

#### Q: Code blocks don't show syntax highlighting
**Solution:** Code highlighting is applied when the response contains markdown code blocks (` ``` `). If the AI doesn't use markdown, code is displayed as plain text.

#### Q: The canvas panel won't appear
**Solution:** The canvas appears automatically when the AI sends code. If you don't see it:
- Check that the AI used the `//tool="canvas"` protocol
- The canvas may be collapsed — look for the right edge of the window

### Getting Help

For additional support, view logs at `logs/gbloxkos.log` or contact GBLOXKOS_OS LLC support.

---

## Appendix: File Locations

| Resource | Path |
|---|---|
| Source code | Project root directory |
| Fonts | `assets/` |
| Session history | `chat_history/sessions.json` |
| Model config | `chat_history/model_config.json` |
| Log file | `logs/gbloxkos.log` (rotates at 5MB, 3 backups) |
| Session backups | `chat_history/sessions.corrupt.{timestamp}` |

---

*GBLOXKOS_CODER v2.0.0 — Developed by GBLOXK_OS LLC*
