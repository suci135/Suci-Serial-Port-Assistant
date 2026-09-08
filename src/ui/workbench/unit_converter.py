"""Compact unit converter panel for the inspector."""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ...core.unit_converter import UNIT_GROUPS, convert, format_value


class UnitConverterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("inspectorPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 10, 4, 4)
        layout.setSpacing(8)
        title = QLabel("嵌入式单位换算")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        self.category = QComboBox()
        self.category.addItems(UNIT_GROUPS)
        self.category.currentTextChanged.connect(self._reload_units)
        layout.addWidget(self.category)
        self.input_value = QLineEdit("1")
        self.input_value.setPlaceholderText("输入数值")
        self.input_value.setClearButtonEnabled(True)
        self.input_value.textChanged.connect(self._convert)
        layout.addWidget(self.input_value)
        units = QHBoxLayout()
        self.source_unit = QComboBox()
        self.target_unit = QComboBox()
        self.source_unit.currentTextChanged.connect(self._convert)
        self.target_unit.currentTextChanged.connect(self._convert)
        units.addWidget(self.source_unit, 1)
        self.swap_button = QPushButton("⇄")
        self.swap_button.setObjectName("secondaryButton")
        self.swap_button.setFixedWidth(38)
        self.swap_button.setToolTip("交换输入和输出单位")
        self.swap_button.clicked.connect(self._swap_units)
        units.addWidget(self.swap_button)
        units.addWidget(self.target_unit, 1)
        layout.addLayout(units)
        result_card = QFrame()
        result_card.setObjectName("unitResultCard")
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(12, 10, 12, 10)
        self.result = QLabel("—")
        self.result.setObjectName("unitResult")
        self.result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.result_hint = QLabel("结果")
        self.result_hint.setObjectName("hintLabel")
        result_layout.addWidget(self.result)
        result_layout.addWidget(self.result_hint)
        layout.addWidget(result_card)
        self.copy_button = QPushButton("复制结果")
        self.copy_button.setObjectName("secondaryButton")
        self.copy_button.clicked.connect(self._copy_result)
        layout.addWidget(self.copy_button)
        layout.addStretch()
        self._result_animation = QPropertyAnimation(self.result, b"windowOpacity", self)
        self._result_animation.setDuration(120)
        self._result_animation.setStartValue(0.55)
        self._result_animation.setEndValue(1.0)
        self._result_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._reload_units("数据")

    def _reload_units(self, category):
        symbols = [unit.symbol for unit in UNIT_GROUPS[category]]
        for combo in (self.source_unit, self.target_unit):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(symbols)
            combo.blockSignals(False)
        self.target_unit.setCurrentIndex(1 if len(symbols) > 1 else 0)
        self._convert()

    def _convert(self):
        try:
            units = {unit.symbol: unit for unit in UNIT_GROUPS[self.category.currentText()]}
            source = units[self.source_unit.currentText()]
            target = units[self.target_unit.currentText()]
            value_text = self.input_value.text().strip()
            result = format_value(convert(float(value_text), source, target))
            self.result.setText(f"{result} {target.symbol}")
            self.result_hint.setText(f"{value_text} {source.symbol} =")
            self.copy_button.setEnabled(True)
            self._result_animation.stop()
            self._result_animation.start()
        except (KeyError, ValueError):
            self.result.setText("—")
            self.result_hint.setText("请输入有效数值")
            self.copy_button.setEnabled(False)

    def _swap_units(self):
        source, target = self.source_unit.currentIndex(), self.target_unit.currentIndex()
        self.source_unit.setCurrentIndex(target)
        self.target_unit.setCurrentIndex(source)

    def _copy_result(self):
        QApplication.clipboard().setText(self.result.text())
        self.copy_button.setText("已复制")
        self.copy_button.setEnabled(False)
        QTimer.singleShot(1000, lambda: (self.copy_button.setText("复制结果"), self.copy_button.setEnabled(True)))
