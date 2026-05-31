"""CalibrationSolver node – MVP placeholder solver.

Subscribes to /arctos/calibration/result, tracks running statistics,
computes improvement and correction estimates, and publishes a solver
solution on /arctos/calibration/solution.

NOTE: This is a placeholder/MVP solver. It does NOT perform real kinematic
optimisation (e.g. DH parameter fitting). It aggregates residual statistics
and publishes derived metrics as a CalibrationResult so downstream nodes
can consume a consistent message type.
"""

import rclpy
from rclpy.node import Node

from arctos_interfaces.msg import CalibrationResult


class CalibrationSolver(Node):
    """MVP calibration solver – residual tracking and improvement estimation."""

    def __init__(self):
        super().__init__('calibration_solver')

        self._pub = self.create_publisher(
            CalibrationResult, '/arctos/calibration/solution', 10
        )

        self.create_subscription(
            CalibrationResult, '/arctos/calibration/result',
            self._on_result, 10,
        )

        self._count = 0
        self._latest_residual = 0.0
        self._best_residual = float('inf')
        self._residual_sum = 0.0

        self.create_timer(1.0, self._log_summary)

        self.get_logger().info(
            'CalibrationSolver (MVP) started – '
            'listening on /arctos/calibration/result'
        )

    def _on_result(self, msg: CalibrationResult):
        self._count += 1
        self._latest_residual = msg.residual_error
        self._residual_sum += msg.residual_error

        if msg.residual_error < self._best_residual:
            self._best_residual = msg.residual_error

        avg = self._residual_sum / self._count
        improvement = self._latest_residual - self._best_residual
        correction_score = max(0.0, avg - self._best_residual)

        solution = CalibrationResult()
        solution.header.stamp = self.get_clock().now().to_msg()
        solution.header.frame_id = 'solver'
        solution.calibration_id = f'mvp_solver_iter_{self._count}'
        solution.parameters = [
            self._latest_residual,
            self._best_residual,
            avg,
            improvement,
            correction_score,
        ]
        solution.residual_error = self._best_residual
        solution.iterations = self._count
        # 1 = converged placeholder (MVP always reports converged)
        solution.convergence_status = 1
        solution.execution_time = 0.0

        self._pub.publish(solution)

    def _log_summary(self):
        if self._count == 0:
            return
        avg = self._residual_sum / self._count
        improvement = self._latest_residual - self._best_residual
        correction = max(0.0, avg - self._best_residual)
        self.get_logger().info(
            f'iter={self._count}  '
            f'best={self._best_residual:.6f}  '
            f'avg={avg:.6f}  '
            f'improvement={improvement:.6f}  '
            f'correction={correction:.6f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = CalibrationSolver()
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
