"""MetricsNode – unified evaluation metrics from twin and calibration.

Subscribes to /arctos/twin/sync_error, /arctos/calibration/state,
and /arctos/calibration/correction,
computes a combined metrics vector including correction magnitude,
publishes on /arctos/evaluation/metrics,
and logs every second.
"""

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Vector3Stamped
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray, MultiArrayDimension, MultiArrayLayout


class MetricsNode(Node):
    """Unified evaluation metrics publisher."""

    def __init__(self):
        super().__init__('metrics_node')

        self._pub = self.create_publisher(
            Float64MultiArray, '/arctos/evaluation/metrics', 10
        )

        self.create_subscription(
            JointState, '/arctos/twin/sync_error', self._on_sync_error, 10
        )
        self.create_subscription(
            Float64MultiArray, '/arctos/calibration/state', self._on_cal_state, 10
        )
        self.create_subscription(
            Vector3Stamped,
            '/arctos/calibration/correction',
            self._on_correction,
            10,
        )

        # Twin sync metrics
        self._mean_abs: float = 0.0
        self._max_abs: float = 0.0
        self._rms: float = 0.0
        self._has_twin = False

        # Calibration state: [count, latest, best, avg]
        self._cal_latest: float = 0.0
        self._cal_best: float = 0.0
        self._cal_avg: float = 0.0
        self._has_cal = False

        # MVP correction output metric
        self._correction_mag: float = 0.0
        self._has_correction = False

        # Log timer – 1 Hz
        self.create_timer(1.0, self._log_metrics)

        self.get_logger().info(
            'MetricsNode started - listening on '
            '/arctos/twin/sync_error, /arctos/calibration/state, '
            '/arctos/calibration/correction'
        )

    def _on_sync_error(self, msg: JointState):
        if len(msg.position) == 0:
            return

        abs_errors = [abs(p) for p in msg.position]
        n = len(abs_errors)

        self._mean_abs = sum(abs_errors) / n
        self._max_abs = max(abs_errors)
        self._rms = math.sqrt(sum(e * e for e in abs_errors) / n)
        self._has_twin = True
        self._publish()

    def _on_cal_state(self, msg: Float64MultiArray):
        if len(msg.data) < 4:
            return
        # msg.data = [count, latest_residual, best_residual, avg_residual]
        self._cal_latest = msg.data[1]
        self._cal_best = msg.data[2]
        self._cal_avg = msg.data[3]
        self._has_cal = True
        self._publish()

    def _on_correction(self, msg: Vector3Stamped):
        v = msg.vector
        self._correction_mag = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
        self._has_correction = True
        self._publish()

    def _publish(self):
        out = Float64MultiArray()
        out.layout = MultiArrayLayout(
            dim=[MultiArrayDimension(label='metrics', size=7, stride=7)],
            data_offset=0,
        )
        out.data = [
            self._mean_abs,
            self._max_abs,
            self._rms,
            self._cal_latest,
            self._cal_best,
            self._cal_avg,
            self._correction_mag,
        ]
        self._pub.publish(out)

    def _log_metrics(self):
        if not (self._has_twin or self._has_cal or self._has_correction):
            return
        parts = []
        if self._has_twin:
            parts.append(
                f'twin: mean={self._mean_abs:.6f} max={self._max_abs:.6f} '
                f'rms={self._rms:.6f}'
            )
        if self._has_cal:
            parts.append(
                f'cal: latest={self._cal_latest:.6f} best={self._cal_best:.6f} '
                f'avg={self._cal_avg:.6f}'
            )
        if self._has_correction:
            parts.append(f'correction: |mag|={self._correction_mag:.6f}')
        self.get_logger().info('  |  '.join(parts))


def main(args=None):
    rclpy.init(args=args)
    node = MetricsNode()
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
