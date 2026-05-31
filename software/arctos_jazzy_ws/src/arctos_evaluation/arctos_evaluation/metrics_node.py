"""MetricsNode – computes evaluation metrics from twin sync error.

Subscribes to /arctos/twin/sync_error, computes mean/max/RMS absolute
joint error, publishes on /arctos/evaluation/metrics, and logs every second.
"""

import math

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray, MultiArrayDimension, MultiArrayLayout


class MetricsNode(Node):
    """Evaluation metrics publisher."""

    def __init__(self):
        super().__init__('metrics_node')

        self._pub = self.create_publisher(
            Float64MultiArray, '/arctos/evaluation/metrics', 10
        )

        self.create_subscription(
            JointState, '/arctos/twin/sync_error', self._on_sync_error, 10
        )

        # Latest computed metrics
        self._mean_abs: float = 0.0
        self._max_abs: float = 0.0
        self._rms: float = 0.0
        self._has_data = False

        # Log timer – 1 Hz
        self.create_timer(1.0, self._log_metrics)

        self.get_logger().info(
            'MetricsNode started – listening on /arctos/twin/sync_error'
        )

    def _on_sync_error(self, msg: JointState):
        if len(msg.position) == 0:
            return

        abs_errors = [abs(p) for p in msg.position]
        n = len(abs_errors)

        self._mean_abs = sum(abs_errors) / n
        self._max_abs = max(abs_errors)
        self._rms = math.sqrt(sum(e * e for e in abs_errors) / n)
        self._has_data = True

        # Publish
        out = Float64MultiArray()
        out.layout = MultiArrayLayout(
            dim=[MultiArrayDimension(label='metrics', size=3, stride=3)],
            data_offset=0,
        )
        # [mean_abs_error, max_abs_error, rms_error]
        out.data = [self._mean_abs, self._max_abs, self._rms]
        self._pub.publish(out)

    def _log_metrics(self):
        if not self._has_data:
            return
        self.get_logger().info(
            f'mean_abs={self._mean_abs:.6f}  '
            f'max_abs={self._max_abs:.6f}  '
            f'rms={self._rms:.6f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = MetricsNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
