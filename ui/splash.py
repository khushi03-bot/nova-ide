from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen
from PyQt6.QtCore import Qt, QTimer, QRectF
from utils.theme import THEME

class SplashScreen(QWidget):
    NOVA_LOGO = [
        '███╗   ██╗ ██████╗  ██╗   ██╗ █████╗ ',
        '████╗  ██║██╔═══██╗ ██║   ██║██╔══██╗',
        '██╔██╗ ██║██║   ██║ ██║   ██║███████║',
        '██║╚██╗██║██║   ██║ ╚██╗ ██╔╝██╔══██║',
        '██║ ╚████║╚██████╔╝  ╚████╔╝ ██║  ██║',
        '╚═╝  ╚═══╝ ╚═════╝    ╚═══╝  ╚═╝  ╚═╝',
    ]
    BOOT_ITEMS = [
        "Neural Core", "Execution Engine", "Bundled Python",
        "AI Integrations", "Editor & Console", "Theme System",
    ]
    CREDIT = "◈  NOVA IDE  •  CREATED BY KHUSHI MITTAL  ◈"

    def __init__(self, on_done):
        super().__init__()
        self.on_done = on_done
        self.setFixedSize(720, 460)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                  (screen.height() - self.height()) // 2)

        self._t = 0.0
        self._logo_reveal = 0
        self._boot_progress = []
        self._boot_index = 0
        self._rain = self._init_rain()
        self._glitch_phase = 0.0
        self._done = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def _init_rain(self):
        import random
        cols = self.width() // 12
        drops = []
        for c in range(cols):
            drops.append({
                "x": c * 12 + 4,
                "y": random.randint(-self.height(), 0),
                "speed": random.uniform(3, 9),
                "chars": [random.choice("01アイウカキ#$%&▓▒░") for _ in range(14)],
            })
        return drops

    def _tick(self):
        import random
        self._t += 0.033
        for d in self._rain:
            d["y"] += d["speed"]
            if d["y"] > self.height() + 60:
                d["y"] = random.randint(-200, -20)
                d["speed"] = random.uniform(3, 9)
            if random.random() < 0.08:
                d["chars"][random.randint(0, len(d["chars"]) - 1)] = random.choice("01アイウカキ#$%&▓▒░")
        
        if self._t > 0.5 and self._logo_reveal < len(self.NOVA_LOGO):
            if random.random() < 0.30:
                self._logo_reveal += 1
                
        if self._logo_reveal >= len(self.NOVA_LOGO):
            if self._boot_index < len(self.BOOT_ITEMS):
                if len(self._boot_progress) <= self._boot_index:
                    self._boot_progress.append(0.0)
                self._boot_progress[self._boot_index] += random.uniform(0.06, 0.16)
                if self._boot_progress[self._boot_index] >= 1.0:
                    self._boot_progress[self._boot_index] = 1.0
                    self._boot_index += 1
            else:
                if not self._done and self._t > 0.5:
                    self._finish_soon()
        self._glitch_phase += 0.033
        self.update()

    def _finish_soon(self):
        self._done = True
        QTimer.singleShot(600, self._finish)

    def _finish(self):
        self._timer.stop()
        self.hide()
        if self.on_done:
            self.on_done()

    def paintEvent(self, event):
        import random
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(THEME["bg"]))

        mono = QFont("Consolas", 11)
        p.setFont(mono)
        for d in self._rain:
            for i, ch in enumerate(d["chars"]):
                y = int(d["y"]) - i * 14
                if 0 <= y <= self.height():
                    if i == 0:
                        p.setPen(QColor(THEME["accent3"]))
                    else:
                        alpha = max(20, 160 - i * 14)
                        col = QColor(THEME["accent1"])
                        col.setAlpha(alpha)
                        p.setPen(col)
                    p.drawText(d["x"], y, ch)

        logo_font = QFont("Consolas", 13)
        logo_font.setBold(True)
        p.setFont(logo_font)
        fm = QFontMetrics(logo_font)
        line_h = fm.height()
        start_y = 70
        for row in range(self._logo_reveal):
            line = self.NOVA_LOGO[row]
            if row == self._logo_reveal - 1 and random.random() < 0.25:
                gl = "".join(random.choice("▓▒░█") if random.random() < 0.12 else c for c in line)
                line = gl
            w = fm.horizontalAdvance(line)
            x = (self.width() - w) // 2
            p.setPen(QColor(THEME["accent1"]))
            p.drawText(x, start_y + row * line_h, line)

        if self._logo_reveal >= len(self.NOVA_LOGO):
            tag_font = QFont("Consolas", 10)
            p.setFont(tag_font)
            p.setPen(QColor(THEME["accent2"]))
            tag = "STANDALONE PYTHON IDE"
            tfm = QFontMetrics(tag_font)
            tw = tfm.horizontalAdvance(tag)
            p.drawText((self.width() - tw) // 2, start_y + 6 * line_h + 18, tag)

        bar_font = QFont("Consolas", 10)
        p.setFont(bar_font)
        bfm = QFontMetrics(bar_font)
        bar_x = 150
        bar_w = 320
        by = 250
        for i, item in enumerate(self.BOOT_ITEMS):
            if i >= len(self._boot_progress):
                break
            prog = self._boot_progress[i]
            y = by + i * 26
            p.setPen(QColor(THEME["fg"]))
            p.drawText(bar_x, y + 11, f"{item:<22}")
            label_w = bfm.horizontalAdvance("X" * 22)
            track_x = bar_x + label_w + 6
            track_w = bar_w - label_w
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(THEME["bg_alt"]))
            p.drawRoundedRect(QRectF(track_x, y, track_w, 12), 3, 3)
            fill_col = QColor(THEME["accent3"]) if prog >= 1.0 else QColor(THEME["accent1"])
            p.setBrush(fill_col)
            p.drawRoundedRect(QRectF(track_x, y, track_w * prog, 12), 3, 3)
            if prog >= 1.0:
                p.setPen(QColor(THEME["accent3"]))
                p.drawText(track_x + track_w + 8, y + 11, "OK")

        credit_font = QFont("Consolas", 11)
        credit_font.setBold(True)
        p.setFont(credit_font)
        pulse = 150 + int(80 * abs((self._glitch_phase % 2) - 1))
        col = QColor(THEME["accent2"])
        col.setAlpha(min(255, pulse + 25))
        p.setPen(col)
        cfm = QFontMetrics(credit_font)
        cw = cfm.horizontalAdvance(self.CREDIT)
        p.drawText((self.width() - cw) // 2, self.height() - 30, self.CREDIT)

        pen = QPen(QColor(THEME["accent1"]))
        pen.setWidth(1)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(0, 0, self.width() - 1, self.height() - 1)


