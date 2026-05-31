"""TwinMonitor node – MVP digital twin state publisher.

Subscribes to /joint_states and republishes as arctos_interfaces/msg/TwinState
on /arctos/twin/state at the incoming message rate.
"""

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped
from builtin_interfaces.msg import Duration

from arctos_interfaces.msg import TwinState


class TwinMonitor(Node):
    """Minimal digital-twin state monitor."""

    def __init__(self):
        super().__init__('twin_monitor')

        # Publisher
        self._pub = self.create_publisher(TwinState, '/arctos/twin/state', 10)

        # Subscriber
        self._sub = self.create_subscription(
            JointState, '/joint_states', self._on_joint_state, 10
        )

        self.get_logger().info('TwinMonitor started – listening on /joint_states')

    def _on_joint_state(self, msg: JointState):
        twin = TwinState()
        twin.header.stamp = self.get_clock().now().to_msg()
        twin.header.frame_id = 'world'

        # Copy incoming joint state
        twin.joint_state = msg

        # Identity end-effector pose (placeholder until FK is wired)
        ee = PoseStamped()
        ee.header = twin.header
        ee.pose.orientation.w = 1.0
        twin.end_effector_pose = ee

        # No time offset in MVP
        twin.time_offset = Duration()

        # Perfect sync for passthrough
        twin.sync_quality = 1.0

        self._pub.publish(twin)


def main(args=None):
    rclpy.init(args=args)
    node = TwinMonitor()
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
