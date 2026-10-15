"""GBLOXKOS_CODER Dashboard - Full modern GUI with copy/paste, right-click, clear history."""
import sys
import re
import random
import platform
import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QScrollArea, QApplication, QSplitter, QTextEdit,
    QMenu, QComboBox, QMessageBox,
    QGraphicsDropShadowEffect, QShortcut,
    QListWidget, QListWidgetItem,
    QAbstractItemView,
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal,
    QTimer, QRect,
)
from PyQt5.QtGui import (
    QFont, QColor,
    QKeySequence, QTextCharFormat, QSyntaxHighlighter,
    QCursor, QGuiApplication,
)

from config import Config, APP_NAME, APP_VERSION, get_available_models, WELCOME_MESSAGES
from ollama_client import get_client
from ai_engine import get_engine
from session_manager import get_session_manager

logger = logging.getLogger("gbloxkos.dashboard")

ASSETS = Path(__file__).parent / "assets"
MAX_BUBBLES = 200


class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        kw_color = QColor("#ff7b72")
        str_color = QColor("#a5d6ff")
        num_color = QColor("#79c0ff")
        cmt_color = QColor("#8b949e")

        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(kw_color)
        kw_fmt.setFontWeight(QFont.Bold)
        keywords = [
            "def", "class", "import", "from", "return", "if", "else", "elif",
            "for", "while", "try", "except", "finally", "with", "as", "in",
            "not", "and", "or", "is", "None", "True", "False", "self",
            "async", "await", "yield", "lambda", "pass", "break", "continue",
            "raise", "del", "global", "nonlocal", "assert", "print",
            "function", "const", "let", "var", "switch", "case", "default",
            "new", "this", "super", "extends", "implements", "interface",
            "type", "struct", "enum", "public", "private", "protected",
            "static", "final", "abstract", "void", "int", "float", "double",
            "string", "bool", "char", "long", "short", "unsigned",
        ]
        for kw in keywords:
            self._rules.append((re.compile(rf'\b{kw}\b'), kw_fmt))

        str_fmt = QTextCharFormat()
        str_fmt.setForeground(str_color)
        self._rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), str_fmt))
        self._rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), str_fmt))
        self._rules.append((re.compile(r'`[^`\\]*(\\.[^`\\]*)*`'), str_fmt))

        num_fmt = QTextCharFormat()
        num_fmt.setForeground(num_color)
        self._rules.append((re.compile(r'\b\d+\.?\d*\b'), num_fmt))

        cmt_fmt = QTextCharFormat()
        cmt_fmt.setForeground(cmt_color)
        cmt_fmt.setFontItalic(True)
        self._rules.append((re.compile(r'#[^\n]*'), cmt_fmt))
        self._rules.append((re.compile(r'//[^\n]*'), cmt_fmt))
        self._rules.append((re.compile(r'/\*.*?\*/', re.DOTALL), cmt_fmt))

    def highlightBlock(self, text):
        if not text:
            return
        for regex, fmt in self._rules:
            try:
                for m in regex.finditer(text):
                    self.setFormat(m.start(), m.end() - m.start(), fmt)
            except Exception:
                continue


class ChatBubble(QFrame):
    copy_requested = pyqtSignal(str)

    def __init__(self, text, role="user", theme=None, parent=None):
        super().__init__(parent)
        self.full_text = text or ""
        self.role = role
        self.theme = theme or {}
        self._setup_ui()

    def _setup_ui(self):
        t = self.theme
        bg = t.get("user_bubble" if self.role == "user" else "ai_bubble", "#1f3a5f")
        self.setStyleSheet(f"""
            ChatBubble {{
                background-color: {bg};
                border-radius: 12px;
                padding: 0px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        header = QHBoxLayout()
        icon = QLabel("You" if self.role == "user" else "AI")
        icon.setStyleSheet(f"color: {t.get('accent', '#58a6ff')}; font-weight: bold; font-size: 11px; background: transparent; border: none;")
        header.addWidget(icon)
        header.addStretch()
        layout.addLayout(header)

        if "```" in self.full_text or "    " in self.full_text:
            self._add_rich_text(layout)
        else:
            msg = QLabel(self.full_text)
            msg.setWordWrap(True)
            msg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            msg.setStyleSheet(f"color: {t.get('text_primary', '#e6edf3')}; font-size: 13px; background: transparent; border: none; padding: 2px;")
            layout.addWidget(msg)

        actions = QHBoxLayout()
        actions.addStretch()

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedSize(50, 22)
        copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.get('button_secondary', '#21262d')};
                color: {t.get('text_secondary', '#8b949e')};
                border: 1px solid {t.get('border', '#30363d')};
                border-radius: 6px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background: {t.get('button_secondary_hover', '#30363d')};
                color: {t.get('text_primary', '#e6edf3')};
            }}
        """)
        copy_btn.clicked.connect(lambda: self.copy_requested.emit(self.full_text))
        actions.addWidget(copy_btn)

        layout.addLayout(actions)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(t.get("shadow", "rgba(0,0,0,0.3)")))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def _add_rich_text(self, layout):
        parts = re.split(r'(```[\s\S]*?```)', self.full_text)
        for part in parts:
            if part.startswith("```") and part.endswith("```"):
                code = part[3:-3]
                lang_match = re.match(r'^(\w+)?\n', code)
                lang = lang_match.group(1) if lang_match else "code"
                if lang_match:
                    code = code[lang_match.end():]

                code_frame = QFrame()
                code_frame.setStyleSheet(f"""
                    QFrame {{
                        background: {self.theme.get('code_bg', '#0d1117')};
                        border: 1px solid {self.theme.get('code_border', '#30363d')};
                        border-radius: 8px;
                    }}
                """)
                code_layout = QVBoxLayout(code_frame)
                code_layout.setContentsMargins(8, 4, 8, 4)

                header = QLabel(f"  {lang}")
                header.setStyleSheet(f"color: {self.theme.get('text_muted', '#6e7681')}; font-size: 10px; background: transparent; border: none; font-weight: bold;")
                code_layout.addWidget(header)

                code_edit = QTextEdit()
                code_edit.setPlainText(code.strip())
                code_edit.setReadOnly(True)
                code_edit.setFont(QFont("Cascadia Code", 11))
                code_edit.setMaximumHeight(min(350, max(80, code.count('\n') * 18 + 40)))
                code_edit.setStyleSheet(f"""
                    QTextEdit {{
                        background: transparent;
                        color: {self.theme.get('code_text', '#e6edf3')};
                        border: none;
                        padding: 4px;
                    }}
                """)
                code_layout.addWidget(code_edit)

                copy_code_btn = QPushButton("Copy Code")
                copy_code_btn.setFixedWidth(80)
                copy_code_btn.setCursor(QCursor(Qt.PointingHandCursor))
                copy_code_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {self.theme.get('accent_dim', '#1f3a5f')};
                        color: {self.theme.get('accent', '#58a6ff')};
                        border: 1px solid {self.theme.get('accent', '#58a6ff')};
                        border-radius: 4px;
                        font-size: 10px; padding: 2px 6px;
                    }}
                    QPushButton:hover {{ background: {self.theme.get('accent', '#58a6ff')}; color: white; }}
                """)
                copy_code_btn.clicked.connect(lambda _, c=code.strip(): self.copy_requested.emit(c))
                code_layout.addWidget(copy_code_btn)

                layout.addWidget(code_frame)
            else:
                if part.strip():
                    msg = QLabel(part.strip())
                    msg.setWordWrap(True)
                    msg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
                    msg.setStyleSheet(f"color: {self.theme.get('text_primary', '#e6edf3')}; font-size: 13px; background: transparent; border: none; padding: 2px;")
                    layout.addWidget(msg)

    def update_theme(self, theme):
        self.theme = theme


class WorkerThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    tool_call = pyqtSignal(str, str)
    thinking = pyqtSignal(str)

    def __init__(self, engine, message, history):
        super().__init__()
        self.engine = engine
        self.message = message
        self.history = history
        self._stopped = False

    def run(self):
        try:
            result = self.engine.chat(
                self.message,
                history=self.history,
                on_tool_call=lambda t, v: self.tool_call.emit(t, v) if not self._stopped else None,
                on_thinking=lambda s: self.thinking.emit(s) if not self._stopped else None,
            )
            if result and not self._stopped:
                self.finished.emit(result)
        except Exception as e:
            logger.error(f"Worker thread error: {e}")
            if not self._stopped:
                self.error.emit(str(e))

    def stop(self):
        self._stopped = True


class ModelSelector(QFrame):
    model_changed = pyqtSignal(str, str)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(f"Model: {self.config.model_title}")
        self.label.setStyleSheet(f"""
            color: {self.config.t('text_secondary')};
            font-size: 11px;
        """)
        layout.addWidget(self.label)

        self.combo = QComboBox()
        self.combo.setMinimumWidth(200)
        self._refresh_models()
        self.combo.currentIndexChanged.connect(self._on_change)
        layout.addWidget(self.combo)

    def _refresh_models(self):
        self.combo.blockSignals(True)
        self.combo.clear()
        try:
            client = get_client()
            models = client.list_models(force=True)
            if models:
                for m in models:
                    if not m.get("is_embedding"):
                        label = f"{m['display_name']}  ({m['size_human']})"
                        self.combo.addItem(label, m["name"])
            else:
                available = get_available_models()
                for m in available:
                    self.combo.addItem(m["title"], m["tag"])
        except Exception as e:
            logger.error(f"Failed to refresh models: {e}")
            available = get_available_models()
            for m in available:
                self.combo.addItem(m["title"], m["tag"])

        idx = self.combo.findData(self.config.model_tag)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
        self.combo.blockSignals(False)

    def _on_change(self, index):
        if index < 0:
            return
        tag = self.combo.currentData()
        title = self.combo.currentText().split("  ")[0] if self.combo.currentText() else tag
        if tag:
            self.config.set_model(tag, title)
            self.label.setText(f"Model: {title}")
            self.model_changed.emit(tag, title)

    def refresh(self):
        self._refresh_models()


class CanvasPanel(QFrame):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedWidth(420)
        self.setStyleSheet(f"""
            QFrame {{
                background: {self.config.t('bg_secondary')};
                border-left: 1px solid {self.config.t('border')};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = QFrame()
        top_bar.setFixedHeight(40)
        top_bar.setStyleSheet(f"background: {self.config.t('bg_tertiary')}; border: none;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 0, 8, 0)

        self.title_label = QLabel("Code Editor")
        self.title_label.setStyleSheet(f"color: {self.config.t('text_primary')}; font-weight: bold; font-size: 12px; background: transparent; border: none;")
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()

        copy_all = QPushButton("Copy All")
        copy_all.setFixedHeight(24)
        copy_all.setCursor(QCursor(Qt.PointingHandCursor))
        copy_all.setStyleSheet(f"""
            QPushButton {{
                background: {self.config.t('accent_dim')};
                color: {self.config.t('accent')};
                border: 1px solid {self.config.t('accent')};
                border-radius: 4px; font-size: 10px; padding: 0 8px;
            }}
            QPushButton:hover {{ background: {self.config.t('accent')}; color: white; }}
        """)
        copy_all.clicked.connect(self._copy_all)
        top_layout.addWidget(copy_all)

        close_btn = QPushButton("X")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {self.config.t('text_muted')};
                border: none; font-weight: bold; font-size: 13px;
            }}
            QPushButton:hover {{ color: {self.config.t('error')}; }}
        """)
        close_btn.clicked.connect(lambda: self.hide())
        top_layout.addWidget(close_btn)

        layout.addWidget(top_bar)

        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setFont(QFont("Cascadia Code", 11))
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background: {self.config.t('code_bg')};
                color: {self.config.t('code_text')};
                border: none;
                padding: 12px;
                selection-background-color: {self.config.t('accent')};
            }}
        """)
        layout.addWidget(self.editor)

        self.hide()

    def update_content(self, code, filename=""):
        self.editor.setPlainText(code or "")
        if filename:
            self.title_label.setText(f"Code Editor - {filename}")
        else:
            self.title_label.setText("Code Editor")
        self.show()
        self.raise_()

    def _copy_all(self):
        text = self.editor.toPlainText()
        if text:
            QApplication.clipboard().setText(text)

    def update_theme(self, theme):
        if not theme:
            return
        self.setStyleSheet(f"""
            QFrame {{
                background: {theme.get('bg_secondary', '#161b22')};
                border-left: 1px solid {theme.get('border', '#30363d')};
            }}
        """)


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.session_mgr = get_session_manager()
        self.ollama = get_client()
        self.engine = get_engine(self.config.model_tag)
        self.worker = None
        self.bubbles = []
        self._updating_history = False
        self._shutdown = False

        self._setup_window()
        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()
        self._load_initial_state()

    def _setup_window(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(900, 600)
        self.resize(self.config.window_width, self.config.window_height)
        self.setStyleSheet(f"background: {self.config.t('bg_primary')};")
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geo = screen.geometry()
            x = (screen_geo.width() - self.width()) // 2
            y = (screen_geo.height() - self.height()) // 2
            self.move(x, y)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        main_layout.addWidget(self.sidebar)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {self.config.t('border')};
                width: 1px;
            }}
        """)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        center_layout.addWidget(self._build_top_bar())
        center_layout.addWidget(self._build_chat_area(), 1)
        center_layout.addWidget(self._build_input_bar())

        self.splitter.addWidget(center)
        self.canvas = CanvasPanel(self.config)
        self.splitter.addWidget(self.canvas)
        self.splitter.setSizes([900, 0])

        main_layout.addWidget(self.splitter, 1)

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(self.config.sidebar_width)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {self.config.t('sidebar_bg')};
                border-right: 1px solid {self.config.t('border')};
            }}
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo_frame = QFrame()
        logo_frame.setFixedHeight(56)
        logo_frame.setStyleSheet(f"background: {self.config.t('bg_secondary')}; border: none; border-bottom: 1px solid {self.config.t('border')};")
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 0, 16, 0)
        logo = QLabel(APP_NAME)
        logo.setStyleSheet(f"color: {self.config.t('accent')}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        logo_layout.addWidget(logo)
        logo_layout.addStretch()
        layout.addWidget(logo_frame)

        new_chat_btn = self._make_sidebar_button("+ New Chat", self._new_chat)
        layout.addWidget(new_chat_btn)

        nav_frame = QFrame()
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(8, 8, 8, 8)
        nav_layout.setSpacing(2)

        self.nav_chat = self._make_nav_button("Chat", self._show_chat)
        self.nav_chat.setProperty("active", True)
        nav_layout.addWidget(self.nav_chat)

        self.nav_tools = self._make_nav_button("Tools", self._show_tools)
        nav_layout.addWidget(self.nav_tools)

        self.nav_system = self._make_nav_button("System", self._show_system)
        nav_layout.addWidget(self.nav_system)

        layout.addWidget(nav_frame)

        section_label = QLabel("  HISTORY")
        section_label.setStyleSheet(f"color: {self.config.t('text_muted')}; font-size: 10px; font-weight: bold; padding: 12px 16px 4px 16px; background: transparent; border: none;")
        layout.addWidget(section_label)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {self.config.t('text_secondary')};
                font-size: 12px;
                padding: 0 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-radius: 6px;
                margin: 1px 4px;
            }}
            QListWidget::item:hover {{
                background: {self.config.t('sidebar_hover')};
            }}
            QListWidget::item:selected {{
                background: {self.config.t('accent_dim')};
                color: {self.config.t('accent')};
            }}
        """)
        self.history_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_list.currentRowChanged.connect(self._on_history_select)
        layout.addWidget(self.history_list, 1)

        clear_hist_btn = self._make_sidebar_button("Clear All History", self._clear_all_history)
        clear_hist_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.config.t('error')};
                border: none;
                border-top: 1px solid {self.config.t('border')};
                text-align: left;
                padding: 10px 20px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {self.config.t('button_danger')}22;
            }}
        """)
        layout.addWidget(clear_hist_btn)

        model_frame = QFrame()
        model_frame.setStyleSheet(f"background: {self.config.t('bg_secondary')}; border-top: 1px solid {self.config.t('border')}; border: none;")
        model_layout = QVBoxLayout(model_frame)
        model_layout.setContentsMargins(8, 8, 8, 8)

        self.model_selector = ModelSelector(self.config)
        self.model_selector.model_changed.connect(self._on_model_changed)
        model_layout.addWidget(self.model_selector)

        layout.addWidget(model_frame)

        settings_btn = self._make_sidebar_button("Settings", self._show_settings)
        layout.addWidget(settings_btn)

        return sidebar

    def _build_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(44)
        bar.setStyleSheet(f"background: {self.config.t('bg_secondary')}; border-bottom: 1px solid {self.config.t('border')};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {self.config.t('success')}; font-size: 11px; background: transparent; border: none;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.session_title_label = QLabel("")
        self.session_title_label.setStyleSheet(f"color: {self.config.t('text_secondary')}; font-size: 11px; background: transparent; border: none;")
        layout.addWidget(self.session_title_label)

        layout.addStretch()

        theme_btn = QPushButton("Theme")
        theme_btn.setFixedHeight(26)
        theme_btn.setCursor(QCursor(Qt.PointingHandCursor))
        theme_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.config.t('button_secondary')};
                color: {self.config.t('text_secondary')};
                border: 1px solid {self.config.t('border')};
                border-radius: 6px; font-size: 11px; padding: 0 12px;
            }}
            QPushButton:hover {{ background: {self.config.t('button_secondary_hover')}; color: {self.config.t('text_primary')}; }}
        """)
        theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(theme_btn)

        return bar

    def _build_chat_area(self):
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {self.config.t('bg_primary')};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.config.t('scrollbar_bg')};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.config.t('scrollbar_thumb')};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.config.t('text_muted')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()

        self.chat_scroll.setWidget(self.chat_container)
        return self.chat_scroll

    def _build_input_bar(self):
        bar = QFrame()
        bar.setStyleSheet(f"background: {self.config.t('bg_primary')}; border: none;")
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(20, 8, 20, 16)
        layout.setSpacing(8)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask anything - I'm your expert coder & assistant...")
        self.input_box.setMinimumHeight(48)
        self.input_box.setStyleSheet(f"""
            QLineEdit {{
                background: {self.config.t('bg_secondary')};
                color: {self.config.t('text_primary')};
                border: 2px solid {self.config.t('border')};
                border-radius: 12px;
                padding: 10px 16px;
                font-size: 14px;
                selection-background-color: {self.config.t('accent')};
            }}
            QLineEdit:focus {{
                border-color: {self.config.t('accent')};
            }}
        """)
        self.input_box.returnPressed.connect(self._send_message)
        layout.addWidget(self.input_box)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedSize(80, 32)
        self.send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.config.t('button_primary')};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {self.config.t('button_primary_hover')}; }}
            QPushButton:disabled {{ background: {self.config.t('text_muted')}; color: {self.config.t('bg_primary')}; }}
        """)
        self.send_btn.clicked.connect(self._send_message)
        btn_row.addWidget(self.send_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedSize(60, 32)
        self.stop_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.config.t('button_danger')};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {self.config.t('button_danger_hover')}; }}
        """)
        self.stop_btn.clicked.connect(self._stop_generation)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.stop_btn)

        layout.addLayout(btn_row)
        return bar

    def _make_sidebar_button(self, text, callback):
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.config.t('text_secondary')};
                border: none;
                text-align: left;
                padding: 10px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {self.config.t('sidebar_hover')};
                color: {self.config.t('text_primary')};
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def _make_nav_button(self, text, callback):
        btn = QPushButton(text)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.config.t('text_secondary')};
                border: none;
                text-align: left;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {self.config.t('sidebar_hover')};
            }}
        """)
        btn.clicked.connect(callback)
        return btn

    def _setup_shortcuts(self):
        paste = QShortcut(QKeySequence.Paste, self)
        paste.activated.connect(self._paste_clipboard)

        copy = QShortcut(QKeySequence.Copy, self)
        copy.activated.connect(self._copy_selection)

        select_all = QShortcut(QKeySequence.SelectAll, self)
        select_all.activated.connect(self._select_all)

        new_chat = QShortcut(QKeySequence("Ctrl+N"), self)
        new_chat.activated.connect(self._new_chat)

        quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit.activated.connect(self.close)

        search = QShortcut(QKeySequence("Ctrl+F"), self)
        search.activated.connect(self._focus_search)

    def _connect_signals(self):
        self.config.subscribe(self._on_config_change)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _load_initial_state(self):
        try:
            if not self.session_mgr.current_session_id:
                self.session_mgr.new_session()
            self._refresh_history()
            self._show_welcome()
        except Exception as e:
            logger.error(f"Failed to load initial state: {e}")

    def _show_welcome(self):
        if not WELCOME_MESSAGES:
            return
        msg = random.choice(WELCOME_MESSAGES)
        self._add_bubble(msg, "assistant")

    def _new_chat(self):
        self.session_mgr.new_session()
        self._clear_chat_display()
        self._show_welcome()
        self._refresh_history()
        self.session_title_label.setText("")

    def _clear_chat_display(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
        self.bubbles.clear()

    def _send_message(self):
        text = self.input_box.text().strip()
        if not text:
            return

        if self._shutdown:
            return

        if self.worker and self.worker.isRunning():
            self._stop_generation()
            QTimer.singleShot(200, lambda: self._do_send(text))
            return

        self._do_send(text)

    def _do_send(self, text):
        try:
            if self._shutdown:
                return

            session = self.session_mgr.get_current()
            if not session:
                self.session_mgr.new_session()
                session = self.session_mgr.get_current()

            if not session:
                self._add_bubble("Error: Could not create or access a chat session.", "assistant")
                return

            self.session_mgr.add_message(session["id"], "user", text)
            self.input_box.clear()
            self._add_bubble(text, "user")

            self.status_label.setText("Thinking...")
            self.status_label.setStyleSheet(f"color: {self.config.t('warning')}; font-size: 11px; background: transparent; border: none;")
            self.send_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

            history = self.session_mgr.get_ollama_messages(session["id"])

            self.worker = WorkerThread(self.engine, text, history)
            self.worker.finished.connect(self._on_response)
            self.worker.error.connect(self._on_error)
            self.worker.tool_call.connect(self._on_tool_call)
            self.worker.thinking.connect(self._on_thinking)
            self.worker.start()
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self._add_bubble(f"Error sending message: {e}", "assistant")
            self._reset_status("Error")

    def _stop_generation(self):
        try:
            if self.worker and self.worker.isRunning():
                self.engine.abort()
                self.worker.stop()
                if not self.worker.wait(3000):
                    logger.warning("Worker thread did not stop in time, terminating")
                    self.worker.terminate()
                self.worker = None
            self._reset_status("Generation stopped")
        except Exception as e:
            logger.error(f"Error stopping generation: {e}")
            self._reset_status("Error stopping")


    def _on_response(self, result):
        try:
            if not result:
                self._reset_status("Ready")
                return

            session = self.session_mgr.get_current()
            response_text = result.get("response", "")

            if response_text:
                if session:
                    self.session_mgr.add_message(session["id"], "assistant", response_text)
                self._add_bubble(response_text, "assistant")

            tool_calls = result.get("tool_calls", [])
            for tc in tool_calls:
                if tc.get("tool") == "canvas" and tc.get("value"):
                    try:
                        self.canvas.update_content(tc.get("value", ""), tc.get("head", ""))
                    except Exception as e:
                        logger.error(f"Canvas update error: {e}")

            tool_results = result.get("tool_results", [])
            for tr in tool_results:
                tool_name = tr.get("tool", "")
                tool_result = tr.get("result", {})
                if not tool_result.get("success") and tool_result.get("output"):
                    output = tool_result["output"]
                    if output and not output.startswith("Tool error"):
                        result_msg = f"Tool [{tool_name}]: {output[:300]}"
                        self._add_bubble(result_msg, "assistant")

            if session and response_text:
                title = session.get("title", "")
                if not title or title.startswith("Chat "):
                    preview = response_text[:40].replace("\n", " ").strip()
                    if preview:
                        try:
                            self.session_mgr.rename_session(session["id"], preview)
                        except Exception:
                            pass

            self._reset_status("Ready")
            self._refresh_history()
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            self._reset_status("Error")
        finally:
            self.worker = None

    def _on_error(self, error_msg):
        try:
            if error_msg:
                self._add_bubble(f"Error: {error_msg}", "assistant")
            self._reset_status("Error occurred")
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
        finally:
            self.worker = None

    def _on_tool_call(self, tool_name, value):
        try:
            if tool_name.startswith("result:"):
                short_name = tool_name.split(":", 1)[1]
                self.status_label.setText(f"Completed: {short_name}")
            else:
                self.status_label.setText(f"Tool: {tool_name}")
        except Exception:
            pass

    def _on_thinking(self, text):
        try:
            self.status_label.setText(text)
            self.status_label.setStyleSheet(f"color: {self.config.t('warning')}; font-size: 11px; background: transparent; border: none;")
        except Exception:
            pass

    def _add_bubble(self, text, role):
        try:
            while len(self.bubbles) >= MAX_BUBBLES:
                old_bubble = self.bubbles.pop(0)
                self.chat_layout.removeWidget(old_bubble)
                old_bubble.setParent(None)
                old_bubble.deleteLater()

            bubble = ChatBubble(text, role, self.config.theme)
            bubble.copy_requested.connect(self._copy_text)

            idx = self.chat_layout.count() - 1
            self.chat_layout.insertWidget(idx, bubble)
            self.bubbles.append(bubble)

            QTimer.singleShot(50, self._scroll_to_bottom)
        except Exception as e:
            logger.error(f"Error adding bubble: {e}")

    def _scroll_to_bottom(self):
        try:
            sb = self.chat_scroll.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception:
            pass

    def _copy_text(self, text):
        try:
            QApplication.clipboard().setText(text)
            self.status_label.setText("Copied to clipboard")
            QTimer.singleShot(2000, lambda: self._reset_status("Ready"))
        except Exception:
            pass

    def _paste_clipboard(self):
        try:
            text = QApplication.clipboard().text()
            if text:
                current = self.input_box.text()
                cursor_pos = self.input_box.cursorPosition()
                self.input_box.setText(current[:cursor_pos] + text + current[cursor_pos:])
                self.input_box.setCursorPosition(cursor_pos + len(text))
        except Exception:
            pass

    def _copy_selection(self):
        try:
            focused = QApplication.focusWidget()
            if isinstance(focused, QTextEdit):
                text = focused.textCursor().selectedText()
                if text:
                    QApplication.clipboard().setText(text)
                    self.status_label.setText("Copied to clipboard")
            elif isinstance(focused, QLineEdit):
                text = focused.selectedText()
                if text:
                    QApplication.clipboard().setText(text)
                    self.status_label.setText("Copied to clipboard")
        except Exception:
            pass

    def _select_all(self):
        try:
            focused = QApplication.focusWidget()
            if isinstance(focused, QTextEdit):
                focused.selectAll()
            elif isinstance(focused, QLineEdit):
                focused.selectAll()
        except Exception:
            pass

    def _focus_search(self):
        self.input_box.setFocus()

    def _show_context_menu(self, pos):
        try:
            menu = QMenu(self)
            menu.setStyleSheet(f"""
                QMenu {{
                    background: {self.config.t('bg_card')};
                    color: {self.config.t('text_primary')};
                    border: 1px solid {self.config.t('border')};
                    border-radius: 8px;
                    padding: 4px;
                }}
                QMenu::item {{
                    padding: 6px 20px;
                    border-radius: 4px;
                }}
                QMenu::item:selected {{
                    background: {self.config.t('accent_dim')};
                    color: {self.config.t('accent')};
                }}
                QMenu::separator {{
                    height: 1px;
                    background: {self.config.t('border')};
                    margin: 4px 8px;
                }}
            """)

            focused = QApplication.focusWidget()
            has_selection = False
            if isinstance(focused, (QTextEdit, QLineEdit)):
                if isinstance(focused, QTextEdit):
                    has_selection = bool(focused.textCursor().selectedText())
                else:
                    has_selection = bool(focused.selectedText())

            if has_selection:
                cut_action = menu.addAction("Cut")
                cut_action.setShortcut(QKeySequence.Cut)
                cut_action.triggered.connect(lambda: self._cut_text(focused))

                copy_action = menu.addAction("Copy")
                copy_action.setShortcut(QKeySequence.Copy)
                copy_action.triggered.connect(lambda: self._copy_from_widget(focused))
                menu.addSeparator()

            paste_action = menu.addAction("Paste")
            paste_action.setShortcut(QKeySequence.Paste)
            paste_action.triggered.connect(lambda: self._paste_to_widget(focused))

            if isinstance(focused, (QTextEdit, QLineEdit)):
                select_all_action = menu.addAction("Select All")
                select_all_action.setShortcut(QKeySequence.SelectAll)
                select_all_action.triggered.connect(lambda: focused.selectAll())
                menu.addSeparator()

            if isinstance(focused, QTextEdit) and focused.toPlainText():
                copy_all = menu.addAction("Copy All")
                copy_all.triggered.connect(lambda: QApplication.clipboard().setText(focused.toPlainText()))

            menu.addSeparator()

            new_action = menu.addAction("New Chat")
            new_action.setShortcut(QKeySequence("Ctrl+N"))
            new_action.triggered.connect(self._new_chat)

            clear_action = menu.addAction("Clear Current Chat")
            clear_action.triggered.connect(self._new_chat)

            clear_all_action = menu.addAction("Clear All History")
            clear_all_action.triggered.connect(self._clear_all_history)

            menu.addSeparator()

            paste_to_input = menu.addAction("Paste to Input")
            paste_to_input.triggered.connect(self._paste_to_input)

            menu.exec_(self.mapToGlobal(pos))
        except Exception as e:
            logger.error(f"Context menu error: {e}")

    def _cut_text(self, widget):
        try:
            if isinstance(widget, QTextEdit):
                cursor = widget.textCursor()
                text = cursor.selectedText()
                if text:
                    QApplication.clipboard().setText(text)
                    cursor.removeSelectedText()
            elif isinstance(widget, QLineEdit):
                text = widget.selectedText()
                if text:
                    QApplication.clipboard().setText(text)
                    start = widget.selectionStart()
                    end = widget.selectionEnd()
                    current = widget.text()
                    widget.setText(current[:start] + current[end:])
                    widget.setCursorPosition(start)
        except Exception:
            pass

    def _copy_from_widget(self, widget):
        try:
            if isinstance(widget, QTextEdit):
                text = widget.textCursor().selectedText()
            elif isinstance(widget, QLineEdit):
                text = widget.selectedText()
            else:
                return
            if text:
                QApplication.clipboard().setText(text)
        except Exception:
            pass

    def _paste_to_widget(self, widget):
        try:
            text = QApplication.clipboard().text()
            if not text:
                return
            if isinstance(widget, QTextEdit):
                widget.insertPlainText(text)
            elif isinstance(widget, QLineEdit):
                pos = widget.cursorPosition()
                current = widget.text()
                widget.setText(current[:pos] + text + current[pos:])
                widget.setCursorPosition(pos + len(text))
        except Exception:
            pass

    def _paste_to_input(self):
        try:
            text = QApplication.clipboard().text()
            if text:
                current = self.input_box.text()
                self.input_box.setText(current + text)
        except Exception:
            pass

    def _on_history_select(self, row):
        if self._updating_history:
            return
        if row < 0:
            return
        try:
            sessions = self.session_mgr.get_all_sessions()
            if row < len(sessions):
                session = sessions[row]
                self.session_mgr.set_current(session["id"])
                self._clear_chat_display()
                messages = self.session_mgr.get_messages(session["id"])
                for msg in messages:
                    role = msg.get("role", "user")
                    if role in ("user", "assistant"):
                        self._add_bubble(msg.get("content", ""), role)
                self.session_title_label.setText(session.get("title", ""))
        except Exception as e:
            logger.error(f"History select error: {e}")

    def _refresh_history(self):
        self._updating_history = True
        try:
            self.history_list.clear()
            sessions = self.session_mgr.get_all_sessions()
            for s in sessions:
                title = s.get("title", "Untitled")
                msg_count = len(s.get("messages", []))
                item_text = f"{title} ({msg_count})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, s["id"])
                self.history_list.addItem(item)

            current_id = self.session_mgr.current_session_id
            if current_id:
                for i in range(self.history_list.count()):
                    if self.history_list.item(i) and self.history_list.item(i).data(Qt.UserRole) == current_id:
                        self.history_list.setCurrentRow(i)
                        break
        except Exception as e:
            logger.error(f"Refresh history error: {e}")
        finally:
            self._updating_history = False

    def _clear_all_history(self):
        reply = QMessageBox.question(
            self, "Clear All History",
            "Delete ALL chat history permanently? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.session_mgr.clear_all()
            self.session_mgr.new_session()
            self._clear_chat_display()
            self._show_welcome()
            self._refresh_history()
            self.session_title_label.setText("")

    def _on_model_changed(self, tag, title):
        try:
            self.engine.set_model(tag)
            self.status_label.setText(f"Model: {title}")
        except Exception as e:
            logger.error(f"Model change error: {e}")

    def _toggle_theme(self):
        new_theme = "light" if self.config.theme_name == "dark" else "dark"
        self.config.set_theme(new_theme)
        self._apply_theme()

    def _apply_theme(self):
        try:
            t = self.config.theme
            self.setStyleSheet(f"background: {self.config.t('bg_primary')};")
            self.sidebar.setStyleSheet(f"""
                QFrame {{
                    background: {self.config.t('sidebar_bg')};
                    border-right: 1px solid {self.config.t('border')};
                }}
            """)
            self.canvas.update_theme(t)
            self.input_box.setStyleSheet(f"""
                QLineEdit {{
                    background: {self.config.t('bg_secondary')};
                    color: {self.config.t('text_primary')};
                    border: 2px solid {self.config.t('border')};
                    border-radius: 12px;
                    padding: 10px 16px;
                    font-size: 14px;
                    selection-background-color: {self.config.t('accent')};
                }}
                QLineEdit:focus {{ border-color: {self.config.t('accent')}; }}
            """)
            self.send_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {self.config.t('button_primary')};
                    color: white; border: none; border-radius: 8px;
                    font-size: 12px; font-weight: bold;
                }}
                QPushButton:hover {{ background: {self.config.t('button_primary_hover')}; }}
                QPushButton:disabled {{ background: {self.config.t('text_muted')}; color: {self.config.t('bg_primary')}; }}
            """)
            self.stop_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {self.config.t('button_danger')};
                    color: white; border: none; border-radius: 8px;
                    font-size: 12px;
                }}
                QPushButton:hover {{ background: {self.config.t('button_danger_hover')}; }}
                QPushButton:disabled {{ background: {self.config.t('text_muted')}; }}
            """)
            self.status_label.setStyleSheet(f"color: {self.config.t('success')}; font-size: 11px; background: transparent; border: none;")
            self.session_title_label.setStyleSheet(f"color: {self.config.t('text_secondary')}; font-size: 11px; background: transparent; border: none;")
            self.model_selector.label.setStyleSheet(f"color: {self.config.t('text_secondary')}; font-size: 11px;")
            self.history_list.setStyleSheet(f"""
                QListWidget {{
                    background: transparent;
                    border: none;
                    color: {self.config.t('text_secondary')};
                    font-size: 12px;
                    padding: 0 4px;
                }}
                QListWidget::item {{
                    padding: 8px 12px;
                    border-radius: 6px;
                    margin: 1px 4px;
                }}
                QListWidget::item:hover {{
                    background: {self.config.t('sidebar_hover')};
                }}
                QListWidget::item:selected {{
                    background: {self.config.t('accent_dim')};
                    color: {self.config.t('accent')};
                }}
            """)
            self.chat_scroll.setStyleSheet(f"""
                QScrollArea {{
                    background: {self.config.t('bg_primary')};
                    border: none;
                }}
                QScrollBar:vertical {{
                    background: {self.config.t('scrollbar_bg')};
                    width: 8px;
                    border-radius: 4px;
                }}
                QScrollBar::handle:vertical {{
                    background: {self.config.t('scrollbar_thumb')};
                    border-radius: 4px;
                    min-height: 30px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {self.config.t('text_muted')};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
            """)
            self.splitter.setStyleSheet(f"""
                QSplitter::handle {{
                    background: {self.config.t('border')};
                    width: 1px;
                }}
            """)
            for bubble in self.bubbles:
                bubble.update_theme(t)
            self._refresh_history()
        except Exception as e:
            logger.error(f"Theme apply error: {e}")

    def _on_config_change(self, event):
        if event == "theme":
            QTimer.singleShot(0, self._apply_theme)

    def _reset_status(self, text="Ready"):
        color = self.config.t("success") if text == "Ready" else self.config.t("text_secondary")
        if "Error" in text or "stopped" in text.lower():
            color = self.config.t("error")
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent; border: none;")
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _show_chat(self):
        pass

    def _show_tools(self):
        tool_info = """Available System Tools:

File System:
  fs_read, fs_write, fs_append, fs_delete, fs_list, fs_find, fs_copy, fs_move

Commands:
  cmd_exec, powershell, open_app

Process Management:
  proc_list, proc_kill

System Info:
  sys_cpu, sys_ram, sys_gpu, sys_disk

Web:
  web_search, web_browse, web_open, net_ping

UI Control:
  type_text, hotkey, screenshot, ui_windows, ui_focus

Media:
  media_volume, media_key

Input these commands in chat to control your system."""
        self._add_bubble(tool_info, "assistant")

    def _show_system(self):
        try:
            ollama_status = 'Connected' if self.ollama.is_healthy() else 'Disconnected'
        except Exception:
            ollama_status = 'Unknown'

        try:
            stats = self.session_mgr.get_stats()
            sessions_count = stats['total_sessions']
            messages_count = stats['total_messages']
        except Exception:
            sessions_count = 0
            messages_count = 0

        info = f"""System Information:
  Platform: {platform.system()} {platform.release()}
  Machine: {platform.machine()}
  Python: {platform.python_version()}

  Ollama Status: {ollama_status}
  Current Model: {self.config.model_title} ({self.config.model_tag})

  Sessions: {sessions_count}
  Total Messages: {messages_count}
"""
        self._add_bubble(info, "assistant")

    def _show_settings(self):
        available = get_available_models()
        models_list = "\n".join(f"    - {m['tag']} ({m['title']})" for m in available[:10]) if available else "    (none detected)"
        info = f"""Settings:
  Theme: {self.config.theme_name.title()}
  Model: {self.config.model_title}
  Model Tag: {self.config.model_tag}
  Ollama URL: {self.config.ollama_url}

  Detected Models:
{models_list}

  Click 'Theme' button in top bar to toggle dark/light mode.
  Use model dropdown in sidebar to switch models.
  Use 'Clear All History' to reset all chats."""
        self._add_bubble(info, "assistant")

    def closeEvent(self, event):
        self._shutdown = True
        try:
            if self.worker and self.worker.isRunning():
                self.engine.abort()
                self.worker.stop()
                self.worker.wait(2000)
            self.config.window_width = self.width()
            self.config.window_height = self.height()
            self.config.save()
            self.session_mgr._save()
        except Exception as e:
            logger.error(f"Close event error: {e}")
        event.accept()
