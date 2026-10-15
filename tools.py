"""Cross-platform system tools for GBLOXKOS_CODER."""
import os
import re
import shutil
import subprocess
import platform
import logging
from pathlib import Path

logger = logging.getLogger("gbloxkos.tools")

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"

SHELL = "powershell.exe" if IS_WINDOWS else "/bin/bash"
SHELL_FLAG = "-Command" if IS_WINDOWS else "-c"
MAX_OUTPUT_LENGTH = 30000


def _run_cmd(command, timeout=60):
    if not command or not str(command).strip():
        return {"success": False, "output": "Empty command", "error": True}
    try:
        result = subprocess.run(
            str(command), shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(Path.home()),
            env={**os.environ, "LC_ALL": "C.UTF-8"},
        )
        output = result.stdout or ""
        err = result.stderr or ""
        if err and not output:
            output = err
        if len(output) > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH] + "\n\n[...output truncated...]"
        return {"success": result.returncode == 0, "output": output.strip(), "error": result.returncode != 0}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": f"Command timed out after {timeout}s", "error": True}
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return {"success": False, "output": str(e), "error": True}


def cmd_exec(command, timeout=60):
    return _run_cmd(command, timeout)


def powershell(command, timeout=60):
    if not command or not str(command).strip():
        return {"success": False, "output": "Empty command", "error": True}
    if IS_WINDOWS:
        try:
            import base64
            encoded = base64.b64encode(str(command).encode("utf-16-le")).decode("ascii")
            full_cmd = f'powershell.exe -NoProfile -NonInteractive -EncodedCommand {encoded}'
        except Exception:
            escaped_cmd = str(command).replace('"', '`"').replace('`', '``')
            full_cmd = f'powershell.exe -NoProfile -Command "{escaped_cmd}"'
    else:
        if shutil.which("pwsh"):
            escaped_cmd = str(command).replace("'", "'\\''")
            full_cmd = f"pwsh -NoProfile -Command '{escaped_cmd}'"
        else:
            return {"success": False, "output": "PowerShell (pwsh) not installed on this system", "error": True}
    return _run_cmd(full_cmd, timeout)


def fs_read(file_path, max_chars=50000):
    try:
        if not file_path or not str(file_path).strip():
            return {"success": False, "output": "Empty file path"}
        p = Path(file_path).expanduser().resolve()
        if not p.exists():
            return {"success": False, "output": f"File not found: {file_path}"}
        if not p.is_file():
            return {"success": False, "output": f"Not a file: {file_path}"}
        if p.stat().st_size > 1048576:
            with open(p, "r", errors="replace") as f:
                content = f.read(max_chars)
            return {"success": True, "output": content + "\n\n[File truncated - showing first 50KB]"}
        with open(p, "r", errors="replace") as f:
            content = f.read()
        return {"success": True, "output": content}
    except PermissionError:
        return {"success": False, "output": f"Permission denied: {file_path}"}
    except Exception as e:
        return {"success": False, "output": f"Error reading file: {e}"}


def fs_write(file_path_content):
    parts = file_path_content.split(":::", 1)
    if len(parts) != 2:
        return {"success": False, "output": "Format: file_path:::content"}
    file_path, content = parts
    try:
        if not file_path or not str(file_path).strip():
            return {"success": False, "output": "Empty file path"}
        p = Path(file_path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w") as f:
            f.write(content)
        return {"success": True, "output": f"Written {len(content)} chars to {p}"}
    except PermissionError:
        return {"success": False, "output": f"Permission denied: {file_path}"}
    except Exception as e:
        return {"success": False, "output": f"Error writing file: {e}"}


def fs_append(file_path_content):
    parts = file_path_content.split(":::", 1)
    if len(parts) != 2:
        return {"success": False, "output": "Format: file_path:::content"}
    file_path, content = parts
    try:
        if not file_path or not str(file_path).strip():
            return {"success": False, "output": "Empty file path"}
        p = Path(file_path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a") as f:
            f.write(content)
        return {"success": True, "output": f"Appended {len(content)} chars to {p}"}
    except PermissionError:
        return {"success": False, "output": f"Permission denied: {file_path}"}
    except Exception as e:
        return {"success": False, "output": f"Error appending: {e}"}


def fs_delete(path):
    try:
        if not path or not str(path).strip():
            return {"success": False, "output": "Empty path"}
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"success": False, "output": f"Path not found: {path}"}
        home = Path.home().resolve()
        try:
            p.relative_to(home)
        except ValueError:
            return {"success": False, "output": f"Cannot delete outside home directory: {path}"}
        critical_paths = {
            home, home / ".ssh", home / ".gnupg", home / ".bashrc",
            home / ".bash_history", home / ".profile", home / ".gitconfig",
            home / ".config", home / ".local", home / ".cache",
            home / ".bash_history", home / ".zshrc", home / ".zprofile",
            home / "Documents", home / "Downloads", home / "Desktop",
            home / "Pictures", home / "Music", home / "Videos",
            home / "Public", home / "Templates",
            Path("/"), Path("/etc"), Path("/usr"), Path("/bin"),
            Path("/sbin"), Path("/lib"), Path("/var"), Path("/boot"),
            Path("/sys"), Path("/proc"), Path("/dev"), Path("/run"),
        }
        for cp in critical_paths:
            try:
                cp_resolved = cp.expanduser().resolve()
                if p == cp_resolved or str(p) == str(cp_resolved):
                    return {"success": False, "output": f"Cannot delete critical system path: {path}"}
            except Exception:
                pass
        # Check if trying to delete a protected directory
        try:
            relative = p.relative_to(home)
            if len(relative.parts) == 1 and relative.parts[0] in {".ssh", ".gnupg", ".config", ".local", "Documents", "Downloads", "Desktop", "Pictures", "Music", "Videos", "Public", "Templates"}:
                return {"success": False, "output": f"Cannot delete protected directory: {path}"}
        except ValueError:
            pass
        if p.is_file():
            p.unlink()
            return {"success": True, "output": f"Deleted file: {p}"}
        elif p.is_dir():
            shutil.rmtree(p)
            return {"success": True, "output": f"Deleted directory: {p}"}
        return {"success": False, "output": f"Unknown path type: {path}"}
    except PermissionError:
        return {"success": False, "output": f"Permission denied: {path}"}
    except Exception as e:
        logger.error(f"Error deleting path {path}: {e}")
        return {"success": False, "output": f"Error deleting: {e}"}


def fs_list(directory="."):
    try:
        if not directory or not str(directory).strip():
            directory = "."
        p = Path(directory).expanduser().resolve()
        if not p.exists():
            return {"success": False, "output": f"Directory not found: {directory}"}
        if not p.is_dir():
            return {"success": False, "output": f"Not a directory: {directory}"}
        entries = []
        count = 0
        for item in sorted(p.iterdir()):
            count += 1
            if count > 500:
                entries.append(f"  ... and more than 500 entries")
                break
            prefix = "  [DIR] " if item.is_dir() else "  [FILE]"
            try:
                size = item.stat().st_size if item.is_file() else 0
                size_str = _human_size(size) if item.is_file() else ""
            except Exception:
                size_str = ""
            entries.append(f"{prefix} {item.name} {size_str}")
        if not entries:
            return {"success": True, "output": f"Empty directory: {p}"}
        header = f"Contents of {p} ({count} entries):\n"
        return {"success": True, "output": header + "\n".join(entries)}
    except PermissionError:
        return {"success": False, "output": f"Permission denied: {directory}"}
    except Exception as e:
        return {"success": False, "output": f"Error listing: {e}"}


def fs_find(pattern, search_dir="."):
    try:
        if not pattern or not str(pattern).strip():
            return {"success": False, "output": "Empty search pattern"}
        search_path = Path(search_dir).expanduser().resolve()
        if not search_path.exists():
            return {"success": False, "output": f"Directory not found: {search_dir}"}
        matches = list(search_path.rglob(pattern))
        if not matches:
            return {"success": True, "output": f"No files matching '{pattern}' in {search_path}"}
        result_lines = [str(m.relative_to(search_path)) for m in matches[:100]]
        if len(matches) > 100:
            result_lines.append(f"\n... and {len(matches)-100} more")
        return {"success": True, "output": f"Found {len(matches)} matches:\n" + "\n".join(result_lines)}
    except Exception as e:
        return {"success": False, "output": f"Error finding files: {e}"}


def fs_copy(src_dst):
    parts = src_dst.split(":::", 1)
    if len(parts) != 2:
        return {"success": False, "output": "Format: source:::destination"}
    src, dst = parts
    try:
        if not src or not dst:
            return {"success": False, "output": "Both source and destination required"}
        s = Path(src).expanduser().resolve()
        d = Path(dst).expanduser().resolve()
        if not s.exists():
            return {"success": False, "output": f"Source not found: {src}"}
        d.parent.mkdir(parents=True, exist_ok=True)
        if s.is_dir():
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
        return {"success": True, "output": f"Copied {s} -> {d}"}
    except Exception as e:
        return {"success": False, "output": f"Error copying: {e}"}


def fs_move(src_dst):
    parts = src_dst.split(":::", 1)
    if len(parts) != 2:
        return {"success": False, "output": "Format: source:::destination"}
    src, dst = parts
    try:
        if not src or not dst:
            return {"success": False, "output": "Both source and destination required"}
        s = Path(src).expanduser().resolve()
        d = Path(dst).expanduser().resolve()
        if not s.exists():
            return {"success": False, "output": f"Source not found: {src}"}
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        return {"success": True, "output": f"Moved {s} -> {d}"}
    except Exception as e:
        return {"success": False, "output": f"Error moving: {e}"}


def proc_list(filter_name=""):
    try:
        if IS_WINDOWS:
            cmd = "Get-Process | Select-Object Name,Id,CPU,WorkingSet64 | Format-Table -AutoSize"
            if filter_name:
                safe_name = re.sub(r'[^a-zA-Z0-9_*]', '', filter_name)
                if safe_name:
                    cmd = f"Get-Process -Name '*{safe_name}*' | Select-Object Name,Id,CPU,WorkingSet64 | Format-Table -AutoSize"
            result = _run_cmd(cmd, timeout=15)
        else:
            cmd = "ps aux --sort=-%cpu"
            if filter_name:
                safe_name = re.sub(r'[^a-zA-Z0-9_]', '', filter_name)
                if safe_name:
                    cmd = f"ps aux | grep -i {safe_name} | grep -v grep"
            result = _run_cmd(cmd, timeout=15)
        return result
    except Exception as e:
        return {"success": False, "output": f"Error listing processes: {e}"}


def proc_kill(name_or_pid):
    try:
        if not name_or_pid or not str(name_or_pid).strip():
            return {"success": False, "output": "Empty process name or PID"}
        name_or_pid = str(name_or_pid).strip()
        critical_processes = {"systemd", "init", "kernel", "kthreadd", "sshd", "dbus", "pulseaudio", "Xorg"}
        if name_or_pid.isdigit():
            pid = int(name_or_pid)
            if pid <= 0:
                return {"success": False, "output": f"Invalid PID: {pid}"}
            if pid in (1, 2):
                return {"success": False, "output": f"Cannot kill critical system process (PID {pid})"}
            if IS_WINDOWS:
                result = _run_cmd(f"Stop-Process -Id {pid} -Force", timeout=15)
            else:
                result = _run_cmd(f"kill {pid}", timeout=15)
        else:
            safe_name = re.sub(r'[^a-zA-Z0-9_.\-]', '', name_or_pid)
            if not safe_name:
                return {"success": False, "output": f"Invalid process name: {name_or_pid}"}
            if safe_name.lower() in {p.lower() for p in critical_processes}:
                return {"success": False, "output": f"Cannot kill critical system process: {safe_name}"}
            if IS_WINDOWS:
                result = _run_cmd(f"Stop-Process -Name '{safe_name}' -Force", timeout=15)
            else:
                result = _run_cmd(f"killall {safe_name}", timeout=15)
        if result.get("success"):
            return {"success": True, "output": f"Killed process: {name_or_pid}"}
        return {"success": False, "output": f"Failed to kill {name_or_pid}: {result.get('output', 'Unknown error')}"}
    except Exception as e:
        return {"success": False, "output": f"Error killing process: {e}"}


def sys_cpu():
    try:
        info = {
            "platform": platform.system(),
            "processor": platform.processor(),
            "cores": os.cpu_count(),
        }
        if IS_LINUX:
            r = _run_cmd("cat /proc/cpuinfo | grep 'model name' | head -1", timeout=5)
            if r["success"]:
                info["model"] = r["output"].split(":", 1)[-1].strip()
            r = _run_cmd("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1", timeout=5)
            if r["success"]:
                info["usage_percent"] = r["output"].strip()
        elif IS_WINDOWS:
            r = _run_cmd("wmic cpu get LoadPercentage /value", timeout=5)
            if r["success"]:
                m = re.search(r'LoadPercentage=(\d+)', r["output"])
                if m:
                    info["usage_percent"] = m.group(1)
        elif IS_MACOS:
            r = _run_cmd("sysctl -n machdep.cpu.brand_string", timeout=5)
            if r["success"]:
                info["model"] = r["output"]
        lines = [f"  {k}: {v}" for k, v in info.items()]
        return {"success": True, "output": "CPU Information:\n" + "\n".join(lines)}
    except Exception as e:
        return {"success": False, "output": f"Error getting CPU info: {e}"}


def sys_ram():
    try:
        try:
            import psutil
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            lines = [
                f"  Total: {_human_size(mem.total)}",
                f"  Available: {_human_size(mem.available)}",
                f"  Used: {_human_size(mem.used)} ({mem.percent}%)",
                f"  Swap Total: {_human_size(swap.total)}",
                f"  Swap Used: {_human_size(swap.used)} ({swap.percent}%)",
            ]
            return {"success": True, "output": "RAM Information:\n" + "\n".join(lines)}
        except ImportError:
            pass
        if IS_WINDOWS:
            r = _run_cmd("wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /value", timeout=5)
            if r["success"]:
                total = re.search(r'TotalVisibleMemorySize=(\d+)', r["output"])
                free = re.search(r'FreePhysicalMemory=(\d+)', r["output"])
                if total and free:
                    t = int(total.group(1)) * 1024
                    f_val = int(free.group(1)) * 1024
                    return {"success": True, "output": f"RAM: {_human_size(f_val)} free / {_human_size(t)} total ({((t-f_val)/t)*100:.1f}% used)"}
        elif IS_LINUX:
            r = _run_cmd("free -h", timeout=5)
            return {"success": True, "output": f"RAM Information:\n{r['output']}"}
        return {"success": True, "output": "RAM info requires psutil or platform-specific commands"}
    except Exception as e:
        return {"success": False, "output": f"Error getting RAM info: {e}"}


def sys_gpu():
    try:
        if IS_WINDOWS:
            r = _run_cmd("wmic path win32_videocontroller get name,adapterram,driverversion /value", timeout=10)
            return {"success": True, "output": f"GPU Information:\n{r['output']}"}
        elif IS_LINUX:
            r = _run_cmd("lspci | grep -i 'vga\\|3d\\|display'", timeout=5)
            nvidia = _run_cmd("nvidia-smi --query-gpu=name,memory.total,temperature.gpu,utilization.gpu --format=csv,noheader", timeout=10)
            output = f"GPU Devices:\n{r['output']}"
            if nvidia["success"]:
                output += f"\n\nNVIDIA GPU Details:\n{nvidia['output']}"
            return {"success": True, "output": output}
        elif IS_MACOS:
            r = _run_cmd("system_profiler SPDisplaysDataType", timeout=10)
            return {"success": True, "output": f"GPU Information:\n{r['output']}"}
        return {"success": True, "output": "GPU detection not available for this platform"}
    except Exception as e:
        return {"success": False, "output": f"Error getting GPU info: {e}"}


def sys_disk(drive=""):
    try:
        if IS_LINUX:
            r = _run_cmd("df -h --output=source,size,used,avail,pcent,target | grep -v tmpfs", timeout=5)
            return {"success": True, "output": f"Disk Information:\n{r['output']}"}
        elif IS_WINDOWS:
            if drive:
                safe_drive = re.sub(r'[^a-zA-Z]', '', str(drive))
                r = _run_cmd(f"wmic logicaldisk where DeviceID='{safe_drive}:' get Size,FreeSpace,FileSystem /value", timeout=5)
            else:
                r = _run_cmd("wmic logicaldisk get DeviceID,Size,FreeSpace,FileSystem /value", timeout=5)
            return {"success": True, "output": f"Disk Information:\n{r['output']}"}
        return {"success": True, "output": "Disk info not available"}
    except Exception as e:
        return {"success": False, "output": f"Error getting disk info: {e}"}


def open_app(app_name):
    try:
        if not app_name or not str(app_name).strip():
            return {"success": False, "output": "Empty application name"}
        safe_name = re.sub(r'[^a-zA-Z0-9_.\- ]', '', str(app_name).strip())
        if not safe_name:
            return {"success": False, "output": f"Invalid application name: {app_name}"}
        if IS_WINDOWS:
            _run_cmd(f"Start-Process '{safe_name}'", timeout=10)
        elif IS_MACOS:
            _run_cmd(f"open -a '{safe_name}'", timeout=10)
        else:
            if shutil.which(safe_name.split()[0]):
                _run_cmd(f"nohup {safe_name} >/dev/null 2>&1 &", timeout=10)
            else:
                return {"success": False, "output": f"Application not found: {safe_name}"}
        return {"success": True, "output": f"Launched: {safe_name}"}
    except Exception as e:
        return {"success": False, "output": f"Error launching: {e}"}


def type_text(text):
    if not text:
        return {"success": False, "output": "Empty text"}
    text = str(text)
    try:
        if IS_WINDOWS:
            escaped = text.replace("'", "''")
            _run_cmd(
                f"Add-Type -AssemblyName System.Windows.Forms; "
                f"[System.Windows.Forms.SendKeys]::SendWait('{escaped}')",
                timeout=10,
            )
        elif IS_LINUX:
            if shutil.which("xdotool"):
                safe_text = text.replace("'", "'\\''")
                _run_cmd(f"xdotool type --clearmodifiers '{safe_text}'", timeout=10)
            elif shutil.which("xclip"):
                import subprocess as sp
                clip = sp.Popen(["xclip", "-selection", "clipboard"], stdin=sp.PIPE)
                clip.communicate(text.encode("utf-8"))
                _run_cmd("xdotool key ctrl+v", timeout=10)
            else:
                return {"success": False, "output": "No typing tool found. Install xdotool or xclip."}
        elif IS_MACOS:
            safe_text = text.replace('"', '\\"')
            _run_cmd(f"osascript -e 'tell application \"System Events\" to keystroke \"{safe_text}\"'", timeout=10)
        return {"success": True, "output": f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}"}
    except Exception as e:
        return {"success": False, "output": f"Error typing: {e}"}


def hotkey(keys):
    if not keys:
        return {"success": False, "output": "Empty hotkey"}
    try:
        key_list = [k.strip().lower() for k in str(keys).split("+")]
        key_list = [re.sub(r'[^a-z0-9]', '', k) for k in key_list]
        key_list = [k for k in key_list if k]
        if not key_list:
            return {"success": False, "output": "Invalid hotkey format"}
        if IS_WINDOWS:
            combo = "".join(f"{{{k.upper()}}}" for k in key_list)
            _run_cmd(
                f"Add-Type -AssemblyName System.Windows.Forms; "
                f"[System.Windows.Forms.SendKeys]::SendWait('{combo}')",
                timeout=10,
            )
        elif IS_LINUX:
            if shutil.which("xdotool"):
                _run_cmd(f"xdotool key {'+'.join(key_list)}", timeout=10)
            else:
                return {"success": False, "output": "xdotool not found. Install xdotool for hotkey support."}
        elif IS_MACOS:
            modifier_map = {"command": "command", "control": "control", "option": "option", "shift": "shift"}
            mods = "+".join(modifier_map.get(k, k) for k in key_list if k in modifier_map)
            non_mods = [k for k in key_list if k not in modifier_map]
            if non_mods and mods:
                key_str = f"keystroke \"{non_mods[0]}\" using {{{mods}}}"
            elif non_mods:
                key_str = f"keystroke \"{non_mods[0]}\""
            else:
                key_str = f"keystroke \"{keys}\""
            _run_cmd(f"osascript -e 'tell application \"System Events\" to {key_str}'", timeout=10)
        return {"success": True, "output": f"Sent hotkey: {keys}"}
    except Exception as e:
        return {"success": False, "output": f"Error sending hotkey: {e}"}


def net_ping(host, count=4):
    try:
        if not host or not str(host).strip():
            return {"success": False, "output": "Empty host"}
        safe_host = re.sub(r'[^a-zA-Z0-9._:-]', '', str(host).strip())
        if not safe_host:
            return {"success": False, "output": f"Invalid host: {host}"}
        flag = "-n" if IS_WINDOWS else "-c"
        r = _run_cmd(f"ping {flag} {count} {safe_host}", timeout=30)
        if r["success"]:
            return {"success": True, "output": r["output"]}
        return {"success": False, "output": f"Ping failed: {r['output']}"}
    except Exception as e:
        return {"success": False, "output": f"Error pinging: {e}"}


def screenshot():
    try:
        out_path = str(Path.home() / "gbloxkos_screenshot.png")
        if IS_WINDOWS:
            _run_cmd(
                f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; '
                f'$bmp = New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, '
                f'[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); '
                f'$gfx = [System.Drawing.Graphics]::FromImage($bmp); '
                f'$gfx.CopyFromScreen(0, 0, 0, 0, $bmp.Size); '
                f'$bmp.Save(\'{out_path}\')"',
                timeout=15,
            )
        elif IS_LINUX:
            result = _run_cmd(f"scrot '{out_path}'", timeout=10)
            if not result.get("success") or not Path(out_path).exists():
                result = _run_cmd(f"import -window root '{out_path}'", timeout=10)
            if not result.get("success") or not Path(out_path).exists():
                result = _run_cmd(f"gnome-screenshot -f '{out_path}'", timeout=10)
            if not result.get("success") or not Path(out_path).exists():
                result = _run_cmd(f"xfce4-screenshot -f -s '{out_path}'", timeout=10)
            if not result.get("success") or not Path(out_path).exists():
                result = _run_cmd(f"maim '{out_path}'", timeout=10)
        elif IS_MACOS:
            _run_cmd(f"screencapture '{out_path}'", timeout=10)
        if Path(out_path).exists():
            return {"success": True, "output": f"Screenshot saved: {out_path}", "path": out_path}
        return {"success": False, "output": "Screenshot tool not found. Install scrot, maim, or gnome-screenshot."}
    except Exception as e:
        return {"success": False, "output": f"Error taking screenshot: {e}"}


def ui_windows():
    try:
        if IS_LINUX:
            if shutil.which("wmctrl"):
                r = _run_cmd("wmctrl -l", timeout=5)
                if r["success"] and r["output"].strip():
                    return {"success": True, "output": f"Windows:\n{r['output']}"}
            if shutil.which("xdotool"):
                r = _run_cmd("xdotool search --name '' getwindowname", timeout=5)
                return {"success": True, "output": f"Windows:\n{r['output']}"}
            return {"success": True, "output": "Window listing requires wmctrl or xdotool"}
        elif IS_WINDOWS:
            r = _run_cmd(
                "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | "
                "Select-Object Id,ProcessName,MainWindowTitle | Format-Table -AutoSize",
                timeout=10,
            )
            return {"success": True, "output": f"Windows:\n{r['output']}"}
        return {"success": True, "output": "Window listing not available on this platform"}
    except Exception as e:
        return {"success": False, "output": f"Error listing windows: {e}"}


def ui_focus(window_name):
    try:
        if not window_name or not str(window_name).strip():
            return {"success": False, "output": "Empty window name"}
        safe_name = re.sub(r'[^a-zA-Z0-9 _.\-]', '', str(window_name).strip())
        if not safe_name:
            return {"success": False, "output": f"Invalid window name: {window_name}"}
        if IS_LINUX:
            if shutil.which("wmctrl"):
                _run_cmd(f"wmctrl -a '{safe_name}'", timeout=5)
            elif shutil.which("xdotool"):
                _run_cmd(f"xdotool search --name '{safe_name}' windowactivate", timeout=5)
            else:
                return {"success": False, "output": "wmctrl or xdotool required for window focus"}
        elif IS_WINDOWS:
            _run_cmd(
                f"$p = Get-Process | Where-Object {{$_.MainWindowTitle -like '*{safe_name}*'}} | Select-Object -First 1; "
                f"if ($p) {{ [Microsoft.VisualBasic.Interaction]::AppActivate($p.Id) }}",
                timeout=10,
            )
        return {"success": True, "output": f"Focused window: {safe_name}"}
    except Exception as e:
        return {"success": False, "output": f"Error focusing: {e}"}


def media_volume(action):
    try:
        if not action or not str(action).strip():
            return {"success": False, "output": "Empty volume action"}
        action = str(action).strip().lower()
        if IS_LINUX:
            if shutil.which("amixer"):
                if action == "up":
                    _run_cmd("amixer set Master 5%+", timeout=5)
                elif action == "down":
                    _run_cmd("amixer set Master 5%-", timeout=5)
                elif action == "mute":
                    _run_cmd("amixer set Master toggle", timeout=5)
                elif action.isdigit():
                    level = min(100, max(0, int(action)))
                    _run_cmd(f"amixer set Master {level}%", timeout=5)
                else:
                    return {"success": False, "output": f"Invalid volume action: {action}"}
            elif shutil.which("pactl"):
                if action == "up":
                    _run_cmd("pactl set-sink-volume @DEFAULT_SINK@ +5%", timeout=5)
                elif action == "down":
                    _run_cmd("pactl set-sink-volume @DEFAULT_SINK@ -5%", timeout=5)
                elif action == "mute":
                    _run_cmd("pactl set-sink-mute @DEFAULT_SINK@ toggle", timeout=5)
                elif action.isdigit():
                    level = min(100, max(0, int(action)))
                    _run_cmd(f"pactl set-sink-volume @DEFAULT_SINK@ {level}%", timeout=5)
                else:
                    return {"success": False, "output": f"Invalid volume action: {action}"}
            else:
                return {"success": False, "output": "No volume control found (amixer or pactl required)"}
        elif IS_WINDOWS:
            if action == "up":
                _run_cmd("$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]175)", timeout=5)
            elif action == "down":
                _run_cmd("$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]174)", timeout=5)
            elif action == "mute":
                _run_cmd("$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]173)", timeout=5)
            else:
                return {"success": False, "output": f"Invalid volume action: {action}"}
        return {"success": True, "output": f"Volume: {action}"}
    except Exception as e:
        return {"success": False, "output": f"Error controlling volume: {e}"}


def media_key(action):
    try:
        if not action or not str(action).strip():
            return {"success": False, "output": "Empty media action"}
        action = str(action).strip().lower()
        key_map = {
            "play": "XF86AudioPlay", "pause": "XF86AudioPause",
            "next": "XF86AudioNext", "prev": "XF86AudioPrev",
            "stop": "XF86AudioStop",
        }
        if IS_LINUX:
            if shutil.which("xdotool"):
                xkey = key_map.get(action)
                if not xkey:
                    return {"success": False, "output": f"Unknown media action: {action}"}
                _run_cmd(f"xdotool key {xkey}", timeout=5)
            else:
                return {"success": False, "output": "xdotool not found. Install xdotool for media key support."}
        elif IS_WINDOWS:
            wkey = {"play": "_play", "pause": "play", "next": "next_track", "prev": "prev_track", "stop": "stop_media"}.get(action)
            if not wkey:
                return {"success": False, "output": f"Unknown media action: {action}"}
            _run_cmd(f"$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys('{{{wkey}}}')", timeout=5)
        return {"success": True, "output": f"Media: {action}"}
    except Exception as e:
        return {"success": False, "output": f"Error with media key: {e}"}


def automation(instructions):
    if not instructions or not str(instructions).strip():
        return {"success": False, "output": "Empty automation instructions"}
    instructions = str(instructions)
    lower = instructions.lower()
    try:
        from web_search import open_in_browser, web_search
    except ImportError:
        return {"success": False, "output": "web_search module not available"}
    if any(w in lower for w in ["open browser", "browse to", "open url", "go to http"]):
        url_match = re.search(r'https?://\S+', instructions)
        if url_match:
            return open_in_browser(url_match.group())
    if any(w in lower for w in ["search for", "google", "look up", "find online"]):
        query = re.sub(r'(?i)(search for|google|look up|find online)\s*', '', instructions).strip()
        if query:
            return web_search(query)
    if any(w in lower for w in ["open app", "launch", "start program"]):
        app = re.sub(r'(?i)(open app|launch|start program)\s*', '', instructions).strip()
        if app:
            return open_app(app)
    return {"success": False, "output": f"Automation cannot determine action for: {instructions[:200]}. Use a specific tool instead."}


def _human_size(size_bytes):
    try:
        size_bytes = int(size_bytes)
    except (TypeError, ValueError):
        return "0B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}PB"


def _web_search_tool(query):
    from web_search import web_search as _ws
    result = _ws(query)
    if result.get("results"):
        lines = [f"Search results for: {query}\n"]
        for i, r in enumerate(result["results"], 1):
            lines.append(f"{i}. {r['title']}")
            lines.append(f"   URL: {r['url']}")
            if r.get("snippet"):
                lines.append(f"   {r['snippet']}")
            lines.append("")
        return {"success": True, "output": "\n".join(lines)}
    return {"success": False, "output": result.get("error", "No results found")}


def _web_browse_tool(url):
    from web_search import browse_url
    result = browse_url(url)
    if result.get("content"):
        output = f"Page: {result.get('title', url)}\nURL: {url}\nStatus: {result.get('status', 'N/A')}\n\n{result['content']}"
        return {"success": True, "output": output}
    return {"success": False, "output": result.get("error", "Failed to browse")}


def _web_open_tool(url):
    from web_search import open_in_browser
    return open_in_browser(url)


def _fs_find_split(val):
    val = str(val) if val else ""
    if " in " in val:
        parts = val.split(" in ", 1)
        return parts[0], parts[1]
    return val, "."


TOOL_REGISTRY = {
    "cmd_exec": lambda val: cmd_exec(val),
    "powershell": lambda val: powershell(val),
    "fs_read": lambda val: fs_read(val),
    "fs_write": lambda val: fs_write(val),
    "fs_append": lambda val: fs_append(val),
    "fs_delete": lambda val: fs_delete(val),
    "fs_list": lambda val: fs_list(val),
    "fs_find": lambda val: fs_find(*_fs_find_split(val)),
    "fs_copy": lambda val: fs_copy(val),
    "fs_move": lambda val: fs_move(val),
    "proc_list": lambda val: proc_list(val),
    "proc_kill": lambda val: proc_kill(val),
    "sys_cpu": lambda val: sys_cpu(),
    "sys_ram": lambda val: sys_ram(),
    "sys_gpu": lambda val: sys_gpu(),
    "sys_disk": lambda val: sys_disk(val),
    "open_app": lambda val: open_app(val),
    "type_text": lambda val: type_text(val),
    "hotkey": lambda val: hotkey(val),
    "net_ping": lambda val: net_ping(val),
    "screenshot": lambda val: screenshot(),
    "ui_windows": lambda val: ui_windows(),
    "ui_focus": lambda val: ui_focus(val),
    "media_volume": lambda val: media_volume(val),
    "media_key": lambda val: media_key(val),
    "automation": lambda val: automation(val),
    "web_search": lambda val: _web_search_tool(val),
    "web_browse": lambda val: _web_browse_tool(val),
    "web_open": lambda val: _web_open_tool(val),
}


def execute_tool(tool_name, value=""):
    tool_func = TOOL_REGISTRY.get(tool_name)
    if not tool_func:
        return {"success": False, "output": f"Unknown tool: {tool_name}"}
    try:
        return tool_func(value or "")
    except Exception as e:
        logger.exception(f"Tool execution error: {tool_name}")
        return {"success": False, "output": f"Tool error ({tool_name}): {e}"}
