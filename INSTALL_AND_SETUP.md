# GBLOXKOS_CODER — Installation & Setup Guide

**Version 2.0.0 | Developer: GBLOXK_OS LLC**

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installing Ollama](#2-installing-ollama)
3. [Installing GBLOXKOS_CODER](#3-installing-gbloxkos_coder)
4. [Pulling AI Models](#4-pulling-ai-models)
5. [Environment Variables](#5-environment-variables)
6. [Post-Installation Verification](#6-post-installation-verification)
7. [Troubleshooting Installation](#7-troubleshooting-installation)
8. [Uninstalling](#8-uninstalling)

---

## 1. Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| **Operating System** | Windows 10+, macOS 10.15+, Ubuntu 20.04+, or other Linux | Same |
| **Python** | 3.8 | 3.11+ |
| **RAM** | 8 GB | 16+ GB (for 7B+ models) |
| **Disk Space** | 500 MB (app) + 2–30 GB (models) | SSD recommended |
| **Internet** | Required for initial setup & web search | Required |
| **Display** | 1024×600 minimum | 1400×900+ recommended |

### Installing Python

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
```

#### macOS

```bash
# Using Homebrew
brew install python@3.11

# Or download from https://python.org
python3 --version
```

#### Windows

1. Download Python 3.11+ from [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Run the installer
3. **Check "Add Python to PATH"** during installation
4. Verify:

```cmd
python --version
```

### Installing System Dependencies (Linux)

Some optional system tools enhance functionality on Linux:

```bash
# Font support
sudo apt install fonts-cascadia-code

# Screen capture and UI automation (optional)
sudo apt install scrot maim gnome-screenshot xdotool wmctrl

# Audio control (optional)
sudo apt install alsa-utils pulseaudio-utils
```

> These are optional — GBLOXKOS_CODER works without them, but some AI tool functions (screenshot, hotkeys, media control) will be unavailable.

---

## 2. Installing Ollama

Ollama is the local LLM runtime that powers GBLOXKOS_CODER.

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Start the Ollama service
ollama serve
```

Verify:

```bash
curl http://127.0.0.1:11434/api/tags
```

### macOS

```bash
brew install ollama
```

Then launch from Applications or:

```bash
ollama serve
```

### Windows

1. Download the installer from [https://ollama.com/download/windows](https://ollama.com/windows)
2. Run `OllamaSetup.exe`
3. Launch "Ollama" from the Start Menu
4. Ollama runs automatically in the system tray

---

## 3. Installing GBLOXKOS_CODER

### Option A: Quick Install (Recommended)

```bash
# Clone or download the repository
git clone https://github.com/gbloxkos/gbloxkos_coder.git
cd gbloxkos_coder

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate          # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "from PyQt5 import QtWidgets; from ollama_client import get_client; print('OK')"
```

### Option B: Install with pip

If published to PyPI:

```bash
pip install gbloxkos-coder
```

(For the latest version, use Option A.)

### Option C: Run Without Virtual Environment

```bash
pip install -r requirements.txt
python app.py
```

> **Warning:** Installing packages system-wide may require `--user` flag or sudo on Linux/macOS.

### Verifying the Installation

```bash
python app.py
```

If successful, you'll see:
- A splash screen with progress
- A warning dialog if Ollama isn't running (non-fatal)
- The main dashboard window

---

## 4. Pulling AI Models

### Recommended Starting Model

```bash
ollama pull qwen2.5-coder
```

### Popular Models by Use Case

| Use Case | Model Command | Approx. Size |
|---|---|---|
| **Coding (recommended)** | `ollama pull qwen2.5-coder` | 4.7 GB |
| Code (smaller/faster) | `ollama pull qwen2.5-coder:3b` | 1.9 GB |
| Code (large, best quality) | `ollama pull qwen2.5-coder:14b` | 8.7 GB |
| General chat | `ollama pull qwen2.5` | 4.7 GB |
| Lightweight | `ollama pull phi3` | 1.7 GB |
| Code + general | `ollama pull llama3.1` | 4.9 GB |
| Heavy duty | `ollama pull deepseek-coder` | 7.0 GB |

### Listing Installed Models

```bash
ollama list
```

### Removing Models

```bash
ollama rm qwen2.5-coder:3b    # Remove specific model
ollama prune                  # Remove all unused models
```

### Model Selection in GBLOXKOS_CODER

1. After pulling a model, **restart GBLOXKOS_CODER**
2. The new model will appear in the **Model** dropdown in the sidebar
3. Select it — it takes effect for the next message

---

## 5. Environment Variables

### OLLAMA_BASE_URL

Override the default Ollama API endpoint:

```bash
export OLLAMA_BASE_URL=http://your-remote-host:11434
python app.py
```

This is useful for:
- Connecting to a remote Ollama server
- Custom port configurations
- Docker/OCI container setups

### Common Ollama Configuration

Set these **before starting Ollama** (not GBLOXKOS_CODER):

```bash
export OLLAMA_HOST=0.0.0.0:11434      # Allow external connections
export OLLAMA_NUM_GPU=1               # Use GPU (NVIDIA only)
export OLLAMA_MAX_LOADED_MODEL_GPU=1  # Max models on GPU
```

> On Linux/macOS, add these to `~/.bashrc` or `~/.zshrc` for persistence.

---

## 6. Post-Installation Verification

### Step-by-Step Verification

1. **Start Ollama:**
   ```bash
   ollama serve    # Linux/macOS
   # Windows: Ollama app from Start Menu
   ```

2. **Pull a model:**
   ```bash
   ollama pull qwen2.5-coder
   ```

3. **Launch GBLOXKOS_CODER:**
   ```bash
   python app.py
   ```

4. **Verify in GUI:**
   - Splash screen shows "Connecting to Ollama..." then "Welcome to GBLOXKOS_CODER!"
   - Sidebar shows the model in the dropdown
   - Top bar shows "Ready" status
   - Type a message and click Send

5. **Test the AI:**
   Ask: "What's 2 + 2?" — the AI should respond with "4"

### File Structure After Setup

```
gbloxkos_coder/
├── venv/                  # Virtual environment (if used)
├── app.py
├── config.py
├── ai_engine.py
├── ollama_client.py
├── protocol_parser.py
├── tools.py
├── web_search.py
├── session_manager.py
├── dashboard.py
├── requirements.txt
├── __init__.py
├── .gitignore
├── assets/
│   ├── *.ttf              # Fonts
├── chat_history/
│   ├── sessions.json      # Chat history
│   └── model_config.json  # Configuration
└── logs/
    └── gbloxkos.log       # Application logs
```

---

## 7. Troubleshooting Installation

### Common Installation Issues

#### Issue: `ModuleNotFoundError: No module named 'PyQt5'`

```bash
# Solution: Install dependencies
pip install PyQt5 requests psutil
```

#### Issue: `Permission denied` when running `python app.py`

```bash
# Solution: Check Python path or use virtual environment
python3 app.py   # Try python3 instead of python

# Or fix permissions
chmod +x app.py
```

#### Issue: `OSError: Cannot load library ...` on Linux

```bash
# Solution: Install Qt5 dependencies
sudo apt install libgl1-mesa-glx libegl1 libglib2.0-0
```

#### Issue: Display errors (Linux headless)

```bash
# Solution: Use virtual display
sudo apt install xvfb
xvfb-run python app.py
```

#### Issue: `Address already in use` on port 11434

```bash
# Ollama is already running or another service uses the port
# Check:
curl http://127.0.0.1:11434/api/tags

# Kill existing Ollama:
pkill -f ollama
# Then restart:
ollama serve
```

#### Issue: Slow model loading

This is normal for large models (7B+). The first query may take 10–60 seconds as the model loads into memory. Subsequent queries will be faster.

#### Issue: `Failed to load font` warnings in logs

These are non-fatal. The app falls back to system fonts. To resolve, ensure `assets/` directory is in the same folder as `app.py`.

#### Issue: Web search returns "Failed to connect"

- Check your internet connection
- Corporate firewalls may block search engines
- Try switching to a different search engine (the app tries multiple automatically)

### Checking Logs

View real-time logs:

```bash
# Linux/macOS
tail -f logs/gbloxkos.log

# Windows
type logs\gbloxkos.log
```

### Resetting Configuration

To reset to defaults:

```bash
# Close GBLOXKOS_CODER
# Delete config file
rm chat_history/model_config.json
rm chat_history/sessions.json
# Restart the application
python app.py
```

### Resetting Sessions Only (Keep Config)

```bash
rm chat_history/sessions.json
python app.py
```

---

## 8. Uninstalling

### Removing the Application

1. **Delete the application directory:**
   ```bash
   rm -rf /path/to/gbloxkos_coder
   ```

2. **Remove virtual environment (if created):**
   ```bash
   rm -rf /path/to/gbloxkos_coder/venv
   ```

3. **(Optional) Remove Ollama and models:**
   ```bash
   # Linux: stop Ollama
   sudo systemctl stop ollama
   sudo systemctl disable ollama
   sudo rm -rf /usr/local/bin/ollama

   # Remove models (frees significant disk space)
   ollama prune
   ```

### What Gets Removed

| Item | Removes with app? | Notes |
|---|---|---|
| Source code | Yes | Delete the directory |
| `chat_history/sessions.json` | Yes | Your chat history |
| `chat_history/model_config.json` | Yes | Your preferences |
| `logs/gbloxkos.log` | Yes | Application logs |
| Ollama installation | No | Separate install |
| Downloaded models | No | Stored in `~/.ollama/` |
| Python packages | No | Installed in venv or system |

---

## Quick Reference Card

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start Ollama (keep this running)
ollama serve

# 3. Pull a model
ollama pull qwen2.5-coder

# 4. In a separate terminal, install GBLOXKOS_CODER
git clone <repo> && cd gbloxkos_coder
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 5. Run the application
python app.py
```

---

*GBLOXKOS_CODER v2.0.0 — Installation & Setup Guide — Developed by GBLOXK_OS LLC*
