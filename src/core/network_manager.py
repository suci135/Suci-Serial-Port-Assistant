"""Socket transport used by the network debugger mode.

The UI only depends on the small manager contract shared with serial and
Bluetooth: connect, disconnect, send_data and Qt signals.  Socket details and
reader threads stay here so network features do not leak into the interface.
"""

from __future__ import annotations

import socket
import threading
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


TCP_CLIENT = "tcp_client"
TCP_SERVER = "tcp_server"
UDP = "udp"


class NetworkManager(QObject):
    """A small TCP/UDP transport with non-blocking UI notifications."""

    device_connected = pyqtSignal()
    device_disconnected = pyqtSignal()
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    connecting_status = pyqtSignal(str)
    clients_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._mode: Optional[str] = None
        self._socket: Optional[socket.socket] = None
        self._clients: dict[socket.socket, str] = {}
        self._connected = False
        self._stop = threading.Event()
        self._lock = threading.RLock()
        self._bound_port = 0
        self._remote: Optional[tuple[str, int]] = None
        self._keepalive = False
        self._broadcast = False
        self._send_target: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def bound_port(self) -> int:
        return self._bound_port

    @property
    def local_endpoint(self) -> Optional[tuple[str, int]]:
        """Return the bound local IP and port for connection diagnostics."""
        if not self._socket:
            return None
        try:
            address = self._socket.getsockname()
            return str(address[0]), int(address[1])
        except OSError:
            return None

    @property
    def client_endpoints(self) -> list[str]:
        with self._lock:
            return sorted(self._clients.values())

    def set_send_target(self, endpoint: Optional[str]):
        """Select one TCP-server client, or ``None`` to broadcast."""
        self._send_target = endpoint

    def configure(self, *, keepalive: bool = False, broadcast: bool = False):
        """Set connection options before opening the next socket."""
        self._keepalive = bool(keepalive)
        self._broadcast = bool(broadcast)

    def connect(
        self,
        host: str,
        port: int,
        mode: str,
        local_host: str = "0.0.0.0",
        local_port: int = 0,
    ) -> bool:
        """Open a TCP client/server or UDP endpoint.

        This method is intended to be called from a worker thread, just like
        the existing serial and Bluetooth connect methods.
        """
        if mode not in (TCP_CLIENT, TCP_SERVER, UDP):
            self.error_occurred.emit("不支持的网络模式")
            return False
        self.disconnect(emit_signal=False)
        self.connecting_status.emit("正在建立网络连接…")
        try:
            if mode == TCP_CLIENT:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if self._keepalive:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                sock.settimeout(5)
                sock.bind((local_host, local_port))
                sock.connect((host, port))
                sock.settimeout(0.25)
                self._activate(mode, sock, (host, port))
                self._start_thread(self._receive_loop, sock)
            elif mode == TCP_SERVER:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host or "0.0.0.0", port))
                sock.listen()
                sock.settimeout(0.25)
                self._activate(mode, sock, None)
                self._start_thread(self._accept_loop, sock)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                if self._broadcast:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.bind((local_host, local_port))
                sock.settimeout(0.25)
                self._activate(mode, sock, (host, port))
                self._start_thread(self._udp_receive_loop, sock)
        except OSError as exc:
            self.connecting_status.emit("")
            self.error_occurred.emit(f"网络连接失败: {exc}")
            self.disconnect(emit_signal=False)
            return False

        self.connecting_status.emit("")
        self.device_connected.emit()
        return True

    def disconnect(self, emit_signal: bool = True):
        """Close every endpoint without waiting for worker threads to finish."""
        was_connected = self._connected
        self._connected = False
        self._stop.set()
        with self._lock:
            sockets = [self._socket, *self._clients]
            self._socket = None
            self._clients.clear()
            self._send_target = None
        for sock in sockets:
            if sock is None:
                continue
            try:
                sock.close()
            except OSError:
                pass
        self._bound_port = 0
        self._remote = None
        self._mode = None
        self.clients_changed.emit([])
        if emit_signal and was_connected:
            self.device_disconnected.emit()

    def send_data(self, data: bytes) -> bool:
        if not self._connected or not data:
            if not self._connected:
                self.error_occurred.emit("网络未连接")
            return False
        try:
            if self._mode == TCP_CLIENT:
                assert self._socket is not None
                self._socket.sendall(data)
            elif self._mode == TCP_SERVER:
                with self._lock:
                    clients = tuple(
                        client
                        for client, endpoint in self._clients.items()
                        if self._send_target is None or endpoint == self._send_target
                    )
                if not clients:
                    self.error_occurred.emit("未找到可发送的 TCP 客户端")
                    return False
                for client in clients:
                    client.sendall(data)
            elif self._mode == UDP:
                assert self._socket is not None and self._remote is not None
                self._socket.sendto(data, self._remote)
            else:
                return False
            return True
        except OSError as exc:
            self.error_occurred.emit(f"网络发送失败: {exc}")
            return False

    def send_text(self, text: str, encoding: str = "utf-8") -> bool:
        try:
            return self.send_data(text.encode(encoding))
        except UnicodeEncodeError as exc:
            self.error_occurred.emit(f"文本编码失败: {exc}")
            return False

    def send_hex_string(self, hex_string: str) -> bool:
        try:
            compact = "".join(char for char in hex_string if char in "0123456789abcdefABCDEF")
            return self.send_data(bytes.fromhex(compact))
        except ValueError as exc:
            self.error_occurred.emit(f"十六进制格式错误: {exc}")
            return False

    def _activate(self, mode: str, sock: socket.socket, remote: Optional[tuple[str, int]]):
        self._stop.clear()
        self._mode = mode
        self._socket = sock
        self._remote = remote
        self._bound_port = int(sock.getsockname()[1])
        self._connected = True

    @staticmethod
    def _start_thread(target, *args):
        threading.Thread(target=target, args=args, daemon=True).start()

    def _accept_loop(self, server: socket.socket):
        while self._connected and not self._stop.is_set():
            try:
                client, address = server.accept()
                if self._keepalive:
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                client.settimeout(0.25)
                with self._lock:
                    self._clients[client] = f"{address[0]}:{address[1]}"
                    endpoints = sorted(self._clients.values())
                self.clients_changed.emit(endpoints)
                self._start_thread(self._receive_loop, client, True)
            except TimeoutError:
                continue
            except OSError:
                break

    def _receive_loop(self, sock: socket.socket, server_client: bool = False):
        while self._connected and not self._stop.is_set():
            try:
                data = sock.recv(65536)
                if not data:
                    break
                self.data_received.emit(data)
            except TimeoutError:
                continue
            except OSError:
                break
        if server_client:
            with self._lock:
                self._clients.pop(sock, None)
                if self._send_target not in self._clients.values():
                    self._send_target = None
                endpoints = sorted(self._clients.values())
            self.clients_changed.emit(endpoints)
            try:
                sock.close()
            except OSError:
                pass
        elif self._connected and not self._stop.is_set():
            self.error_occurred.emit("网络连接已断开")
            self.disconnect()

    def _udp_receive_loop(self, sock: socket.socket):
        while self._connected and not self._stop.is_set():
            try:
                data, _address = sock.recvfrom(65536)
                if data:
                    self.data_received.emit(data)
            except TimeoutError:
                continue
            except OSError:
                break
