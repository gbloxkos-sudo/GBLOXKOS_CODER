#!/usr/bin/env python3
"""GBLOXKOS_CODER - Entry point with splash screen and crash handling."""
import sys
import os
import time
import logging
import signal
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

APP_DIR = Path(__file__).parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

LOG_DIR = APP_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        RotatingFileHandler(LOG_DIR / "gbloxkos.log", maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("gbloxkos.main")

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

from PyQt5.QtWidgets import QApplication, QSplashScreen, QLabel, QMessageBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QFontDatabase


def setup_fonts():
    assets = APP_DIR / "assets"
    font_ids = []
    if assets.exists():
        for f in assets.glob("*.ttf"):
            try:
                fid = QFontDatabase.addApplicationFont(str(f))
                if fid >= 0:
                    font_ids.append(fid)
                else:
                    logger.warning(f"Failed to load font: {f.name}")
            except Exception as e:
                logger.warning(f"Error loading font {f.name}: {e}")
    return font_ids


class SplashThread(QThread):
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)

    def run(self):
        steps = [
            (10, "Initializing GBLOXKOS_CODER..."),
            (25, "Loading fonts and themes..."),
            (40, "Connecting to Ollama..."),
            (55, "Detecting installed models..."),
            (70, "Loading session data..."),
            (85, "Preparing AI engine..."),
            (95, "Almost ready..."),
            (100, "Welcome to GBLOXKOS_CODER!"),
        ]
        for pct, msg in steps:
            try:
                self.progress.emit(pct, msg)
                time.sleep(0.3)
            except RuntimeError:
                logger.warning("Splash thread runtime error, stopping")
                break
            except Exception as e:
                logger.error(f"Splash thread error: {e}")
                self.error.emit(str(e))
                break


class SplashScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(500, 320)
        pixmap.fill(QColor("#0d1117"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QColor("#58a6ff"))
        font = QFont("Segoe UI", 28)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect().adjusted(0, -40, 0, 0), Qt.AlignCenter, "GBLOXKOS_CODER")

        painter.setPen(QColor("#8b949e"))
        font.setPointSize(11)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(pixmap.rect().adjusted(0, 30, 0, 0), Qt.AlignCenter, "Expert AI Coding Assistant")

        painter.setPen(QColor("#30363d"))
        painter.drawLine(80, 200, 420, 200)

        painter.end()

        super().__init__(pixmap)
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self._progress_label = QLabel(self)
        self._progress_label.setGeometry(80, 220, 340, 30)
        self._progress_label.setStyleSheet("color: #58a6ff; font-size: 12px; background: transparent;")
        self._progress_label.setAlignment(Qt.AlignCenter)

        self._bar_bg = QLabel(self)
        self._bar_bg.setGeometry(80, 260, 340, 6)
        self._bar_bg.setStyleSheet("background: #21262d; border-radius: 3px;")
        self._bar_bg.setAutoFillBackground(True)

        self._bar_fill = QLabel(self)
        self._bar_fill.setGeometry(80, 260, 0, 6)
        self._bar_fill.setStyleSheet("background: #58a6ff; border-radius: 3px;")
        self._bar_fill.setAutoFillBackground(True)

        self._version_label = QLabel(self)
        self._version_label.setGeometry(80, 280, 340, 20)
        self._version_label.setStyleSheet("color: #6e7681; font-size: 10px; background: transparent;")
        self._version_label.setAlignment(Qt.AlignCenter)
        self._version_label.setText("v2.0.0")

    def update_progress(self, pct, msg):
        try:
            self._progress_label.setText(msg)
            width = int(340 * pct / 100)
            self._bar_fill.setFixedWidth(width)
        except Exception:
            pass


def check_ollama():
    try:
        from ollama_client import get_client
        from config import detect_ollama_models, get_default_model, get_available_models
        client = get_client()
        ok = client.health_check()
        if ok:
            models = client.list_models(force=True)
            detect_ollama_models()
            default = get_default_model()
            available = get_available_models()
            logger.info(f"Ollama connected. {len(available)} models available. Default: {default}")
            return ok, default, available
        else:
            logger.warning("Ollama not detected. AI features may be limited.")
            return ok, None, []
    except Exception as e:
        logger.warning(f"Ollama check failed: {e}")
        return False, None, []


def excepthook(exc_type, exc_value, exc_tb):
    if exc_type is KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down gracefully.")
        try:
            app = QApplication.instance()
            if app:
                app.quit()
        except Exception:
            pass
        return
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical(f"Unhandled exception:\n{tb}")
    try:
        app = QApplication.instance()
        if app:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("GBLOXKOS_CODER - Fatal Error")
            msg.setText(f"{exc_type.__name__}: {exc_value}")
            msg.setInformativeText(tb[-500:])
            msg.exec_()
    except Exception:
        pass
    sys.exit(1)


def main():
    sys.excepthook = excepthook

    if hasattr(signal, 'SIGINT'):
        signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("GBLOXKOS_CODER")
    app.setApplicationVersion("2.0.0")

    setup_fonts()

    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#0d1117"))
    palette.setColor(QPalette.WindowText, QColor("#e6edf3"))
    palette.setColor(QPalette.Base, QColor("#161b22"))
    palette.setColor(QPalette.AlternateBase, QColor("#1c2333"))
    palette.setColor(QPalette.ToolTipBase, QColor("#1c2333"))
    palette.setColor(QPalette.ToolTipText, QColor("#e6edf3"))
    palette.setColor(QPalette.Text, QColor("#e6edf3"))
    palette.setColor(QPalette.Button, QColor("#21262d"))
    palette.setColor(QPalette.ButtonText, QColor("#e6edf3"))
    palette.setColor(QPalette.BrightText, QColor("#f85149"))
    palette.setColor(QPalette.Link, QColor("#58a6ff"))
    palette.setColor(QPalette.Highlight, QColor("#1f3a5f"))
    palette.setColor(QPalette.HighlightedText, QColor("#e6edf3"))
    app.setPalette(palette)

    splash = SplashScreen()
    splash.show()
    app.processEvents()

    splash_th = SplashThread()
    splash_th.progress.connect(splash.update_progress)
    splash_th.error.connect(lambda e: logger.error(f"Splash error: {e}"))
    splash_th.start()

    def on_splash_finished():
        QTimer.singleShot(0, lambda: _launch_app(app, splash))
    
    splash_th.finished.connect(on_splash_finished)

    sys.exit(app.exec_())


def _launch_app(app, splash):
    ollama_ok = False
    detected_model = None
    try:
        ollama_ok, detected_model, _ = check_ollama()
    except Exception as e:
        logger.warning(f"Ollama check error during launch: {e}")

    # Refresh config with detected model
    if detected_model:
        try:
            from config import Config
            Config().refresh_model_from_detection()
        except Exception as e:
            logger.warning(f"Failed to refresh config model: {e}")

    try:
        splash.close()
    except Exception:
        pass

    try:
        from dashboard import Dashboard
        window = Dashboard()
        window.show()
    except Exception as e:
        logger.critical(f"Failed to launch dashboard: {e}", exc_info=True)
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("GBLOXKOS_CODER - Launch Error")
            msg.setText("Failed to start the application")
            msg.setInformativeText(str(e))
            msg.exec_()
        except Exception:
            pass
        sys.exit(1)

    if not ollama_ok:
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Ollama Not Detected")
            msg.setText("Ollama is not running or not installed.")
            msg.setInformativeText(
                "AI features require Ollama with at least one model installed.\n\n"
                "To install Ollama: https://ollama.com\n"
                "To pull a model: ollama pull qwen2.5-coder\n\n"
                "You can still use the GUI, but AI chat will not work."
            )
            msg.exec_()
        except Exception:
            pass


if __name__ == "__main__":
    main()
