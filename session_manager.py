"""Chat session persistence manager for GBLOXKOS_CODER."""
import json
import uuid
import logging
import threading
import tempfile
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("gbloxkos.session")

DATA_DIR = Path(__file__).parent / "chat_history"
DATA_DIR.mkdir(exist_ok=True)

SESSIONS_FILE = DATA_DIR / "sessions.json"
MAX_SESSIONS = 200
MAX_MESSAGES_PER_SESSION = 500
MAX_MESSAGE_LENGTH = 100000


class SessionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.sessions = {}
        self.current_session_id = None
        self._data_lock = threading.RLock()
        self._load()

    def _load(self):
        try:
            if SESSIONS_FILE.exists():
                with open(SESSIONS_FILE, "r") as f:
                    data = json.load(f)
                self.sessions = data.get("sessions", {})
                self.current_session_id = data.get("current_id")
                if self.current_session_id and self.current_session_id not in self.sessions:
                    self.current_session_id = None
                self._enforce_limits()
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load sessions (corrupt data): {e}")
            self.sessions = {}
            self.current_session_id = None
            self._backup_corrupt_file()
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            self.sessions = {}
            self.current_session_id = None

    def _enforce_limits(self):
        if len(self.sessions) > MAX_SESSIONS:
            sorted_sessions = sorted(
                self.sessions.values(),
                key=lambda s: s.get("updated", ""),
                reverse=True,
            )
            keep_ids = {s["id"] for s in sorted_sessions[:MAX_SESSIONS]}
            self.sessions = {k: v for k, v in self.sessions.items() if k in keep_ids}

        for sid, session in self.sessions.items():
            msgs = session.get("messages", [])
            if len(msgs) > MAX_MESSAGES_PER_SESSION:
                session["messages"] = msgs[-MAX_MESSAGES_PER_SESSION:]
            for msg in session["messages"]:
                content = msg.get("content", "")
                if content is None:
                    msg["content"] = ""
                elif isinstance(content, str) and len(content) > MAX_MESSAGE_LENGTH:
                    msg["content"] = content[:MAX_MESSAGE_LENGTH] + "\n\n[Message truncated]"

    def _backup_corrupt_file(self):
        try:
            if SESSIONS_FILE.exists():
                backup = SESSIONS_FILE.with_suffix(f".corrupt.{int(datetime.now().timestamp())}")
                SESSIONS_FILE.rename(backup)
                logger.info(f"Backed up corrupt sessions file to {backup}")
        except Exception:
            pass

    def _save(self):
        try:
            data = {
                "sessions": self.sessions,
                "current_id": self.current_session_id,
            }
            fd, tmp_path = tempfile.mkstemp(
                dir=str(SESSIONS_FILE.parent),
                prefix=".sessions_",
                suffix=".tmp",
            )
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(data, f, indent=2, default=str)
                os.replace(tmp_path, str(SESSIONS_FILE))
                logger.debug("Sessions saved successfully")
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def new_session(self, title=None):
        with self._data_lock:
            sid = str(uuid.uuid4())[:12]
            now = datetime.now().isoformat()
            if not title:
                title = f"Chat {datetime.now().strftime('%b %d, %H:%M')}"
            self.sessions[sid] = {
                "id": sid,
                "title": title,
                "created": now,
                "updated": now,
                "model": "",
                "messages": [],
            }
            self.current_session_id = sid
            self._enforce_limits()
            self._save()
            return sid

    def get_current(self):
        with self._data_lock:
            if not self.current_session_id or self.current_session_id not in self.sessions:
                return None
            return dict(self.sessions[self.current_session_id])

    def set_current(self, session_id):
        with self._data_lock:
            if session_id in self.sessions:
                self.current_session_id = session_id
                self._save()
                return True
            return False

    def add_message(self, session_id, role, content, metadata=None):
        with self._data_lock:
            if session_id not in self.sessions:
                return False
            if content is None:
                return False
            content_str = str(content)
            if not content_str.strip() and content_str != "":
                return False
            if len(content_str) > MAX_MESSAGE_LENGTH:
                content_str = content_str[:MAX_MESSAGE_LENGTH] + "\n\n[Message truncated]"
            msg = {
                "id": str(uuid.uuid4())[:8],
                "role": role,
                "content": content_str,
                "timestamp": datetime.now().isoformat(),
            }
            if metadata and isinstance(metadata, dict):
                msg["metadata"] = metadata
            self.sessions[session_id]["messages"].append(msg)
            if len(self.sessions[session_id]["messages"]) > MAX_MESSAGES_PER_SESSION:
                self.sessions[session_id]["messages"] = self.sessions[session_id]["messages"][-MAX_MESSAGES_PER_SESSION:]
            self.sessions[session_id]["updated"] = datetime.now().isoformat()
            self._save()
            return True

    def get_messages(self, session_id, limit=None):
        with self._data_lock:
            if session_id not in self.sessions:
                return []
            msgs = self.sessions[session_id].get("messages", [])
            if limit:
                return list(msgs[-limit:])
            return list(msgs)

    def get_all_sessions(self, sort_by="updated"):
        with self._data_lock:
            sessions = list(self.sessions.values())
        if sort_by == "updated":
            sessions.sort(key=lambda s: s.get("updated", ""), reverse=True)
        elif sort_by == "created":
            sessions.sort(key=lambda s: s.get("created", ""), reverse=True)
        elif sort_by == "title":
            sessions.sort(key=lambda s: s.get("title", "").lower())
        return sessions

    def rename_session(self, session_id, new_title):
        with self._data_lock:
            if session_id in self.sessions:
                self.sessions[session_id]["title"] = str(new_title)[:200] if new_title else "Untitled"
                self._save()
                return True
            return False

    def delete_session(self, session_id):
        with self._data_lock:
            if session_id not in self.sessions:
                return False
            del self.sessions[session_id]
            if self.current_session_id == session_id:
                if self.sessions:
                    self.current_session_id = next(iter(self.sessions))
                else:
                    self.current_session_id = None
            self._save()
            return True

    def clear_all(self):
        with self._data_lock:
            self.sessions = {}
            self.current_session_id = None
            self._save()
            return True

    def set_model(self, session_id, model_name):
        with self._data_lock:
            if session_id in self.sessions:
                self.sessions[session_id]["model"] = str(model_name) if model_name else ""
                self._save()

    def get_ollama_messages(self, session_id, limit=50):
        msgs = self.get_messages(session_id, limit)
        result = []
        for m in msgs:
            if not isinstance(m, dict):
                continue
            role = m.get("role", "user")
            content = m.get("content", "")
            if role in ("user", "assistant", "system") and content:
                content_str = str(content).strip()
                if content_str:
                    result.append({"role": role, "content": content_str})
        return result

    def export_session(self, session_id, fmt="json"):
        with self._data_lock:
            if session_id not in self.sessions:
                return None
            session = dict(self.sessions[session_id])
            session["messages"] = list(session.get("messages", []))
        try:
            if fmt == "json":
                return json.dumps(session, indent=2, default=str)
            elif fmt == "text":
                lines = [
                    f"Session: {session.get('title', 'Untitled')}",
                    f"Created: {session.get('created', 'N/A')}",
                    "=" * 60,
                    "",
                ]
                for m in session.get("messages", []):
                    role = m.get("role", "unknown").upper()
                    ts = m.get("timestamp", "")
                    content = m.get("content", "")
                    if content is None:
                        content = ""
                    lines.append(f"[{ts}] {role}:")
                    lines.append(str(content))
                    lines.append("")
                return "\n".join(lines)
        except Exception as e:
            logger.error(f"Export error: {e}")
            return None
        return None

    def search_sessions(self, query):
        if not query or not str(query).strip():
            return []
        query_lower = str(query).lower()
        results = []
        with self._data_lock:
            for sid, session in self.sessions.items():
                title_match = query_lower in str(session.get("title", "")).lower()
                msg_match = any(
                    query_lower in str(m.get("content", "")).lower()
                    for m in session.get("messages", [])
                    if m.get("content") is not None
                )
                if title_match or msg_match:
                    results.append(dict(session))
        return results

    def get_stats(self):
        with self._data_lock:
            total_sessions = len(self.sessions)
            total_messages = sum(len(s.get("messages", [])) for s in self.sessions.values())
            total_chars = sum(
                len(m.get("content", ""))
                for s in self.sessions.values()
                for m in s.get("messages", [])
            )
            current = self.current_session_id
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_characters": total_chars,
            "current_session": current,
        }


_manager = None
_manager_lock = threading.Lock()


def get_session_manager():
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager = SessionManager()
    return _manager
