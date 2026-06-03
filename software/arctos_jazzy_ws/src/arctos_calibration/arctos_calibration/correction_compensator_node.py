"""First compensation layer for raw-vs-compensated target comparison.

This node applies the MVP calibration correction vector to the incoming raw
reference-frame pose and republishes the resulting compensated target. It does
not command hardware; it prepares a PoseStamped target for evaluation and later
command-compensation work.
"""

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped, Vector3Stamped


class CorrectionCompensatorNode(Node):
    """Apply the latest correction vector to incoming reference poses."""

    def __init__(self):
        super().__init__('correction_compensator_node')

        self._latest_correction: Vector3Stamped | None = None
        self._latest_raw: PoseStamped | None = None
        self._latest_compensated: PoseStamped | None = None

        self._pub = self.create_publisher(
            PoseStamped, '/arctos/calibration/compensated_target', 10
        )
        self.create_subscription(
            PoseStamped,
            '/arctos/perception/reference_frame_pose',
            self._on_reference_pose,
            10,
        )
        self.create_subscription(
            Vector3Stamped,
            '/arctos/calibration/correction',
            self._on_correction,
            10,
        )

        self.create_timer(1.0, self._log_compensation)

        self.get_logger().info(
            'CorrectionCompensatorNode started - publishing '
            '/arctos/calibration/compensated_target'
        )

    def _on_correction(self, msg: Vector3Stamped):
        self._latest_correction = msg

    def _on_reference_pose(self, msg: PoseStamped):
        self._latest_raw = msg
        if self._latest_correction is None:
            return

        c = self._latest_correction.vector
        out = PoseStamped()
        out.header = msg.header
        out.pose.position.x = msg.pose.position.x + c.x
        out.pose.position.y = msg.pose.position.y + c.y
        out.pose.position.z = msg.pose.position.z + c.z
        out.pose.orientation = msg.pose.orientation

        self._latest_compensated = out
        self._pub.publish(out)

    def _log_compensation(self):
        if self._latest_raw is None or self._latest_correction is None:
            return
        if self._latest_compensated is None:
            return

        raw = self._latest_raw.pose.position
        corr = self._latest_correction.vector
        comp = self._latest_compensated.pose.position
        raw_error = math.sqrt(raw.x * raw.x + raw.y * raw.y + raw.z * raw.z)
        comp_error = math.sqrt(comp.x * comp.x + comp.y * comp.y + comp.z * comp.z)

        self.get_logger().info(
            'compensation: '
            f'raw=({raw.x:.4f}, {raw.y:.4f}, {raw.z:.4f}) '
            f'correction=({corr.x:.4f}, {corr.y:.4f}, {corr.z:.4f}) '
            f'compensated=({comp.x:.4f}, {comp.y:.4f}, {comp.z:.4f}) '
            f'raw_error={raw_error:.4f} compensated_error={comp_error:.4f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = CorrectionCompensatorNode()
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
