"""Enhanced protocol parser for GBLOXKOS_CODER tool-call protocol."""
import re


def _normalize(s):
    if not s:
        return ""
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace('\\"', '"').replace("\\'", "'")
    s = s.replace("\\n", "\n").replace("\\t", "\t")
    s = s.replace("\\\\", "\\")
    return s.strip()


_DQ_STRING = r'"((?:[^"\\]|\\.)*)"'
_SQ_STRING = r"'((?:[^'\\]|\\.)*)'"

_TOOL_NAME_DQ = rf'//\s*tool\s*=\s*{_DQ_STRING}'
_TOOL_NAME_SQ = rf"//\s*tool\s*=\s*{_SQ_STRING}"

_HEAD_DQ = r'\s+head\s*=\s*"' + r'((?:[^"\\]|\\.)*)' + r'"'
_HEAD_SQ = r"\s+head\s*=\s*'" + r"((?:[^'\\]|\\.)*)" + r"'"

_VALUE_DQ = r'\s+value\s*=\s*"' + r'((?:[^"\\]|\\.)*)' + r'"'
_VALUE_SQ = r"\s+value\s*=\s*'" + r"((?:[^'\\]|\\.)*)" + r"'"

_TOOL_ONLY_RE = re.compile(
    rf"(?:{_TOOL_NAME_DQ}|{_TOOL_NAME_SQ})"
    rf"(?:{_HEAD_DQ}|{_HEAD_SQ})?"
    rf"(?:{_VALUE_DQ}|{_VALUE_SQ})?",
    re.DOTALL,
)

_JUNK_LINE_RE = re.compile(r"^\s*[/\\]{2,}\s*$", re.MULTILINE)


def parse_tool_chunk(chunk):
    if not chunk:
        return None
    chunk = chunk.strip()
    if not chunk.startswith("//"):
        return None
    m = _TOOL_ONLY_RE.search(chunk)
    if not m:
        return None
    tool = _normalize(m.group(1) or m.group(2) or "")
    head = _normalize(m.group(3) or m.group(4) or "")
    value = _normalize(m.group(5) or m.group(6) or "")
    if not tool:
        return None
    return (tool, head, value)


def split_protocol(raw_text):
    if not raw_text:
        return []

    text = _JUNK_LINE_RE.sub("", raw_text)
    segments = []

    tool_matches = list(_TOOL_ONLY_RE.finditer(text))

    last_end = 0
    for m in tool_matches:
        start = m.start()
        if start > last_end:
            pre = text[last_end:start].strip()
            if pre:
                segments.append(("text", pre, "", ""))

        tool = _normalize(m.group(1) or m.group(2) or "")
        head = _normalize(m.group(3) or m.group(4) or "")
        value = _normalize(m.group(5) or m.group(6) or "")
        if tool:
            segments.append(("tool", tool, head, value))
        last_end = m.end()

    if last_end < len(text):
        trailing = text[last_end:].strip()
        if trailing:
            segments.append(("text", trailing, "", ""))

    if not segments:
        stripped = text.strip()
        if stripped:
            segments.append(("text", stripped, "", ""))

    # Filter out empty text segments
    filtered_segments = []
    for seg in segments:
        if seg[0] == "text" and not seg[1].strip():
            continue
        if seg[0] == "tool" and not seg[1].strip():
            continue
        filtered_segments.append(seg)

    return filtered_segments


def build_display_text(raw_text, exclude_tools=None):
    if not raw_text:
        return ""
    if exclude_tools is None:
        exclude_tools = {"canvas", "generate-head", "automation", "verify_step"}

    segments = split_protocol(raw_text)
    display_parts = []

    for seg in segments:
        if not seg or len(seg) < 2:
            continue
        seg_type = seg[0]
        if seg_type == "text":
            display_parts.append(seg[1])
        elif seg_type == "tool":
            tool_name = seg[1]
            if tool_name in exclude_tools:
                continue
            if tool_name in ("msg", "message", "reply"):
                display_parts.append(seg[3])
            else:
                if seg[3]:
                    display_parts.append(f"[{tool_name}] {seg[3]}")

    return "\n".join(p for p in display_parts if p).strip()


def extract_tool_calls(raw_text):
    if not raw_text:
        return []
    segments = split_protocol(raw_text)
    calls = []
    for seg in segments:
        if seg[0] == "tool" and len(seg) >= 4:
            calls.append({
                "tool": seg[1],
                "head": seg[2],
                "value": seg[3],
            })
    return calls


def has_tool_calls(raw_text):
    if not raw_text:
        return False
    return bool(_TOOL_ONLY_RE.search(raw_text))


def strip_tool_calls(raw_text):
    if not raw_text:
        return ""
    segments = split_protocol(raw_text)
    parts = [seg[1] for seg in segments if seg[0] == "text" and len(seg) > 1]
    return "\n".join(parts).strip()
