"""Unity/VR bridge MVP for the Arctos digital twin framework.

This node exposes ROS 2 digital twin, perception, calibration correction, and
evaluation metrics as a Unity-friendly JSON string. It is an MVP bridge for VR
visualization and does not require Unity-side code to be present.
"""

import json

import rclpy
from rclpy.node import Node

from arctos_interfaces.msg import TwinState
from geometry_msgs.msg import PoseStamped, Vector3Stamped
from std_msgs.msg import Float64MultiArray, String


class UnityBridgeNode(Node):
    """Publish a 10 Hz JSON snapshot for Unity/VR clients."""

    def __init__(self):
        super().__init__('unity_bridge_node')

        self._twin_state: TwinState | None = None
        self._tag_pose: PoseStamped | None = None
        self._correction: Vector3Stamped | None = None
        self._metrics: Float64MultiArray | None = None

        self._pub = self.create_publisher(String, '/arctos/vr/unity_state', 10)

        self.create_subscription(
            TwinState, '/arctos/twin/state', self._on_twin_state, 10
        )
        self.create_subscription(
            PoseStamped,
            '/arctos/perception/reference_frame_pose',
            self._on_tag_pose,
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

        self.create_timer(0.1, self._publish_state)
        self.create_timer(1.0, self._log_status)

        self.get_logger().info(
            'UnityBridgeNode MVP started - publishing /arctos/vr/unity_state'
        )

    def _on_twin_state(self, msg: TwinState):
        self._twin_state = msg

    def _on_tag_pose(self, msg: PoseStamped):
        self._tag_pose = msg

    def _on_correction(self, msg: Vector3Stamped):
        self._correction = msg

    def _on_metrics(self, msg: Float64MultiArray):
        self._metrics = msg

    def _publish_state(self):
        msg = String()
        msg.data = json.dumps(self._state_dict())
        self._pub.publish(msg)

    def _state_dict(self) -> dict:
        return {
            'timestamp': self.get_clock().now().nanoseconds / 1e9,
            'joint_names': self._joint_names(),
            'joint_positions': self._joint_positions(),
            'tag_pose': self._tag_pose_dict(),
            'correction': self._correction_dict(),
            'metrics': self._metrics_dict(),
        }

    def _joint_names(self):
        if self._twin_state is None:
            return None
        return list(self._twin_state.joint_state.name)

    def _joint_positions(self):
        if self._twin_state is None:
            return None
        return list(self._twin_state.joint_state.position)

    def _tag_pose_dict(self):
        if self._tag_pose is None:
            return {'x': None, 'y': None, 'z': None}
        p = self._tag_pose.pose.position
        return {'x': p.x, 'y': p.y, 'z': p.z}

    def _correction_dict(self):
        if self._correction is None:
            return {'x': None, 'y': None, 'z': None}
        v = self._correction.vector
        return {'x': v.x, 'y': v.y, 'z': v.z}

    def _metrics_dict(self):
        values = [] if self._metrics is None else list(self._metrics.data)
        return {
            'mean_twin_error': self._metric(values, 0),
            'max_twin_error': self._metric(values, 1),
            'rms_twin_error': self._metric(values, 2),
            'raw_error': self._metric(values, 7),
            'compensated_error': self._metric(values, 8),
            'improvement_percent': self._metric(values, 9),
        }

    @staticmethod
    def _metric(values, index: int):
        if len(values) <= index:
            return None
        return values[index]

    def _log_status(self):
        self.get_logger().info(
            'Unity bridge status: '
            f'twin={self._twin_state is not None} '
            f'tag_pose={self._tag_pose is not None} '
            f'correction={self._correction is not None} '
            f'metrics={self._metrics is not None}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = UnityBridgeNode()
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
