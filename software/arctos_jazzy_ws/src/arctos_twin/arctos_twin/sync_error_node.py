"""SyncError node – computes per-joint position error between twin and real.

Subscribes to /joint_states and /arctos/twin/state, matches joints by name,
and publishes the position difference on /arctos/twin/sync_error.
"""

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState
from arctos_interfaces.msg import TwinState


class SyncError(Node):
    """Publishes joint-level synchronisation error."""

    def __init__(self):
        super().__init__('sync_error')

        self._pub = self.create_publisher(
            JointState, '/arctos/twin/sync_error', 10
        )

        self._last_joint_state: JointState | None = None
        self._last_twin_state: TwinState | None = None
        self._both_received = False

        self.create_subscription(
            JointState, '/joint_states', self._on_joint_state, 10
        )
        self.create_subscription(
            TwinState, '/arctos/twin/state', self._on_twin_state, 10
        )

        self.get_logger().info('SyncError started – waiting for both streams')

    def _on_joint_state(self, msg: JointState):
        self._last_joint_state = msg
        self._try_publish()

    def _on_twin_state(self, msg: TwinState):
        self._last_twin_state = msg
        self._try_publish()

    def _try_publish(self):
        if self._last_joint_state is None or self._last_twin_state is None:
            return

        if not self._both_received:
            self._both_received = True
            self.get_logger().info('Both input streams available – publishing sync error')

        real = self._last_joint_state
        twin_js = self._last_twin_state.joint_state

        # Build lookup: joint name -> position from twin
        twin_lookup: dict[str, float] = {}
        for name, pos in zip(twin_js.name, twin_js.position):
            twin_lookup[name] = pos

        err = JointState()
        err.header.stamp = self.get_clock().now().to_msg()
        err.header.frame_id = 'twin_error'

        for name, real_pos in zip(real.name, real.position):
            if name in twin_lookup:
                err.name.append(name)
                err.position.append(twin_lookup[name] - real_pos)

        self._pub.publish(err)


def main(args=None):
    rclpy.init(args=args)
    node = SyncError()
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
