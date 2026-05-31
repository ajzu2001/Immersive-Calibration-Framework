"""CalibrationManager node – maintains running calibration statistics.

Subscribes to /arctos/calibration/result and publishes a state vector
[observation_count, latest_residual, best_residual, average_residual]
on /arctos/calibration/state.
"""

import rclpy
from rclpy.node import Node

from arctos_interfaces.msg import CalibrationResult
from std_msgs.msg import Float64MultiArray, MultiArrayDimension, MultiArrayLayout


class CalibrationManager(Node):
    """Aggregates calibration results into running statistics."""

    def __init__(self):
        super().__init__('calibration_manager')

        self._pub = self.create_publisher(
            Float64MultiArray, '/arctos/calibration/state', 10
        )

        self.create_subscription(
            CalibrationResult, '/arctos/calibration/result', self._on_result, 10
        )

        self._count = 0
        self._latest_residual = 0.0
        self._best_residual = float('inf')
        self._residual_sum = 0.0

        self.create_timer(1.0, self._log_summary)

        self.get_logger().info(
            'CalibrationManager started – listening on /arctos/calibration/result'
        )

    def _on_result(self, msg: CalibrationResult):
        self._count += 1
        self._latest_residual = msg.residual_error
        self._residual_sum += msg.residual_error

        if msg.residual_error < self._best_residual:
            self._best_residual = msg.residual_error

        avg = self._residual_sum / self._count

        out = Float64MultiArray()
        out.layout = MultiArrayLayout(
            dim=[MultiArrayDimension(label='state', size=4, stride=4)],
            data_offset=0,
        )
        out.data = [
            float(self._count),
            self._latest_residual,
            self._best_residual,
            avg,
        ]
        self._pub.publish(out)

    def _log_summary(self):
        if self._count == 0:
            return
        avg = self._residual_sum / self._count
        self.get_logger().info(
            f'observations={self._count}  '
            f'latest={self._latest_residual:.6f}  '
            f'best={self._best_residual:.6f}  '
            f'avg={avg:.6f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = CalibrationManager()
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
