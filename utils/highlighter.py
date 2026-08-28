from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression
from utils.theme import THEME

class PythonHighlighter(QSyntaxHighlighter):
    KEYWORDS = [
        "and", "as", "assert", "async", "await", "break", "class", "continue",
        "def", "del", "elif", "else", "except", "finally", "for", "from",
        "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
        "or", "pass", "raise", "return", "try", "while", "with", "yield",
        "True", "False", "None", "match", "case",
    ]
    BUILTINS = [
        "print", "len", "range", "int", "str", "float", "list", "dict", "set",
        "tuple", "bool", "open", "input", "type", "isinstance", "enumerate",
        "zip", "map", "filter", "sum", "min", "max", "abs", "sorted", "reversed",
        "super", "object", "self",
    ]

    def __init__(self, doc):
        super().__init__(doc)
        self.rules = []

        def fmt(color, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Weight.Bold)
            if italic:
                f.setFontItalic(True)
            return f

        kw_fmt = fmt(THEME["keyword"], bold=True)
        for w in self.KEYWORDS:
            self.rules.append(
                (QRegularExpression(rf"\b{w}\b"), kw_fmt)
            )

        bi_fmt = fmt(THEME["builtin"])
        for w in self.BUILTINS:
            self.rules.append((QRegularExpression(rf"\b{w}\b"), bi_fmt))

        self.rules.append(
            (QRegularExpression(r"\bdef\s+(\w+)"), fmt(THEME["func"], bold=True))
        )
        self.rules.append(
            (QRegularExpression(r"\b[0-9]+\.?[0-9]*\b"), fmt(THEME["number"]))
        )
        self.str_fmt = fmt(THEME["string"])
        self.rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.str_fmt))
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.str_fmt))
        self.comment_fmt = fmt(THEME["comment"], italic=True)
        self.rules.append((QRegularExpression(r"#[^\n]*"), self.comment_fmt))

    def highlightBlock(self, text):
        for pattern, f in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), f)
