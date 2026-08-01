"""Compact session telemetry and actions for the navigation sidebar."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


def format_bytes(value: int) -> str:
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"


class SessionOverviewCard(QFrame):
    marker_requested = pyqtSignal()
    pause_toggled = pyqtSignal(bool)
    clear_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sessionOverviewCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(7)

        header = QHBoxLayout()
        title = QLabel("会话概览")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        self.duration = QLabel("未连接")
        self.duration.setObjectName("sessionDuration")
        header.addWidget(self.duration)
        layout.addLayout(header)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(6)
        metrics.setVerticalSpacing(4)
        self.tx_value = self._add_metric(metrics, 0, 0, "TX")
        self.rx_value = self._add_metric(metrics, 0, 1, "RX")
        self.tx_rate = self._add_metric(metrics, 1, 0, "发送速率")
        self.rx_rate = self._add_metric(metrics, 1, 1, "接收速率")
        layout.addLayout(metrics)

        actions = QHBoxLayout()
        actions.setSpacing(5)
        marker = QPushButton("标记")
        marker.setObjectName("sessionActionButton")
        marker.setToolTip("在消息流中插入带备注的时间标记")
        marker.clicked.connect(self.marker_requested)
        self.pause = QPushButton("暂停")
        self.pause.setObjectName("sessionActionButton")
        self.pause.setCheckable(True)
        self.pause.setToolTip("暂停消息渲染，后台仍继续接收")
        self.pause.toggled.connect(self.pause_toggled)
        clear = QPushButton("清屏")
        clear.setObjectName("sessionActionButton")
        clear.clicked.connect(self.clear_requested)
        for button in (marker, self.pause, clear):
            actions.addWidget(button, 1)
        layout.addLayout(actions)

    @staticmethod
    def _add_metric(layout, row: int, column: int, title: str):
        container = QFrame()
        container.setObjectName("sessionMetric")
        metric_layout = QVBoxLayout(container)
        metric_layout.setContentsMargins(6, 5, 6, 5)
        metric_layout.setSpacing(1)
        title_label = QLabel(title)
        title_label.setObjectName("sessionMetricTitle")
        value_label = QLabel("0 B")
        value_label.setObjectName("sessionMetricValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        metric_layout.addWidget(title_label)
        metric_layout.addWidget(value_label)
        layout.addWidget(container, row, column)
        return value_label

    def update_values(
        self,
        duration_text: str,
        sent_frames: int,
        sent_bytes: int,
        received_frames: int,
        received_bytes: int,
        send_rate: float,
        receive_rate: float,
    ):
        self.duration.setText(duration_text)
        self.tx_value.setText(f"{sent_frames} · {format_bytes(sent_bytes)}")
        self.rx_value.setText(f"{received_frames} · {format_bytes(received_bytes)}")
        self.tx_rate.setText(f"{format_bytes(int(send_rate))}/s")
        self.rx_rate.setText(f"{format_bytes(int(receive_rate))}/s")

    def set_paused(self, paused: bool):
        self.pause.setChecked(paused)
        self.pause.setText("继续" if paused else "暂停")
