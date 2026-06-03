"""MVP calibration correction output from perception pose error.

This node is a dissertation-critical bridge between calibration perception and
future command compensation. It does not solve or optimize calibration
parameters. Instead, it publishes a simple gain-scaled Cartesian correction
vector derived from the current reference-frame pose.
"""

import math

import rclpy
from rclpy.node import Node

from arctos_interfaces.msg import CalibrationResult
from geometry_msgs.msg import PoseStamped, Vector3Stamped


class CalibrationCorrectionNode(Node):
    """Publish an MVP correction vector from the current reference pose."""

    def __init__(self):
        super().__init__('calibration_correction_node')

        self.declare_parameter('target_distance', 0.45)
        self.declare_parameter('correction_gain', 0.5)

        self._target_distance = float(self.get_parameter('target_distance').value)
        self._correction_gain = float(self.get_parameter('correction_gain').value)
        self._latest_solution: CalibrationResult | None = None
        self._latest_correction: Vector3Stamped | None = None

        self._pub = self.create_publisher(
            Vector3Stamped, '/arctos/calibration/correction', 10
        )
        self.create_subscription(
            CalibrationResult,
            '/arctos/calibration/solution',
            self._on_solution,
            10,
        )
        self.create_subscription(
            PoseStamped,
            '/arctos/perception/reference_frame_pose',
            self._on_reference_pose,
            10,
        )

        self.create_timer(1.0, self._log_correction)

        self.get_logger().info(
            'CalibrationCorrectionNode started - MVP correction output on '
            '/arctos/calibration/correction '
            f'(target_distance={self._target_distance:.3f}, '
            f'correction_gain={self._correction_gain:.3f})'
        )

    def _on_solution(self, msg: CalibrationResult):
        self._latest_solution = msg

    def _on_reference_pose(self, msg: PoseStamped):
        target_distance = float(self.get_parameter('target_distance').value)
        correction_gain = float(self.get_parameter('correction_gain').value)
        self._target_distance = target_distance
        self._correction_gain = correction_gain

        out = Vector3Stamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = msg.header.frame_id
        out.vector.x = correction_gain * (-msg.pose.position.x)
        out.vector.y = correction_gain * (-msg.pose.position.y)
        out.vector.z = correction_gain * (target_distance - msg.pose.position.z)

        self._latest_correction = out
        self._pub.publish(out)

    def _log_correction(self):
        if self._latest_correction is None:
            return

        v = self._latest_correction.vector
        magnitude = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
        solution_state = 'solution received' if self._latest_solution else 'no solution yet'
        self.get_logger().info(
            'MVP correction vector: '
            f'x={v.x:.4f} y={v.y:.4f} z={v.z:.4f} '
            f'|mag|={magnitude:.4f} ({solution_state})'
        )


def main(args=None):
    rclpy.init(args=args)
    node = CalibrationCorrectionNode()
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
