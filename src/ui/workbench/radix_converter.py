"""Programmer-calculator style radix conversion panel."""

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    QTimer,
    Qt,
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.radix_converter import convert_integer


def _group_right(text: str, width: int, pad_first: bool = False) -> str:
    sign = ""
    if text.startswith("-"):
        sign, text = "-", text[1:]
    if pad_first and text:
        text = text.zfill(((len(text) + width - 1) // width) * width)
    groups = []
    while text:
        groups.append(text[-width:])
        text = text[:-width]
    return sign + " ".join(reversed(groups or ["0"]))


class BaseValueRow(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, key: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setObjectName("baseValueRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(10)
        marker_space = QWidget()
        marker_space.setFixedWidth(4)
        layout.addWidget(marker_space)

        name = QLabel(key)
        name.setObjectName("baseName")
        name.setFixedWidth(42)
        layout.addWidget(name)
        self.value = QLabel("0")
        self.value.setObjectName("baseValue")
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.value, 1)
        self.set_selected(False)

    def set_selected(self, selected: bool):
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.key)
        super().mousePressEvent(event)


class RadixConverterWidget(QWidget):
    insert_hex_requested = pyqtSignal(str)

    _BASES = {"HEX": 16, "DEC": 10, "OCT": 8, "BIN": 2}
    _WIDTHS = {"自动位宽": None, "BYTE · 8 位": 8, "WORD · 16 位": 16,
               "DWORD · 32 位": 32, "QWORD · 64 位": 64}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("inspectorPage")
        self._conversion = None
        self._active_key = "DEC"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 10, 4, 4)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("程序员计算器")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        self.bit_width = QComboBox()
        self.bit_width.addItems(self._WIDTHS)
        self.bit_width.setMaximumWidth(132)
        self.bit_width.setToolTip("固定位宽下，负数使用二进制补码显示")
        self.bit_width.currentTextChanged.connect(self._on_width_changed)
        header.addWidget(self.bit_width)
        layout.addLayout(header)

        self.display = QLineEdit("0")
        self.display.setObjectName("radixDisplay")
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.display.setClearButtonEnabled(True)
        self.display.setPlaceholderText("0")
        self.display.textEdited.connect(self.convert_from_display)
        self.display.editingFinished.connect(self._format_display)
        layout.addWidget(self.display)

        self.rows = {}
        for key in ("HEX", "DEC", "OCT", "BIN"):
            row = BaseValueRow(key)
            row.clicked.connect(self.select_base)
            self.rows[key] = row
            layout.addWidget(row)

        self.selection_indicator = QFrame(self)
        self.selection_indicator.setObjectName("baseSelectionIndicator")
        self.selection_indicator.setGeometry(0, 0, 4, 24)
        self.selection_indicator.raise_()
        self._indicator_animation = QPropertyAnimation(
            self.selection_indicator, b"geometry", self
        )
        self._indicator_animation.setDuration(170)
        self._indicator_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._display_effect = QGraphicsOpacityEffect(self.display)
        self._display_effect.setOpacity(1.0)
        self.display.setGraphicsEffect(self._display_effect)
        self._display_animation = QPropertyAnimation(
            self._display_effect, b"opacity", self
        )
        self._display_animation.setDuration(150)
        self._display_animation.setStartValue(0.42)
        self._display_animation.setEndValue(1.0)
        self._display_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.status = QLabel("点击任意进制行即可切换输入进制")
        self.status.setObjectName("hintLabel")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.insert_button = QPushButton("插入 HEX 到发送框")
        self.insert_button.setObjectName("primaryButton")
        self.insert_button.clicked.connect(self.insert_hex)
        layout.addWidget(self.insert_button)
        layout.addStretch()

        self._set_active_row("DEC", animate=False)
        self.convert_from_display()
        QTimer.singleShot(0, self._snap_indicator_to_active_row)

    def _bit_width(self):
        return self._WIDTHS[self.bit_width.currentText()]

    def convert_from_display(self):
        text = self.display.text()
        if not text.strip():
            self._set_error("请输入需要转换的数值")
            return
        try:
            self._conversion = convert_integer(
                text, self._BASES[self._active_key], self._bit_width()
            )
        except ValueError as error:
            self._set_error(str(error))
            return
        self._render_conversion()

    def _render_conversion(self):
        conversion = self._conversion
        values = {
            "HEX": _group_right(conversion.hexadecimal, 4),
            "DEC": f"{conversion.value:,}",
            "OCT": _group_right(conversion.octal, 3),
            "BIN": _group_right(conversion.binary, 4, pad_first=True),
        }
        for key, value in values.items():
            self.rows[key].value.setText(value)
        self.status.setObjectName("hintLabel")
        self.status.setText("点击任意进制行即可切换输入进制")
        self.insert_button.setEnabled(bool(conversion.byte_hex))
        self._refresh_status_style()

    def _set_error(self, message: str):
        self._conversion = None
        for row in self.rows.values():
            row.value.setText("—")
        self.status.setObjectName("conversionError")
        self.status.setText(message)
        self.insert_button.setEnabled(False)
        self._refresh_status_style()

    def _refresh_status_style(self):
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def _indicator_geometry(self, key: str) -> QRect:
        row = self.rows[key]
        origin = row.mapTo(self, QPoint(0, (row.height() - 24) // 2))
        return QRect(origin.x(), origin.y(), 4, 24)

    def _snap_indicator_to_active_row(self):
        if not self.rows:
            return
        self.selection_indicator.setGeometry(
            self._indicator_geometry(self._active_key)
        )
        self.selection_indicator.raise_()

    def _set_active_row(self, key: str, animate: bool = True):
        self._active_key = key
        for row_key, row in self.rows.items():
            row.set_selected(row_key == key)
        target = self._indicator_geometry(key)
        if animate and self.isVisible():
            self._indicator_animation.stop()
            self._indicator_animation.setStartValue(self.selection_indicator.geometry())
            self._indicator_animation.setEndValue(target)
            self._indicator_animation.start()
        else:
            self.selection_indicator.setGeometry(target)
        self.selection_indicator.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._snap_indicator_to_active_row)

    def select_base(self, key: str):
        if key == self._active_key:
            self.display.setFocus()
            self.display.selectAll()
            return
        if self._conversion is None:
            self._set_active_row(key)
            self.convert_from_display()
            return
        self._set_active_row(key)
        self._set_display_text(self._value_for_key(key))
        self._display_animation.stop()
        self._display_animation.start()
        self.display.setFocus()
        self.display.selectAll()

    def _value_for_key(self, key: str) -> str:
        values = {
            "HEX": self._conversion.hexadecimal,
            "DEC": self._conversion.decimal,
            "OCT": self._conversion.octal,
            "BIN": self._conversion.binary,
        }
        return values[key]

    def _set_display_text(self, text: str):
        self.display.blockSignals(True)
        self.display.setText(text)
        self.display.blockSignals(False)

    def _format_display(self):
        if self._conversion is not None:
            formatted = self.rows[self._active_key].value.text()
            self._set_display_text(formatted)

    def _on_width_changed(self):
        if self._conversion is None:
            self.convert_from_display()
            return
        value = self._conversion.value
        try:
            self._conversion = convert_integer(str(value), 10, self._bit_width())
        except ValueError as error:
            self._set_error(str(error))
            return
        self._render_conversion()
        self._set_display_text(self._value_for_key(self._active_key))

    def insert_hex(self):
        if self._conversion and self._conversion.byte_hex:
            self.insert_hex_requested.emit(self._conversion.byte_hex)
