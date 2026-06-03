"""Mock ESP32 serial packet generator for bridge testing without hardware."""

import json
import math
import random

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MockSerialPacketNode(Node):
    """Publish newline-equivalent JSON packets matching ESP32_SERIAL_PROTOCOL.md."""

    def __init__(self):
        super().__init__('mock_serial_packet_node')
        self.declare_parameter('publish_rate_hz', 100.0)
        self.declare_parameter('encoder_noise_std', 0.002)
        self.declare_parameter('imu_noise_std', 0.005)

        self._encoder_noise_std = float(self.get_parameter('encoder_noise_std').value)
        self._imu_noise_std = float(self.get_parameter('imu_noise_std').value)
        publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)
        self._period = 1.0 / max(1e-6, publish_rate_hz)
        self._heartbeat = 0
        self._start_time = self.get_clock().now().nanoseconds / 1e9

        self._pub = self.create_publisher(String, '/arctos/hardware/mock_serial_packet', 10)
        self.create_timer(self._period, self._publish_packet)
        self.get_logger().info('Mock ESP32 serial packet generator started')

    def _publish_packet(self):
        now = self.get_clock().now()
        t = now.nanoseconds / 1e9 - self._start_time
        self._heartbeat += 1
        packet = {
            'timestamp': int(now.nanoseconds / 1000),
            'encoders': [
                0.25 * math.sin(0.35 * t + index * 0.45)
                + random.gauss(0.0, self._encoder_noise_std)
                for index in range(6)
            ],
            'limit_min': [False] * 6,
            'limit_max': [False] * 6,
            'imu': {
                'roll': random.gauss(0.0, self._imu_noise_std),
                'pitch': random.gauss(0.0, self._imu_noise_std),
                'yaw': 0.05 * math.sin(0.2 * t) + random.gauss(0.0, self._imu_noise_std),
            },
            'heartbeat': self._heartbeat,
        }
        msg = String()
        msg.data = json.dumps(packet)
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MockSerialPacketNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except rclpy._rclpy_pybind11.RCLError:
            pass


if __name__ == '__main__':
    main()
