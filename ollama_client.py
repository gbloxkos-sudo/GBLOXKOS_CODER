"""Ollama API client with auto-detection, retry, health checks."""
import json
import time
import logging
import threading

try:
    import requests as _requests
    from requests.adapters import HTTPAdapter
    from requests.exceptions import ConnectionError as _ConnectionError
    from requests.exceptions import Timeout as _Timeout
    from requests.exceptions import RequestException
except ImportError:
    _requests = None
    _ConnectionError = type('ConnectionError', (Exception,), {})
    _Timeout = type('Timeout', (Exception,), {})
    RequestException = type('RequestException', (Exception,), {})

logger = logging.getLogger("gbloxkos.ollama")

OLLAMA_BASE = "http://127.0.0.1:11434"
MAX_RETRIES = 3
RETRY_DELAY = 2.0
REQUEST_TIMEOUT = 120
STREAM_CHUNK_TIMEOUT = 30


class OllamaClient:
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
        self.base_url = OLLAMA_BASE
        self.models = []
        self._healthy = False
        self._last_health_check = 0
        self._health_lock = threading.Lock()
        self._request_lock = threading.Lock()
        self._session = None
        self._session_lock = threading.Lock()
        self._abort = False
        self._abort_lock = threading.Lock()

    def _get_session(self):
        if _requests is None:
            raise ImportError("requests library not installed: pip install requests")
        with self._session_lock:
            if self._session is None:
                self._session = _requests.Session()
                self._session.headers.update({"Content-Type": "application/json"})
                adapter = HTTPAdapter(
                    max_retries=0,
                    pool_connections=4,
                    pool_maxsize=4,
                )
                self._session.mount("http://", adapter)
                self._session.mount("https://", adapter)
            return self._session

    def abort(self):
        with self._abort_lock:
            self._abort = True
        self._reset_session()

    def reset_abort(self):
        with self._abort_lock:
            self._abort = False

    def is_aborted(self):
        with self._abort_lock:
            return self._abort

    def _reset_session(self):
        with self._session_lock:
            if self._session:
                try:
                    self._session.close()
                except Exception:
                    pass
                self._session = None
            self._healthy = False
            self._last_health_check = 0

    def _get_requests_module(self):
        if _requests is None:
            raise ImportError("requests library not installed: pip install requests")
        return _requests

    def health_check(self):
        now = time.time()
        with self._health_lock:
            if now - self._last_health_check < 10:
                return self._healthy
        try:
            req = self._get_requests_module()
            r = req.get(f"{self.base_url}/api/tags", timeout=5)
            healthy = r.status_code == 200
            with self._health_lock:
                self._healthy = healthy
                self._last_health_check = now
            return healthy
        except (_ConnectionError, _Timeout):
            with self._health_lock:
                self._healthy = False
                self._last_health_check = now
            return False
        except Exception:
            with self._health_lock:
                self._healthy = False
                self._last_health_check = now
            return False

    def list_models(self, force=False):
        if self.models and not force:
            return list(self.models)
        try:
            s = self._get_session()
            r = s.get(f"{self.base_url}/api/tags", timeout=10)
            if r.status_code != 200:
                logger.warning(f"Ollama list failed: {r.status_code}")
                return list(self.models)

            data = r.json()
            models = []
            for m in data.get("models", []):
                name = m.get("name", "")
                if not name:
                    continue
                size = m.get("size", 0)
                modified = m.get("modified_at", "")
                family = m.get("details", {}).get("family", "")
                params = m.get("details", {}).get("parameter_size", "")
                quant = m.get("details", {}).get("quantization_level", "")

                display_name = _make_display_name(name)
                is_code = any(kw in name.lower() for kw in ["code", "coder", "starcoder", "granite-code", "yi-coder"])
                is_embedding = "embed" in name.lower()

                models.append({
                    "name": name,
                    "display_name": display_name,
                    "size": size,
                    "size_human": _human_size(size),
                    "modified": modified,
                    "family": family,
                    "params": params,
                    "quant": quant,
                    "is_code_model": is_code,
                    "is_embedding": is_embedding,
                })

            models.sort(key=lambda x: (not x["is_code_model"], x["display_name"]))
            with self._request_lock:
                self.models = models
            logger.info(f"Detected {len(models)} Ollama models")
            return list(models)
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return list(self.models)

    def get_model_names(self, include_embeddings=False):
        self.list_models()
        with self._request_lock:
            return [
                m["name"] for m in self.models
                if include_embeddings or not m["is_embedding"]
            ]

    def get_model_info(self, name):
        self.list_models()
        with self._request_lock:
            for m in self.models:
                if m["name"] == name:
                    return dict(m)
        return None

    def chat(self, model, messages, stream=False, options=None):
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        if options:
            payload["options"] = options

        self.reset_abort()

        for attempt in range(MAX_RETRIES):
            try:
                if self.is_aborted():
                    return {"error": "Aborted"}

                s = self._get_session()
                r = s.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                    stream=True,
                )

                if r.status_code != 200:
                    error_msg = f"Ollama returned {r.status_code}: {r.text[:200]}"
                    logger.warning(error_msg)
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                    else:
                        return {"error": error_msg}

                full_content = ""
                for line in r.iter_lines():
                    if self.is_aborted():
                        return {"error": "Aborted"}
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            full_content += chunk["message"]["content"]
                        if chunk.get("done", False):
                            return {
                                "model": chunk.get("model", model),
                                "created_at": chunk.get("created_at", ""),
                                "message": {"role": "assistant", "content": full_content},
                                "done": True,
                            }
                    except json.JSONDecodeError:
                        continue

                return {"message": {"role": "assistant", "content": full_content}, "done": True}

            except _ConnectionError:
                msg = f"Cannot connect to Ollama at {self.base_url}. Is it running?"
                logger.error(msg)
                self._reset_session()
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    return {"error": msg}
            except _Timeout:
                msg = f"Ollama request timed out ({REQUEST_TIMEOUT}s)"
                logger.warning(msg)
                self._reset_session()
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return {"error": msg}
            except Exception as e:
                msg = f"Ollama error: {e}"
                logger.exception(msg)
                self._reset_session()
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return {"error": msg}

        return {"error": "Max retries exceeded"}

    def generate(self, model, prompt, system=None, stream=False, options=None):
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        self.reset_abort()

        for attempt in range(MAX_RETRIES):
            try:
                if self.is_aborted():
                    return {"error": "Aborted"}

                s = self._get_session()
                r = s.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                    stream=True,
                )

                if r.status_code != 200:
                    error_msg = f"Ollama returned {r.status_code}"
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))
                    else:
                        return {"error": error_msg}

                full_response = ""
                for line in r.iter_lines():
                    if self.is_aborted():
                        return {"error": "Aborted"}
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            full_response += chunk["response"]
                        if chunk.get("done", False):
                            return {"response": full_response, "done": True}
                    except json.JSONDecodeError:
                        continue

                return {"response": full_response, "done": True}

            except _ConnectionError:
                self._reset_session()
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    return {"error": f"Cannot connect to Ollama at {self.base_url}"}
            except _Timeout:
                self._reset_session()
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return {"error": f"Ollama request timed out ({REQUEST_TIMEOUT}s)"}
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return {"error": str(e)}

        return {"error": "Max retries exceeded"}

    def pull_model(self, model_name, progress_callback=None):
        try:
            s = self._get_session()
            r = s.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=3600,
            )
            for line in r.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if progress_callback:
                            progress_callback(data)
                    except json.JSONDecodeError:
                        continue
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_model(self, model_name):
        try:
            s = self._get_session()
            r = s.delete(
                f"{self.base_url}/api/delete",
                json={"name": model_name},
            )
            return {"success": r.status_code == 200}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def show_model(self, model_name):
        try:
            s = self._get_session()
            r = s.post(
                f"{self.base_url}/api/show",
                json={"name": model_name},
            )
            if r.status_code == 200:
                return r.json()
            return {"error": f"Status {r.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def is_healthy(self):
        with self._health_lock:
            return self._healthy


def _make_display_name(model_name):
    name = model_name.split(":")[0] if ":" in model_name else model_name
    parts = name.replace("-", " ").replace("_", " ").split("/")
    if len(parts) > 1:
        name = parts[-1]
    else:
        name = parts[0]
    words = name.split()
    result = " ".join(w.capitalize() for w in words)
    return result


def _human_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


_client = None
_client_lock = threading.Lock()


def get_client():
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = OllamaClient()
    return _client
