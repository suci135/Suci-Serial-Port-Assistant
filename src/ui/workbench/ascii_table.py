"""Searchable ASCII reference panel."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.ascii_catalog import ascii_entries


class AsciiTableWidget(QWidget):
    insert_text_requested = pyqtSignal(str)
    insert_hex_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("inspectorPage")
        self._entries = ascii_entries()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 10, 4, 4)
        layout.setSpacing(8)

        title = QLabel("ASCII 码表")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索字符、名称、十进制或 HEX…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("asciiTable")
        self.table.setHorizontalHeaderLabels(["Dec", "Hex", "字符", "名称", "说明"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self._insert_best_format)
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.insert_text_button = QPushButton("插入字符")
        self.insert_text_button.setObjectName("secondaryButton")
        self.insert_text_button.clicked.connect(self._insert_text)
        self.insert_hex_button = QPushButton("插入 HEX")
        self.insert_hex_button.setObjectName("primaryButton")
        self.insert_hex_button.clicked.connect(self._insert_hex)
        actions.addWidget(self.insert_text_button)
        actions.addWidget(self.insert_hex_button)
        layout.addLayout(actions)

        hint = QLabel("双击可打印字符直接插入；控制字符自动按 HEX 插入")
        hint.setObjectName("hintLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self._populate()

    def _populate(self):
        self.table.setRowCount(len(self._entries))
        for row, entry in enumerate(self._entries):
            values = (
                str(entry.decimal), entry.hexadecimal, entry.character,
                entry.name, entry.description,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, entry.decimal)
                self.table.setItem(row, column, item)
        self.table.selectRow(32)

    def _selected_value(self):
        row = self.table.currentRow()
        if row < 0 or self.table.item(row, 0) is None:
            return None
        return int(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))

    def _apply_filter(self, query: str):
        query = query.strip().casefold()
        for row, entry in enumerate(self._entries):
            haystack = " ".join(
                (str(entry.decimal), entry.hexadecimal, entry.character,
                 entry.name, entry.description)
            ).casefold()
            self.table.setRowHidden(row, bool(query and query not in haystack))

    def _insert_text(self):
        value = self._selected_value()
        if value is None:
            return
        if 32 <= value <= 126:
            self.insert_text_requested.emit(chr(value))
        else:
            self.insert_hex_requested.emit(f"{value:02X}")

    def _insert_hex(self):
        value = self._selected_value()
        if value is not None:
            self.insert_hex_requested.emit(f"{value:02X}")

    def _insert_best_format(self, row: int, _column: int):
        self.table.selectRow(row)
        self._insert_text()
