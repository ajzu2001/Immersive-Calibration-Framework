"""Sensor fusion MVP for hardware encoder source of truth.

Uses encoder positions from /arctos/hardware/joint_sensor_state as the primary
joint estimate and optionally compares against /joint_states when command/sim
state is available. This is an MVP fusion layer, not a final EKF.
"""

import rclpy
from rclpy.node import Node

from arctos_interfaces.msg import HardwareJointState
from sensor_msgs.msg import JointState


class SensorFusionNode(Node):
    """Fuse hardware encoder state into a canonical JointState stream."""

    def __init__(self):
        super().__init__('sensor_fusion_node')

        self._latest_hardware: HardwareJointState | None = None
        self._latest_joint_state: JointState | None = None
        self._latest_avg_difference: float | None = None

        self._pub = self.create_publisher(
            JointState, '/arctos/twin/fused_joint_state', 10
        )
        self.create_subscription(
            HardwareJointState,
            '/arctos/hardware/joint_sensor_state',
            self._on_hardware_state,
            10,
        )
        self.create_subscription(JointState, '/joint_states', self._on_joint_state, 10)
        self.create_timer(1.0, self._log_status)

        self.get_logger().info(
            'SensorFusionNode MVP started - encoder positions are primary source'
        )

    def _on_hardware_state(self, msg: HardwareJointState):
        self._latest_hardware = msg
        fused = JointState()
        fused.header = msg.header
        fused.name = list(msg.joint_names)
        fused.position = list(msg.encoder_positions)
        fused.velocity = []
        fused.effort = []
        self._pub.publish(fused)
        self._update_difference(fused)

    def _on_joint_state(self, msg: JointState):
        self._latest_joint_state = msg
        if self._latest_hardware is not None:
            fused = JointState()
            fused.name = list(self._latest_hardware.joint_names)
            fused.position = list(self._latest_hardware.encoder_positions)
            self._update_difference(fused)

    def _update_difference(self, fused: JointState):
        if self._latest_joint_state is None:
            self._latest_avg_difference = None
            return
        command_by_name = dict(zip(self._latest_joint_state.name, self._latest_joint_state.position))
        differences = []
        for name, encoder_position in zip(fused.name, fused.position):
            if name in command_by_name:
                differences.append(abs(encoder_position - command_by_name[name]))
        if differences:
            self._latest_avg_difference = sum(differences) / len(differences)

    def _log_status(self):
        if self._latest_hardware is None:
            self.get_logger().info('Sensor fusion waiting for hardware joint sensor state')
            return
        if self._latest_avg_difference is None:
            self.get_logger().info(
                'Sensor fusion publishing encoder-derived state; no /joint_states comparison yet'
            )
            return
        self.get_logger().info(
            f'encoder-vs-joint-state average difference={self._latest_avg_difference:.6f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = SensorFusionNode()
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
