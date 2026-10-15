"""AI Engine - expert coder brain with tool execution loop."""
import logging
import threading
import time
from config import SYSTEM_PROMPT
import config as _config
from ollama_client import get_client
from protocol_parser import split_protocol, extract_tool_calls, build_display_text
from tools import execute_tool

logger = logging.getLogger("gbloxkos.ai")

TOOL_EXECUTION_TIMEOUT = 60
MAX_HISTORY_MESSAGES = 50
MAX_RESPONSE_LENGTH = 50000
MAX_TOOL_RETRIES = 3


class AIEngine:
    def __init__(self, model=None):
        self.ollama = get_client()
        self.model = model or _config.DEFAULT_MODEL
        self.system_prompt = SYSTEM_PROMPT
        self._abort = False
        self._abort_lock = threading.Lock()
        self._chat_lock = threading.Lock()
        self._model_lock = threading.Lock()

    def abort(self):
        with self._abort_lock:
            self._abort = True
        try:
            self.ollama.abort()
        except Exception:
            pass

    def reset_abort(self):
        with self._abort_lock:
            self._abort = False
        try:
            self.ollama.reset_abort()
        except Exception:
            pass

    def is_aborted(self):
        with self._abort_lock:
            return self._abort

    def set_model(self, model):
        if model:
            with self._model_lock:
                self.model = model

    def get_model(self):
        with self._model_lock:
            return self.model

    def _validate_model(self):
        model = self.get_model()
        try:
            available = self.ollama.get_model_names()
        except Exception as e:
            logger.warning(f"Failed to get model list: {e}")
            return bool(model)

        if not model:
            if available:
                self.set_model(available[0])
                logger.warning(f"No model set, using fallback: {available[0]}")
                return True
            return False

        if available and model not in available:
            logger.warning(f"Model '{model}' not found in available models. Available: {available[:5]}")
            if available:
                self.set_model(available[0])
                logger.info(f"Falling back to model: {available[0]}")
                return True
            return False
        return True

    def chat(self, user_message, history=None, on_tool_call=None, on_thinking=None):
        # Use blocking lock with timeout to prevent indefinite blocking
        if not self._chat_lock.acquire(timeout=5.0):
            return {
                "response": "Already processing a request. Please wait for the current response.",
                "tool_calls": [],
                "raw": "",
            }
        try:
            return self._chat_inner(user_message, history, on_tool_call, on_thinking)
        finally:
            self._chat_lock.release()

    def _chat_inner(self, user_message, history, on_tool_call, on_thinking):
        self.reset_abort()

        if not user_message or not str(user_message).strip():
            return {
                "response": "Please provide a message.",
                "tool_calls": [],
                "raw": "",
            }

        if not self._validate_model():
            return {
                "response": "No AI models available. Please install a model with: ollama pull qwen2.5-coder",
                "tool_calls": [],
                "raw": "",
            }

        messages = [{"role": "system", "content": self.system_prompt}]

        if history:
            for msg in history[-MAX_HISTORY_MESSAGES:]:
                if not isinstance(msg, dict):
                    continue
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    content_str = str(content).strip()
                    if content_str and not content_str.startswith("Error:"):
                        messages.append({"role": role, "content": content_str})

        messages.append({"role": "user", "content": str(user_message).strip()})

        if on_thinking:
            try:
                on_thinking("Thinking...")
            except Exception:
                pass

        model = self.get_model()
        try:
            response = self.ollama.chat(
                model=model,
                messages=messages,
                stream=True,  # Always use streaming for better handling
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_ctx": 8192,
                    "num_predict": 4096,
                },
            )
        except Exception as e:
            logger.error(f"Ollama chat call failed: {e}")
            return {"response": f"Error communicating with Ollama: {e}", "tool_calls": [], "raw": ""}

        if self.is_aborted():
            return {"response": "Generation aborted.", "tool_calls": [], "raw": ""}

        if not isinstance(response, dict):
            return {"response": "Invalid response from model.", "tool_calls": [], "raw": ""}

        if "error" in response:
            return {"response": f"Error: {response['error']}", "tool_calls": [], "raw": ""}

        raw_content = ""
        try:
            msg_obj = response.get("message")
            if isinstance(msg_obj, dict):
                raw_content = msg_obj.get("content", "") or ""
            elif isinstance(msg_obj, str):
                raw_content = msg_obj
        except (AttributeError, KeyError, TypeError):
            pass

        if not raw_content:
            try:
                raw_content = response.get("response", "") or ""
            except Exception:
                pass

        if not raw_content:
            raw_content = str(response) if response else ""

        raw_content = raw_content.strip()
        if not raw_content:
            return {"response": "No response from model.", "tool_calls": [], "raw": ""}

        if len(raw_content) > MAX_RESPONSE_LENGTH:
            raw_content = raw_content[:MAX_RESPONSE_LENGTH] + "\n\n[Response truncated]"

        tool_calls = extract_tool_calls(raw_content)
        display_text = build_display_text(raw_content)

        if on_tool_call:
            for tc in tool_calls:
                if self.is_aborted():
                    break
                tool_name = tc["tool"]
                tool_value = tc["value"]
                try:
                    on_tool_call(tool_name, tool_value)
                except Exception:
                    pass

        tool_results = []
        for tc in tool_calls:
            if self.is_aborted():
                break
            tool_name = tc["tool"]
            tool_value = tc["value"]
            tool_head = tc["head"]

            if tool_name in ("msg", "message", "reply"):
                continue
            if tool_name == "canvas":
                continue
            if tool_name == "generate-head":
                continue

            result = None
            for attempt in range(MAX_TOOL_RETRIES):
                if self.is_aborted():
                    break
                try:
                    result = execute_tool(tool_name, tool_value)
                    if result and result.get("success"):
                        break
                    else:
                        logger.warning(f"Tool {tool_name} attempt {attempt + 1} failed: {result.get('output', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Tool execution failed for {tool_name} (attempt {attempt + 1}): {e}")
                    result = {"success": False, "output": f"Tool error: {e}"}

            if result is None:
                result = {"success": False, "output": f"Tool '{tool_name}' failed after {MAX_TOOL_RETRIES} attempts"}

            if not isinstance(result, dict):
                result = {"success": False, "output": str(result) if result else "Empty result"}

            tool_results.append({
                "tool": tool_name,
                "head": tool_head,
                "value": tool_value,
                "result": result,
            })

            if on_tool_call:
                try:
                    on_tool_call(f"result:{tool_name}", result.get("output", "")[:500])
                except Exception:
                    pass

        final_response = display_text if display_text else raw_content

        if not final_response.strip() and tool_results:
            result_texts = []
            for tr in tool_results:
                output = tr["result"].get("output", "")
                if output:
                    truncated = output[:500] + "..." if len(output) > 500 else output
                    result_texts.append(f"[{tr['tool']}] {truncated}")
            final_response = "\n\n".join(result_texts) if result_texts else "Task completed."

        final_response = final_response.strip()
        if not final_response:
            final_response = "I've processed your request."

        return {
            "response": final_response,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "raw": raw_content,
        }

    def code_review(self, code, language=""):
        if not code or not str(code).strip():
            return {"response": "No code provided for review.", "tool_calls": [], "raw": ""}
        prompt = f"Review this{' ' + language if language else ''} code for bugs, improvements, and best practices:\n\n```\n{code}\n```"
        return self.chat(prompt)

    def explain_code(self, code, language=""):
        if not code or not str(code).strip():
            return {"response": "No code provided to explain.", "tool_calls": [], "raw": ""}
        prompt = f"Explain this{' ' + language if language else ''} code in detail, line by line:\n\n```\n{code}\n```"
        return self.chat(prompt)

    def debug_code(self, code, error_msg="", language=""):
        if not code or not str(code).strip():
            return {"response": "No code provided to debug.", "tool_calls": [], "raw": ""}
        prompt = f"Debug this{' ' + language if language else ''} code"
        if error_msg:
            prompt += f". Error: {error_msg}"
        prompt += f":\n\n```\n{code}\n```"
        return self.chat(prompt)

    def generate_code(self, description, language="", context=""):
        if not description or not str(description).strip():
            return {"response": "Please provide a description for code generation.", "tool_calls": [], "raw": ""}
        prompt = f"Write complete, production-ready {language + ' ' if language else ''}code for: {description}"
        if context:
            prompt += f"\n\nContext: {context}"
        prompt += "\n\nProvide the full implementation. Use the canvas tool to send the code to the editor."
        return self.chat(prompt)

    def refactor_code(self, code, language=""):
        if not code or not str(code).strip():
            return {"response": "No code provided to refactor.", "tool_calls": [], "raw": ""}
        prompt = f"Refactor this{' ' + language if language else ''} code for better readability, performance, and maintainability:\n\n```\n{code}\n```"
        prompt += "\n\nProvide the improved version. Use the canvas tool to send the refactored code."
        return self.chat(prompt)

    def ask_about_web(self, question, search_results):
        if not question or not str(question).strip():
            return {"response": "Please provide a question.", "tool_calls": [], "raw": ""}
        prompt = f"Based on these search results, answer the question: {question}\n\nSearch Results:\n{search_results}"
        return self.chat(prompt)


_engine = None
_engine_lock = threading.Lock()


def get_engine(model=None):
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = AIEngine(model)
        elif model:
            _engine.set_model(model)
        return _engine
