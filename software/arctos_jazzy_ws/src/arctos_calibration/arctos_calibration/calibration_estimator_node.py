"""Calibration Parameter Estimation MVP.

This node estimates a dissertation-target calibration model from perception,
correction, and evaluation streams. It is not the final optimizer. The MVP maps
persistent observed error into interpretable parameter estimates for:
joint zero offsets, link length errors, base frame error, and tool frame error.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev

import rclpy
from rclpy.node import Node

from arctos_interfaces.msg import CalibrationModel
from geometry_msgs.msg import PoseStamped, Vector3Stamped
from std_msgs.msg import Float64MultiArray


class CalibrationEstimatorNode(Node):
    """Estimate and persist a CalibrationModel from live MVP evidence streams."""

    def __init__(self):
        super().__init__('calibration_estimator_node')

        self.declare_parameter(
            'output_directory',
            '~/Immersive-Calibration-Framework/software/arctos_jazzy_ws/results',
        )
        self.declare_parameter('joint_count', 6)
        self.declare_parameter('history_limit', 100)

        self._output_directory = Path(
            str(self.get_parameter('output_directory').value)
        ).expanduser()
        self._joint_count = int(self.get_parameter('joint_count').value)
        self._history_limit = int(self.get_parameter('history_limit').value)

        self._poses: list[tuple[float, float, float]] = []
        self._corrections: list[tuple[float, float, float]] = []
        self._residuals: list[float] = []
        self._latest_model: CalibrationModel | None = None

        self._pub = self.create_publisher(
            CalibrationModel, '/arctos/calibration/model', 10
        )
        self.create_subscription(
            PoseStamped,
            '/arctos/perception/reference_frame_pose',
            self._on_pose,
            10,
        )
        self.create_subscription(
            Vector3Stamped,
            '/arctos/calibration/correction',
            self._on_correction,
            10,
        )
        self.create_subscription(
            Float64MultiArray,
            '/arctos/evaluation/metrics',
            self._on_metrics,
            10,
        )

        self.create_timer(1.0, self._publish_model)

        self.get_logger().info(
            'Calibration Parameter Estimation MVP started - publishing '
            '/arctos/calibration/model'
        )

    def _on_pose(self, msg: PoseStamped):
        p = msg.pose.position
        self._append_limited(self._poses, (p.x, p.y, p.z))

    def _on_correction(self, msg: Vector3Stamped):
        v = msg.vector
        self._append_limited(self._corrections, (v.x, v.y, v.z))

    def _on_metrics(self, msg: Float64MultiArray):
        if len(msg.data) >= 9 and msg.data[8] > 0.0:
            residual = float(msg.data[8])
        elif len(msg.data) >= 8 and msg.data[7] > 0.0:
            residual = float(msg.data[7])
        elif len(msg.data) >= 4:
            residual = abs(float(msg.data[3]))
        else:
            return
        self._append_limited(self._residuals, residual)

    def _publish_model(self):
        if not (self._poses or self._corrections or self._residuals):
            return

        model = self._estimate_model()
        self._latest_model = model
        self._pub.publish(model)
        self._save_model(model)

        self.get_logger().info(
            'Calibration model MVP: '
            f'confidence={model.confidence:.3f} '
            f'base=({model.base_offset_x:.4f}, {model.base_offset_y:.4f}, {model.base_offset_z:.4f}) '
            f'tool=({model.tool_offset_x:.4f}, {model.tool_offset_y:.4f}, {model.tool_offset_z:.4f})'
        )

    def _estimate_model(self) -> CalibrationModel:
        avg_pose = self._average_xyz(self._poses)
        avg_correction = self._average_xyz(self._corrections)
        avg_residual = mean(self._residuals) if self._residuals else 0.0
        residual_std = pstdev(self._residuals) if len(self._residuals) > 1 else 0.0

        model = CalibrationModel()

        correction_components = list(avg_correction)
        joint_offsets = []
        for index in range(self._joint_count):
            component = correction_components[index % 3]
            scale = 0.10 if index < 3 else 0.05
            joint_offsets.append(scale * component)
        model.joint_zero_offsets = joint_offsets

        residual_scale = max(avg_residual, 0.0) * 0.01
        model.link_length_errors = [
            residual_scale * (1.0 + 0.05 * index) for index in range(self._joint_count)
        ]

        model.base_offset_x = -0.10 * avg_pose[0]
        model.base_offset_y = -0.10 * avg_pose[1]
        model.base_offset_z = -0.10 * avg_pose[2]

        model.tool_offset_x = 0.50 * avg_correction[0]
        model.tool_offset_y = 0.50 * avg_correction[1]
        model.tool_offset_z = 0.50 * avg_correction[2]

        sample_factor = min(1.0, len(self._residuals) / 50.0)
        consistency = 1.0 / (1.0 + 10.0 * residual_std)
        model.confidence = max(0.0, min(1.0, sample_factor * consistency))
        return model

    def _save_model(self, model: CalibrationModel):
        self._output_directory.mkdir(parents=True, exist_ok=True)
        path = self._output_directory / 'calibration_model.json'
        payload = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'joint_zero_offsets': list(model.joint_zero_offsets),
            'link_length_errors': list(model.link_length_errors),
            'base_offset_x': model.base_offset_x,
            'base_offset_y': model.base_offset_y,
            'base_offset_z': model.base_offset_z,
            'tool_offset_x': model.tool_offset_x,
            'tool_offset_y': model.tool_offset_y,
            'tool_offset_z': model.tool_offset_z,
            'confidence': model.confidence,
        }
        with path.open('w') as f:
            json.dump(payload, f, indent=2)
            f.write('\n')

    def _average_xyz(self, values: list[tuple[float, float, float]]) -> tuple[float, float, float]:
        if not values:
            return (0.0, 0.0, 0.0)
        return (
            mean(v[0] for v in values),
            mean(v[1] for v in values),
            mean(v[2] for v in values),
        )

    def _append_limited(self, target: list, value):
        target.append(value)
        if len(target) > self._history_limit:
            del target[0]


def main(args=None):
    rclpy.init(args=args)
    node = CalibrationEstimatorNode()
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
