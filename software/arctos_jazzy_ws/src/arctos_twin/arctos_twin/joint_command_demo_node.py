"""JointCommandDemo node – publishes safe sinusoidal joint commands.

Sends position commands to /arm_position_controller/commands to produce
visible robot motion in Gazebo. Only joint1 moves by default; all other
joints hold at 0.0.

Parameters:
  amplitude  (float, default 0.3)  — peak displacement in radians
  frequency  (float, default 0.2)  — oscillation frequency in Hz
  rate       (float, default 20.0) — publish rate in Hz
"""

import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float64MultiArray

NUM_JOINTS = 6


class JointCommandDemo(Node):
    """Publishes a repeating sinusoidal motion for demonstration."""

    def __init__(self):
        super().__init__('joint_command_demo')

        self.declare_parameter('amplitude', 0.3)
        self.declare_parameter('frequency', 0.2)
        self.declare_parameter('rate', 20.0)

        self._pub = self.create_publisher(
            Float64MultiArray, '/arm_position_controller/commands', 10
        )

        rate = self.get_parameter('rate').value
        self.create_timer(1.0 / rate, self._publish)
        self._start_time = self.get_clock().now()

        amp = self.get_parameter('amplitude').value
        freq = self.get_parameter('frequency').value
        self.get_logger().info(
            f'JointCommandDemo started — joint1 sine wave '
            f'amp={amp:.2f} rad, freq={freq:.2f} Hz, rate={rate:.0f} Hz'
        )

    def _publish(self):
        amp = self.get_parameter('amplitude').value
        freq = self.get_parameter('frequency').value
        elapsed = (self.get_clock().now() - self._start_time).nanoseconds * 1e-9

        positions = [0.0] * NUM_JOINTS
        positions[0] = amp * math.sin(2.0 * math.pi * freq * elapsed)

        msg = Float64MultiArray()
        msg.data = positions
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = JointCommandDemo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Send zero position before shutting down
        stop = Float64MultiArray()
        stop.data = [0.0] * NUM_JOINTS
        node._pub.publish(stop)
        node.get_logger().info('Sent zero position — shutting down')
        node.destroy_node()
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except rclpy._rclpy_pybind11.RCLError:
            pass


if __name__ == '__main__':
    main()
