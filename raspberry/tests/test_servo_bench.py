import unittest
from unittest.mock import Mock, patch

from cuty.hardware import servo_bench


class ServoBenchTests(unittest.TestCase):
    def test_heartbeat_ack_in_fault_stops_test(self):
        bridge = Mock()
        bridge.exchange.side_effect = [
            "V2,ACK,1,OK,DISARMED", "V2,ACK,2,OK,DISARMED",
            "V2,ACK,3,OK,DISARMED", "V2,ACK,4,OK,READY",
            "V2,ACK,5,OK,ACTIVE", "V2,ACK,6,OK,ACTIVE",
            "V2,ACK,7,OK,FAULT",
        ]
        with patch.object(servo_bench.time, "monotonic", return_value=0):
            with self.assertRaisesRegex(RuntimeError, "ACTIVE"):
                servo_bench.run_test(bridge, 1, 1000, 3)

    def test_fault_recovery_and_single_session_with_heartbeat(self):
        bridge = Mock()
        bridge.exchange.side_effect = [
            "V2,ACK,1,OK,FAULT", "V2,ACK,2,OK,DISARMED",
            "V2,ACK,3,OK,DISARMED", "V2,ACK,4,OK,DISARMED",
            "V2,ACK,5,OK,READY", "V2,ACK,6,OK,ACTIVE",
            "V2,ACK,7,OK,ACTIVE", "V2,ACK,8,OK,ACTIVE",
        ]
        with patch.object(servo_bench.time, "monotonic", side_effect=[0, 0, 4]), \
                patch.object(servo_bench.time, "sleep"):
            servo_bench.run_test(bridge, 2, -1000, 3)
        self.assertEqual([call.args[0] for call in bridge.exchange.call_args_list], [
            b"V2,HB\n", b"V2,RESET\n", b"V2,DISARM\n", b"V2,HB\n",
            b"V2,ARM\n", b"V2,START\n", b"V2,TARGET,LEFT_ARM,-1000\n", b"V2,HB\n",
        ])

    def test_nack_stops_before_start_and_main_closes_bridge(self):
        bridge = Mock()
        bridge.exchange.side_effect = [
            "V2,ACK,1,OK,DISARMED", "V2,ACK,2,OK,DISARMED",
            "V2,ACK,3,OK,DISARMED", "V2,NACK,4,REJECTED,FAULT",
        ]
        with patch.object(servo_bench, "STM32Bridge", return_value=bridge):
            result = servo_bench.main(["--port", "/dev/test", "--channel", "1", "--target", "1000"])
        self.assertEqual(result, 2)
        bridge.close.assert_called_once()
        self.assertNotIn(b"V2,START\n", [call.args[0] for call in bridge.exchange.call_args_list])

    def test_invalid_limits_never_send(self):
        for channel, value, seconds in [(0, 0, 3), (1, 1001, 3), (1, 0, float("nan")), (1, 0, 11)]:
            bridge = Mock()
            with self.assertRaises(ValueError):
                servo_bench.run_test(bridge, channel, value, seconds)
            bridge.exchange.assert_not_called()

    def test_keyboard_interrupt_still_closes_bridge(self):
        bridge = Mock()
        with patch.object(servo_bench, "STM32Bridge", return_value=bridge), \
                patch.object(servo_bench, "run_test", side_effect=KeyboardInterrupt):
            result = servo_bench.main(["--port", "/dev/test", "--channel", "1", "--target", "0"])
        self.assertEqual(result, 130)
        bridge.close.assert_called_once()
