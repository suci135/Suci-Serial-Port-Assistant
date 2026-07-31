"""Transport-agnostic send composer widget."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)


class SendComposer(QFrame):
    """Collect outgoing data without knowing how it will be transported."""

    send_requested = pyqtSignal()
    repeat_toggled = pyqtSignal(int)
    interval_changed = pyqtSignal(int)

    def __init__(self, minimum_height: int, parent=None):
        super().__init__(parent)
        self.setObjectName("sendComposer")
        self.setMinimumHeight(minimum_height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        input_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["HEX", "ASCII", "UTF-8"])
        self.format_combo.setCurrentText("UTF-8")
        self.format_combo.setMinimumWidth(84)
        self.format_combo.setMaximumWidth(110)
        self.format_combo.setFixedHeight(42)
        input_row.addWidget(self.format_combo)

        self.input = QTextEdit()
        self.input.setObjectName("sendInput")
        self.input.setPlaceholderText("输入要发送的数据…")
        self.input.setFixedHeight(42)
        self.input.setFrameShape(QFrame.Shape.NoFrame)
        input_row.addWidget(self.input, 1)

        self.send_button = QPushButton("发送")
        self.send_button.setObjectName("primaryButton")
        self.send_button.setMinimumSize(72, 42)
        self.send_button.clicked.connect(self.send_requested)
        input_row.addWidget(self.send_button)
        layout.addLayout(input_row)

        options = QHBoxLayout()
        options.setSpacing(8)
        self.add_carriage = QCheckBox("\\r")
        self.add_newline = QCheckBox("\\n")
        self.repeat_check = QCheckBox("循环")
        self.repeat_check.setToolTip("按设定间隔重复发送当前输入")
        self.repeat_check.stateChanged.connect(self.repeat_toggled)
        self.interval_spin = QSpinBox()
        self.interval_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.interval_spin.setRange(50, 60000)
        self.interval_spin.setValue(1000)
        self.interval_spin.setSuffix(" ms")
        self.interval_spin.setMaximumWidth(86)
        self.interval_spin.setToolTip("循环发送间隔")
        self.interval_spin.valueChanged.connect(self.interval_changed)
        options.addWidget(self.add_carriage)
        options.addWidget(self.add_newline)
        options.addWidget(self.repeat_check)
        options.addWidget(self.interval_spin)
        options.addStretch()
        layout.addLayout(options)
