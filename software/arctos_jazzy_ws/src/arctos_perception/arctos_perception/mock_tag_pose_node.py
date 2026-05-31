"""MockTagPose node – publishes a reference frame pose for calibration development.

Publishes a fixed PoseStamped on /arctos/perception/reference_frame_pose at 10 Hz.
Optional Gaussian noise can be added via the 'noise_stddev' parameter.
"""

import random

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped


class MockTagPose(Node):
    """Publishes a mock fiducial / reference-frame pose."""

    def __init__(self):
        super().__init__('mock_tag_pose')

        self.declare_parameter('frame_id', 'camera_link')
        self.declare_parameter('noise_stddev', 0.0)

        # Fixed reference pose (1 m in front of camera, identity orientation)
        self.declare_parameter('pos_x', 0.5)
        self.declare_parameter('pos_y', 0.0)
        self.declare_parameter('pos_z', 0.3)

        self._pub = self.create_publisher(
            PoseStamped, '/arctos/perception/reference_frame_pose', 10
        )

        self.create_timer(0.1, self._publish)  # 10 Hz

        self.get_logger().info(
            'MockTagPose started – publishing at 10 Hz on '
            '/arctos/perception/reference_frame_pose'
        )

    def _publish(self):
        noise = self.get_parameter('noise_stddev').value

        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.get_parameter('frame_id').value

        msg.pose.position.x = self.get_parameter('pos_x').value
        msg.pose.position.y = self.get_parameter('pos_y').value
        msg.pose.position.z = self.get_parameter('pos_z').value

        if noise > 0.0:
            msg.pose.position.x += random.gauss(0.0, noise)
            msg.pose.position.y += random.gauss(0.0, noise)
            msg.pose.position.z += random.gauss(0.0, noise)

        # Identity orientation
        msg.pose.orientation.w = 1.0

        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MockTagPose()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
