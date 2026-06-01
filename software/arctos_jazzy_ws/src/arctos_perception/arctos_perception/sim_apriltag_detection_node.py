"""Simulated AprilTag detection publisher — SIMULATION TEST BRIDGE ONLY.

Publishes a synthetic AprilTagDetectionArray on /apriltag/detections and a
matching TF transform (camera_link → 36h11:<tag_id>) at 10 Hz.  This allows
tag_pose_node to be exercised end-to-end without a real camera or Gazebo
rendering.

THIS NODE IS NOT REAL PERCEPTION.  It exists solely to close the data loop
during software integration testing.
"""

import math
import random

import rclpy
from rclpy.node import Node

from apriltag_msgs.msg import AprilTagDetection, AprilTagDetectionArray
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class SimAprilTagDetection(Node):
    """Publishes synthetic AprilTag detections + TF for testing."""

    def __init__(self):
        super().__init__('sim_apriltag_detection')

        # ── Parameters ──────────────────────────────────────────────
        self.declare_parameter('tag_id', 0)
        self.declare_parameter('tag_family', '36h11')
        self.declare_parameter('parent_frame', 'camera_link')
        # Simulated tag position relative to camera (metres).
        self.declare_parameter('tag_x', 0.35)
        self.declare_parameter('tag_y', 0.0)
        self.declare_parameter('tag_z', -0.10)
        # Optional Gaussian noise on the simulated pose (metres).
        self.declare_parameter('noise_stddev', 0.002)
        self.declare_parameter('publish_rate', 10.0)

        # ── Publishers ──────────────────────────────────────────────
        self._det_pub = self.create_publisher(
            AprilTagDetectionArray, '/apriltag/detections', 10
        )
        self._tf_broadcaster = TransformBroadcaster(self)

        rate = self.get_parameter('publish_rate').value
        self.create_timer(1.0 / rate, self._publish)

        tag_id = self.get_parameter('tag_id').value
        family = self.get_parameter('tag_family').value
        self.get_logger().info(
            f'SimAprilTagDetection started — publishing fake tag '
            f'{family}:{tag_id} at {rate} Hz  '
            f'[SIMULATION TEST BRIDGE — NOT REAL PERCEPTION]'
        )

    # ── Timer callback ──────────────────────────────────────────────

    def _publish(self):
        now = self.get_clock().now().to_msg()

        tag_id = self.get_parameter('tag_id').value
        family = self.get_parameter('tag_family').value
        parent = self.get_parameter('parent_frame').value
        noise = self.get_parameter('noise_stddev').value

        tx = self.get_parameter('tag_x').value
        ty = self.get_parameter('tag_y').value
        tz = self.get_parameter('tag_z').value

        if noise > 0.0:
            tx += random.gauss(0.0, noise)
            ty += random.gauss(0.0, noise)
            tz += random.gauss(0.0, noise)

        # ── TF: parent_frame → <family>:<tag_id> ────────────────────
        tf = TransformStamped()
        tf.header.stamp = now
        tf.header.frame_id = parent
        tf.child_frame_id = f'{family}:{tag_id}'
        tf.transform.translation.x = tx
        tf.transform.translation.y = ty
        tf.transform.translation.z = tz
        # Small fixed rotation so orientation is non-trivial.
        tf.transform.rotation.x = 0.0
        tf.transform.rotation.y = 0.0
        tf.transform.rotation.z = 0.0
        tf.transform.rotation.w = 1.0
        self._tf_broadcaster.sendTransform(tf)

        # ── Detection array ─────────────────────────────────────────
        det = AprilTagDetection()
        det.family = f'tag{family}'
        det.id = tag_id
        det.hamming = 0
        det.goodness = 0.0
        det.decision_margin = 85.0   # simulated confidence
        # Approximate pixel centre (not used by tag_pose_node but
        # required by the message definition).
        det.centre.x = 320.0
        det.centre.y = 240.0
        # Placeholder corners (square around centre).
        for i, (cx, cy) in enumerate([
            (280.0, 200.0), (360.0, 200.0),
            (360.0, 280.0), (280.0, 280.0),
        ]):
            det.corners[i].x = cx
            det.corners[i].y = cy
        det.homography = [0.0] * 9

        arr = AprilTagDetectionArray()
        arr.header.stamp = now
        arr.header.frame_id = parent
        arr.detections = [det]
        self._det_pub.publish(arr)


def main(args=None):
    rclpy.init(args=args)
    node = SimAprilTagDetection()
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
