import re
import ast
from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget, QCompleter, QToolTip
from PyQt6.QtGui import QColor, QFont, QTextFormat, QTextCursor, QPainter, QTextCharFormat
from PyQt6.QtCore import Qt, QSize, QStringListModel, QTimer
from utils.theme import THEME
from utils.highlighter import PythonHighlighter

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint(event)

    def mousePressEvent(self, event):
        self.editor.toggle_breakpoint_at_y(event.position().y())

class CodeEditor(QPlainTextEdit):
    def __init__(self, font_size=13):
        super().__init__()
        self.font_size = font_size
        self._setup_font()
        self.setMouseTracking(True)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
        self.line_area = LineNumberArea(self)
        self.highlighter = PythonHighlighter(self.document())
        self._error_line = 0
        self._debug_line = 0
        self.breakpoints = set()
        
        self.syntax_error_line = -1
        self.syntax_error_msg = ""
        self.syntax_timer = QTimer(self)
        self.syntax_timer.setSingleShot(True)
        self.syntax_timer.timeout.connect(self._check_syntax)
        self.textChanged.connect(self._on_text_changed)

        self.blockCountChanged.connect(self.update_line_area_width)
        self.updateRequest.connect(self.update_line_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_area_width(0)
        self.highlight_current_line()

        self._autocomplete_words = sorted(set(
            PythonHighlighter.KEYWORDS + PythonHighlighter.BUILTINS))
        self.completer = QCompleter(self._autocomplete_words, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setWidget(self)
        self.completer.activated.connect(self.insert_completion)

    def _setup_font(self):
        font = QFont("Consolas", self.font_size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(" "))
        self.update_line_area_width(0)

    def apply_theme(self):
        self.highlighter.rehighlight()
        self.highlight_current_line()
        self.line_area.update()
        
    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.font_size = min(48, self.font_size + 1)
            elif delta < 0:
                self.font_size = max(8, self.font_size - 1)
            self._setup_font()
            event.accept()
        else:
            super().wheelEvent(event)

    def _on_text_changed(self):
        self.syntax_timer.start(500)

    def _check_syntax(self):
        text = self.toPlainText()
        self.syntax_error_line = -1
        self.syntax_error_msg = ""
        try:
            ast.parse(text)
        except SyntaxError as e:
            self.syntax_error_line = getattr(e, 'lineno', -1)
            self.syntax_error_msg = getattr(e, 'msg', 'Syntax Error')
        self.highlight_current_line()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self.syntax_error_line > 0:
            cursor = self.cursorForPosition(event.pos())
            if cursor.blockNumber() + 1 == self.syntax_error_line:
                QToolTip.showText(event.globalPosition().toPoint(), self.syntax_error_msg, self)
                return
        QToolTip.hideText()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 26 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_area(self, rect, dy):
        if dy:
            self.line_area.scroll(0, dy)
        else:
            self.line_area.update(0, rect.y(), self.line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_area.setGeometry(cr.left(), cr.top(),
                                   self.line_number_area_width(), cr.height())

    def toggle_breakpoint_at_y(self, y):
        block = self.firstVisibleBlock()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        while block.isValid() and top <= y:
            if block.isVisible() and y <= bottom:
                line_no = block.blockNumber() + 1
                if line_no in self.breakpoints:
                    self.breakpoints.discard(line_no)
                else:
                    self.breakpoints.add(line_no)
                self.line_area.update()
                return
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())

    def line_number_area_paint(self, event):
        painter = QPainter(self.line_area)
        painter.fillRect(event.rect(), QColor(THEME["gutter"]))
        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = round(self.blockBoundingGeometry(block)
                    .translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        painter.setPen(QColor(THEME["gutter_fg"]))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_no = num + 1
                if line_no in self.breakpoints:
                    painter.setBrush(QColor(THEME["error"]))
                    painter.setPen(Qt.PenStyle.NoPen)
                    r = self.fontMetrics().height() // 3
                    cy = top + self.fontMetrics().height() // 2
                    painter.drawEllipse(6, cy - r, r * 2, r * 2)
                    painter.setPen(QColor(THEME["gutter_fg"]))
                painter.drawText(16, top, self.line_area.width() - 22,
                                 self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, str(line_no))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            num += 1

    def _find_matching_bracket(self):
        pairs = {"(": ")", "[": "]", "{": "}"}
        rev = {v: k for k, v in pairs.items()}
        text = self.toPlainText()
        pos = self.textCursor().position()
        for check_pos in (pos, pos - 1):
            if 0 <= check_pos < len(text):
                ch = text[check_pos]
                if ch in pairs:
                    depth = 0
                    for i in range(check_pos, len(text)):
                        if text[i] == ch:
                            depth += 1
                        elif text[i] == pairs[ch]:
                            depth -= 1
                            if depth == 0:
                                return (check_pos, i)
                    return None
                if ch in rev:
                    depth = 0
                    for i in range(check_pos, -1, -1):
                        if text[i] == ch:
                            depth += 1
                        elif text[i] == rev[ch]:
                            depth -= 1
                            if depth == 0:
                                return (i, check_pos)
                    return None
        return None

    def highlight_current_line(self):
        selections = []
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor(THEME["current"]))
        sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        selections.append(sel)
        if getattr(self, "_debug_line", 0) > 0:
            block = self.document().findBlockByNumber(self._debug_line - 1)
            if block.isValid():
                dsel = QTextEdit.ExtraSelection()
                dsel.format.setBackground(QColor(70, 60, 15))
                dsel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                cur = self.textCursor()
                cur.setPosition(block.position())
                dsel.cursor = cur
                dsel.cursor.clearSelection()
                selections.append(dsel)
        if getattr(self, "_error_line", 0) > 0:
            block = self.document().findBlockByNumber(self._error_line - 1)
            if block.isValid():
                esel = QTextEdit.ExtraSelection()
                esel.format.setBackground(QColor(80, 20, 20))
                esel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                cur = self.textCursor()
                cur.setPosition(block.position())
                esel.cursor = cur
                esel.cursor.clearSelection()
                selections.append(esel)
        match = self._find_matching_bracket()
        if match:
            for p in match:
                bsel = QTextEdit.ExtraSelection()
                bsel.format.setBackground(QColor(THEME["accent1"]))
                bsel.format.setForeground(QColor(THEME["bg"]))
                cur = self.textCursor()
                cur.setPosition(p)
                cur.setPosition(p + 1, QTextCursor.MoveMode.KeepAnchor)
                bsel.cursor = cur
                selections.append(bsel)
                
        if self.syntax_error_line > 0:
            block = self.document().findBlockByNumber(self.syntax_error_line - 1)
            if block.isValid():
                ssel = QTextEdit.ExtraSelection()
                fmt = QTextCharFormat()
                fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
                fmt.setUnderlineColor(QColor(THEME["error"]))
                ssel.format = fmt
                ssel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
                cur = self.textCursor()
                cur.setPosition(block.position())
                cur.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                ssel.cursor = cur
                selections.append(ssel)
                
        self.setExtraSelections(selections)

    def mark_error_line(self, line_no: int):
        self._error_line = line_no
        self.highlight_current_line()

    def clear_error_line(self):
        self._error_line = 0
        self.highlight_current_line()

    def mark_debug_line(self, line_no: int):
        self._debug_line = line_no
        self.highlight_current_line()
        cur = self.textCursor()
        block = self.document().findBlockByNumber(line_no - 1)
        if block.isValid():
            cur.setPosition(block.position())
            self.setTextCursor(cur)
            self.centerCursor()

    def clear_debug_line(self):
        self._debug_line = 0
        self.highlight_current_line()

    def keyPressEvent(self, event):
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape,
                               Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                event.ignore()
                return

        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            line = cursor.block().text()
            indent = len(line) - len(line.lstrip())
            extra = "    " if line.rstrip().endswith(":") else ""
            super().keyPressEvent(event)
            self.insertPlainText(" " * indent + extra)
            return
        super().keyPressEvent(event)
        self._update_autocomplete()

    def _text_under_cursor(self) -> str:
        cur = self.textCursor()
        cur.select(QTextCursor.SelectionType.WordUnderCursor)
        return cur.selectedText()

    def _current_doc_identifiers(self):
        text = self.toPlainText()
        return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))

    def _update_autocomplete(self):
        prefix = self._text_under_cursor()
        if len(prefix) < 2:
            self.completer.popup().hide()
            return
        words = sorted(set(self._autocomplete_words) | self._current_doc_identifiers())
        model = self.completer.model()
        if not isinstance(model, QStringListModel):
            model = QStringListModel(self)
            self.completer.setModel(model)
        model.setStringList(words)
        self.completer.setCompletionPrefix(prefix)
        if self.completer.completionCount() == 0 or (
                self.completer.completionCount() == 1 and
                self.completer.currentCompletion() == prefix):
            self.completer.popup().hide()
            return
        rect = self.cursorRect()
        rect.setWidth(self.completer.popup().sizeHintForColumn(0) +
                      self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(rect)

    def insert_completion(self, completion: str):
        cur = self.textCursor()
        cur.select(QTextCursor.SelectionType.WordUnderCursor)
        cur.insertText(completion)
        self.setTextCursor(cur)

