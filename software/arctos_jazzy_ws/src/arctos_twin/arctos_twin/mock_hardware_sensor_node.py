"""Mock hardware sensor publisher for v17 sensor fusion MVP.

Simulates the future ESP32 acquisition stack: six AS5600 encoder positions,
limit switches, and IMU orientation. This is a software-only stand-in for the
future real robot hardware interface.
"""

import math
import random

import rclpy
from rclpy.node import Node

from arctos_interfaces.msg import HardwareJointState


class MockHardwareSensorNode(Node):
    """Publish noisy mock hardware joint sensor data."""

    JOINT_NAMES = [f'joint_{index + 1}' for index in range(6)]

    def __init__(self):
        super().__init__('mock_hardware_sensor_node')

        self.declare_parameter('publish_rate_hz', 20.0)
        self.declare_parameter('encoder_noise_std', 0.002)
        self.declare_parameter('imu_noise_std', 0.005)

        self._encoder_noise_std = float(self.get_parameter('encoder_noise_std').value)
        self._imu_noise_std = float(self.get_parameter('imu_noise_std').value)
        publish_rate_hz = float(self.get_parameter('publish_rate_hz').value)
        period = 1.0 / max(1e-6, publish_rate_hz)
        self._start_time = self.get_clock().now().nanoseconds / 1e9

        self._pub = self.create_publisher(
            HardwareJointState, '/arctos/hardware/joint_sensor_state', 10
        )
        self.create_timer(period, self._publish)

        self.get_logger().info(
            'Mock hardware sensor node started - publishing '
            '/arctos/hardware/joint_sensor_state'
        )

    def _publish(self):
        now = self.get_clock().now()
        t = now.nanoseconds / 1e9 - self._start_time

        msg = HardwareJointState()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = 'hardware_sensor_frame'
        msg.joint_names = list(self.JOINT_NAMES)
        msg.encoder_positions = [
            0.25 * math.sin(0.35 * t + index * 0.45)
            + random.gauss(0.0, self._encoder_noise_std)
            for index in range(6)
        ]
        msg.limit_switch_min = [False] * 6
        msg.limit_switch_max = [False] * 6
        msg.imu_roll = random.gauss(0.0, self._imu_noise_std)
        msg.imu_pitch = random.gauss(0.0, self._imu_noise_std)
        msg.imu_yaw = 0.05 * math.sin(0.2 * t) + random.gauss(0.0, self._imu_noise_std)
        msg.confidence = 0.95
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MockHardwareSensorNode()
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
