import socket
import time
import unittest

from PyQt6.QtCore import QCoreApplication

from src.core.network_manager import NetworkManager, TCP_CLIENT, TCP_SERVER, UDP


class NetworkManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def _wait_for(self, predicate, timeout=2.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return True
            time.sleep(0.01)
        return False

    def test_tcp_server_and_client_exchange_bytes(self):
        server = NetworkManager()
        client = NetworkManager()
        received_by_server = []
        received_by_client = []
        server.data_received.connect(received_by_server.append)
        client.data_received.connect(received_by_client.append)
        try:
            server.configure(keepalive=True)
            client.configure(keepalive=True)
            self.assertTrue(server.connect("127.0.0.1", 0, TCP_SERVER))
            self.assertGreater(server.bound_port, 0)
            with socket.socket() as reservation:
                reservation.bind(("127.0.0.1", 0))
                source_port = reservation.getsockname()[1]
            self.assertTrue(
                client.connect(
                    "127.0.0.1",
                    server.bound_port,
                    TCP_CLIENT,
                    "127.0.0.1",
                    source_port,
                )
            )
            self.assertEqual(client.local_endpoint, ("127.0.0.1", source_port))
            self.assertTrue(client.send_data(b"ping"))
            self.assertTrue(self._wait_for(lambda: received_by_server == [b"ping"]))
            self.assertTrue(server.send_data(b"pong"))
            self.assertTrue(self._wait_for(lambda: received_by_client == [b"pong"]))
        finally:
            client.disconnect()
            server.disconnect()

    def test_udp_exchange_bytes(self):
        first = NetworkManager()
        second = NetworkManager()
        received = []
        second.data_received.connect(received.append)
        try:
            first.configure(broadcast=True)
            second.configure(broadcast=True)
            self.assertTrue(
                first.connect("127.0.0.1", 9, UDP, "127.0.0.1", local_port=0)
            )
            self.assertEqual(first.local_endpoint[0], "127.0.0.1")
            self.assertTrue(second.connect("127.0.0.1", first.bound_port, UDP, local_port=0))
            first.disconnect()
            self.assertTrue(first.connect("127.0.0.1", second.bound_port, UDP, local_port=0))
            self.assertTrue(first.send_data(b"udp"))
            self.assertTrue(self._wait_for(lambda: received == [b"udp"]))
        finally:
            first.disconnect()
            second.disconnect()

    def test_tcp_server_can_send_to_one_selected_client(self):
        server = NetworkManager()
        first = NetworkManager()
        second = NetworkManager()
        first_received = []
        second_received = []
        first.data_received.connect(first_received.append)
        second.data_received.connect(second_received.append)
        try:
            self.assertTrue(server.connect("127.0.0.1", 0, TCP_SERVER))
            self.assertTrue(first.connect("127.0.0.1", server.bound_port, TCP_CLIENT))
            self.assertTrue(second.connect("127.0.0.1", server.bound_port, TCP_CLIENT))
            self.assertTrue(self._wait_for(lambda: len(server.client_endpoints) == 2))
            endpoint = f"{first.local_endpoint[0]}:{first.local_endpoint[1]}"
            server.set_send_target(endpoint)
            self.assertTrue(server.send_data(b"first-only"))
            self.assertTrue(self._wait_for(lambda: first_received == [b"first-only"]))
            self.app.processEvents()
            self.assertEqual(second_received, [])
        finally:
            first.disconnect()
            second.disconnect()
            server.disconnect()


if __name__ == "__main__":
    unittest.main()
