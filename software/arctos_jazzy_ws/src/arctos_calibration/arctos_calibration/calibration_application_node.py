"""Calibration Application Layer MVP.

This node validates and clamps the estimated calibration model before publishing
an applied model and a JSON twin-adjustment state. It simulates how an imperfect
Digital Twin would be updated by calibration without modifying URDF, Gazebo,
ros2_control, or controller configuration.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import rclpy
from rclpy.node import Node

from arctos_interfaces.msg import CalibrationModel
from std_msgs.msg import Float64MultiArray, String


class CalibrationApplicationNode(Node):
    """Apply safety limits to calibration estimates and publish simulated state."""

    JOINT_LIMIT_RAD = math.radians(10.0)
    LINK_LIMIT_M = 0.010
    FRAME_LIMIT_M = 0.050

    def __init__(self):
        super().__init__('calibration_application_node')

        self.declare_parameter(
            'output_directory',
            '~/Immersive-Calibration-Framework/software/arctos_jazzy_ws/results',
        )
        self._output_directory = Path(
            str(self.get_parameter('output_directory').value)
        ).expanduser()
        self._latest_model_quality = 0.0
        self._latest_raw_error = 0.0
        self._latest_residual = 0.0

        self._model_pub = self.create_publisher(
            CalibrationModel, '/arctos/calibration/applied_model', 10
        )
        self._state_pub = self.create_publisher(
            String, '/arctos/calibration/twin_adjustment_state', 10
        )
        self.create_subscription(
            CalibrationModel, '/arctos/calibration/model', self._on_model, 10
        )
        self.create_subscription(
            Float64MultiArray, '/arctos/evaluation/metrics', self._on_metrics, 10
        )

        self.get_logger().info(
            'Calibration Application Layer MVP started - applying safety limits only'
        )

    def _on_metrics(self, msg: Float64MultiArray):
        if len(msg.data) >= 9:
            self._latest_raw_error = max(0.0, float(msg.data[7]))
            self._latest_residual = max(0.0, float(msg.data[8]))
        elif len(msg.data) >= 4:
            self._latest_residual = abs(float(msg.data[3]))

    def _on_model(self, msg: CalibrationModel):
        applied, clamped = self._validated_model(msg)
        self._latest_model_quality = self._model_quality(applied.confidence)

        self._model_pub.publish(applied)
        state_msg = String()
        state_payload = self._state_payload(applied)
        state_msg.data = json.dumps(state_payload)
        self._state_pub.publish(state_msg)
        self._save_applied_model(applied, state_payload)

        self.get_logger().info(
            'received calibration model: '
            f'confidence={msg.confidence:.3f} '
            f'joint_count={len(msg.joint_zero_offsets)} '
            f'link_count={len(msg.link_length_errors)}'
        )
        self.get_logger().info(
            f'clamped values: {clamped if clamped else "none"} '
            f'applied_confidence={applied.confidence:.3f}'
        )

    def _validated_model(self, msg: CalibrationModel):
        clamped: list[str] = []
        applied = CalibrationModel()
        applied.joint_zero_offsets = [
            self._clamp(value, self.JOINT_LIMIT_RAD, f'joint_zero_offsets[{i}]', clamped)
            for i, value in enumerate(msg.joint_zero_offsets)
        ]
        applied.link_length_errors = [
            self._clamp(value, self.LINK_LIMIT_M, f'link_length_errors[{i}]', clamped)
            for i, value in enumerate(msg.link_length_errors)
        ]

        applied.base_offset_x = self._clamp(msg.base_offset_x, self.FRAME_LIMIT_M, 'base_offset_x', clamped)
        applied.base_offset_y = self._clamp(msg.base_offset_y, self.FRAME_LIMIT_M, 'base_offset_y', clamped)
        applied.base_offset_z = self._clamp(msg.base_offset_z, self.FRAME_LIMIT_M, 'base_offset_z', clamped)
        applied.tool_offset_x = self._clamp(msg.tool_offset_x, self.FRAME_LIMIT_M, 'tool_offset_x', clamped)
        applied.tool_offset_y = self._clamp(msg.tool_offset_y, self.FRAME_LIMIT_M, 'tool_offset_y', clamped)
        applied.tool_offset_z = self._clamp(msg.tool_offset_z, self.FRAME_LIMIT_M, 'tool_offset_z', clamped)
        applied.confidence = max(0.0, min(1.0, float(msg.confidence)))
        if applied.confidence != msg.confidence:
            clamped.append('confidence')
        return applied, clamped

    @staticmethod
    def _clamp(value: float, limit: float, name: str, clamped: list[str]) -> float:
        value = float(value)
        limited = max(-limit, min(limit, value))
        if limited != value:
            clamped.append(name)
        return limited

    def _model_quality(self, confidence: float) -> float:
        if self._latest_raw_error > 1e-12:
            normalized_residual = min(1.0, self._latest_residual / self._latest_raw_error)
        else:
            normalized_residual = min(1.0, self._latest_residual / (1.0 + self._latest_residual))
        return max(0.0, min(1.0, confidence * (1.0 - normalized_residual)))

    def _state_payload(self, model: CalibrationModel) -> dict:
        return {
            'joint_zero_offsets': list(model.joint_zero_offsets),
            'link_length_errors': list(model.link_length_errors),
            'base_offset': {
                'x': model.base_offset_x,
                'y': model.base_offset_y,
                'z': model.base_offset_z,
            },
            'tool_offset': {
                'x': model.tool_offset_x,
                'y': model.tool_offset_y,
                'z': model.tool_offset_z,
            },
            'confidence': model.confidence,
        }

    def _save_applied_model(self, model: CalibrationModel, state_payload: dict):
        self._output_directory.mkdir(parents=True, exist_ok=True)
        path = self._output_directory / 'applied_calibration_model.json'
        payload = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            **state_payload,
            'model_quality': self._latest_model_quality,
        }
        with path.open('w') as f:
            json.dump(payload, f, indent=2)
            f.write('\n')


def main(args=None):
    rclpy.init(args=args)
    node = CalibrationApplicationNode()
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
