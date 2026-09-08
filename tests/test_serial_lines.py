import unittest

from src.core.serial_manager import SerialManager


class FakeSerial:
    cts = True
    dsr = False
    cd = True
    ri = False
    dtr = False
    rts = False

    def send_break(self, duration):
        self.break_duration = duration


class SerialLineControlTests(unittest.TestCase):
    def setUp(self):
        self.manager = SerialManager()
        self.manager._serial = FakeSerial()
        self.manager._is_connected = True

    def test_reads_all_input_lines(self):
        self.assertEqual(
            self.manager.line_states,
            {"CTS": True, "DSR": False, "DCD": True, "RI": False},
        )

    def test_controls_dtr_rts_and_break(self):
        self.assertTrue(self.manager.set_dtr(True))
        self.assertTrue(self.manager.set_rts(True))
        self.assertTrue(self.manager.send_break(0.4))
        self.assertTrue(self.manager._serial.dtr)
        self.assertTrue(self.manager._serial.rts)
        self.assertEqual(self.manager._serial.break_duration, 0.4)

    def test_disconnected_lines_are_safe(self):
        self.manager._is_connected = False
        self.assertEqual(
            self.manager.line_states,
            {"CTS": False, "DSR": False, "DCD": False, "RI": False},
        )
        self.assertFalse(self.manager.set_dtr(True))
        self.assertFalse(self.manager.send_break())


if __name__ == "__main__":
    unittest.main()
