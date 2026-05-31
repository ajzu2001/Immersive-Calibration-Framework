"""CalibrationObserver node – mock calibration result from reference poses.

Subscribes to /arctos/perception/reference_frame_pose, computes a position
error magnitude, and publishes a CalibrationResult on /arctos/calibration/result.
"""

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from arctos_interfaces.msg import CalibrationResult


class CalibrationObserver(Node):
    """Publishes mock calibration results from incoming reference poses."""

    def __init__(self):
        super().__init__('calibration_observer')

        self._pub = self.create_publisher(
            CalibrationResult, '/arctos/calibration/result', 10
        )

        self.create_subscription(
            PoseStamped,
            '/arctos/perception/reference_frame_pose',
            self._on_pose,
            10,
        )

        self._msg_count = 0
        self._last_log_time = self.get_clock().now()

        self.get_logger().info(
            'CalibrationObserver started – listening on '
            '/arctos/perception/reference_frame_pose'
        )

    def _on_pose(self, msg: PoseStamped):
        p = msg.pose.position
        position_error = math.sqrt(p.x * p.x + p.y * p.y + p.z * p.z)

        result = CalibrationResult()
        result.header = msg.header
        result.calibration_id = 'Mock calibration observation received'
        result.parameters = [position_error, 0.0]  # [pos_error_m, orient_error_rad]
        result.residual_error = position_error
        result.iterations = 0
        result.convergence_status = 1  # 1 = converged (success)
        result.execution_time = 0.0

        self._pub.publish(result)
        self._msg_count += 1

        # Log at most once per second
        now = self.get_clock().now()
        if (now - self._last_log_time).nanoseconds >= 1_000_000_000:
            self.get_logger().info(
                f'Observations: {self._msg_count}  '
                f'residual_error={position_error:.6f}'
            )
            self._last_log_time = now


def main(args=None):
    rclpy.init(args=args)
    node = CalibrationObserver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
