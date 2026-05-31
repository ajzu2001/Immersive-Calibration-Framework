"""TagPose node – publishes real AprilTag pose for calibration.

Subscribes to /apriltag/detections (AprilTagDetectionArray) and listens for
the corresponding TF transform published by apriltag_ros.  When the target
tag is detected, its 3-D pose is republished as a PoseStamped on
/arctos/perception/reference_frame_pose (the same topic the mock node uses).

A PerceptionQuality message is also published on /arctos/perception/quality.
"""

import time

import rclpy
from rclpy.node import Node

from apriltag_msgs.msg import AprilTagDetectionArray
from geometry_msgs.msg import PoseStamped
from arctos_interfaces.msg import PerceptionQuality

from tf2_ros import Buffer, TransformListener, LookupException
from tf2_ros import ConnectivityException, ExtrapolationException


class TagPose(Node):
    """Adapter: apriltag_ros detections + TF → PoseStamped."""

    def __init__(self):
        super().__init__('tag_pose')

        # ── Parameters ──────────────────────────────────────────────
        self.declare_parameter('target_tag_id', 0)
        self.declare_parameter('reference_frame', 'camera_link')
        # Tag family used by apriltag_ros (affects TF frame name).
        self.declare_parameter('tag_family', '36h11')
        # Override the auto-generated TF child frame name.
        # If empty, the node builds it as "<tag_family>:<target_tag_id>".
        self.declare_parameter('tag_frame_override', '')

        # ── TF2 listener ────────────────────────────────────────────
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)

        # ── Publishers ──────────────────────────────────────────────
        self._pose_pub = self.create_publisher(
            PoseStamped, '/arctos/perception/reference_frame_pose', 10
        )
        self._quality_pub = self.create_publisher(
            PerceptionQuality, '/arctos/perception/quality', 10
        )

        # ── Subscriber ──────────────────────────────────────────────
        self.create_subscription(
            AprilTagDetectionArray,
            '/apriltag/detections',
            self._on_detections,
            10,
        )

        # ── Internal state ──────────────────────────────────────────
        self._detection_count: int = 0
        self._last_log_time = self.get_clock().now()

        self.get_logger().info(
            f'TagPose started – target tag {self._target_tag_id} '
            f'(frame: {self._tag_frame}), '
            f'publishing on /arctos/perception/reference_frame_pose'
        )

    # ── Helpers ─────────────────────────────────────────────────────

    @property
    def _target_tag_id(self) -> int:
        return self.get_parameter('target_tag_id').value

    @property
    def _reference_frame(self) -> str:
        return self.get_parameter('reference_frame').value

    @property
    def _tag_frame(self) -> str:
        override = self.get_parameter('tag_frame_override').value
        if override:
            return override
        family = self.get_parameter('tag_family').value
        return f'{family}:{self._target_tag_id}'

    # ── Callback ────────────────────────────────────────────────────

    def _on_detections(self, msg: AprilTagDetectionArray):
        t_start = time.monotonic()
        target_id = self._target_tag_id

        # Find the target tag in the detection array.
        target_det = None
        for det in msg.detections:
            if det.id == target_id:
                target_det = det
                break

        num_detections = len(msg.detections)

        if target_det is None:
            self._publish_quality(
                stamp=msg.header.stamp,
                frame_id=msg.header.frame_id,
                overall_score=0.0,
                confidence=0.0,
                consistency=0.0,
                num_detections=num_detections,
                elapsed_ms=0,
                status='target tag not detected',
            )
            self._warn_throttled(
                f'Tag id={target_id} not found in {num_detections} detection(s)'
            )
            return

        # ── Look up TF pose ─────────────────────────────────────────
        ref_frame = self._reference_frame
        tag_frame = self._tag_frame

        try:
            # Use latest available transform (Time(0)) rather than the
            # exact header stamp, to avoid ExtrapolationExceptions when
            # the TF tree has a small delay relative to the detection msg.
            tf_stamped = self._tf_buffer.lookup_transform(
                ref_frame, tag_frame, rclpy.time.Time()
            )
        except (LookupException, ConnectivityException,
                ExtrapolationException) as exc:
            self._warn_throttled(
                f'TF lookup {ref_frame} → {tag_frame} failed: {exc}'
            )
            self._publish_quality(
                stamp=msg.header.stamp,
                frame_id=msg.header.frame_id,
                overall_score=0.0,
                confidence=target_det.decision_margin / 100.0,
                consistency=0.0,
                num_detections=num_detections,
                elapsed_ms=0,
                status=f'TF lookup failed: {exc}',
            )
            return

        # ── Convert TransformStamped → PoseStamped ──────────────────
        pose = PoseStamped()
        pose.header.stamp = msg.header.stamp
        pose.header.frame_id = ref_frame

        t = tf_stamped.transform.translation
        r = tf_stamped.transform.rotation
        pose.pose.position.x = t.x
        pose.pose.position.y = t.y
        pose.pose.position.z = t.z
        pose.pose.orientation.x = r.x
        pose.pose.orientation.y = r.y
        pose.pose.orientation.z = r.z
        pose.pose.orientation.w = r.w

        self._pose_pub.publish(pose)
        self._detection_count += 1

        # ── Publish quality ─────────────────────────────────────────
        elapsed_ms = int((time.monotonic() - t_start) * 1000)
        confidence = min(target_det.decision_margin / 100.0, 1.0)

        self._publish_quality(
            stamp=msg.header.stamp,
            frame_id=ref_frame,
            overall_score=confidence,
            confidence=confidence,
            consistency=1.0,
            num_detections=num_detections,
            elapsed_ms=elapsed_ms,
            status='ok',
        )

        # ── Periodic log ────────────────────────────────────────────
        now = self.get_clock().now()
        if (now - self._last_log_time).nanoseconds >= 1_000_000_000:
            self.get_logger().info(
                f'Detections: {self._detection_count}  '
                f'pos=({t.x:.3f}, {t.y:.3f}, {t.z:.3f})  '
                f'confidence={confidence:.2f}'
            )
            self._last_log_time = now

    # ── Helpers ─────────────────────────────────────────────────────

    def _publish_quality(
        self, *, stamp, frame_id, overall_score, confidence,
        consistency, num_detections, elapsed_ms, status,
    ):
        q = PerceptionQuality()
        q.header.stamp = stamp
        q.header.frame_id = frame_id
        q.overall_score = float(overall_score)
        q.detection_confidence = float(confidence)
        q.tracking_consistency = float(consistency)
        q.num_detections = int(num_detections)
        q.processing_time_ms = int(elapsed_ms)
        q.status_message = status
        self._quality_pub.publish(q)

    def _warn_throttled(self, text: str):
        now = self.get_clock().now()
        if (now - self._last_log_time).nanoseconds >= 5_000_000_000:
            self.get_logger().warn(text)
            self._last_log_time = now


def main(args=None):
    rclpy.init(args=args)
    node = TagPose()
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
