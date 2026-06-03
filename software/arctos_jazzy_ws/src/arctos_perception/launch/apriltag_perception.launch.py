"""Launch the AprilTag perception stack.

Brings up:
  1. apriltag_ros detector   – subscribes to image_rect + camera_info
  2. tag_pose_node adapter   – converts detections + TF → PoseStamped

The launch file does NOT start a camera driver.  Image topics must
already be available (from Gazebo, usb_cam, or another source).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('arctos_perception')
    params_file = PathJoinSubstitution([pkg_share, 'config', 'apriltag_params.yaml'])

    # ── Arguments ────────────────────────────────────────────────────
    target_tag_id_arg = DeclareLaunchArgument(
        'target_tag_id', default_value='0',
        description='ID of the AprilTag to track')
    reference_frame_arg = DeclareLaunchArgument(
        'reference_frame', default_value='camera_link',
        description='TF reference frame for published pose')
    tag_frame_override_arg = DeclareLaunchArgument(
        'tag_frame_override', default_value='apriltag_target',
        description='TF frame published by apriltag_ros for the target tag')

    # Image topic remappings (caller provides the actual camera topics)
    image_topic_arg = DeclareLaunchArgument(
        'image_topic', default_value='/camera/image_raw',
        description='Source image topic for the detector')
    camera_info_topic_arg = DeclareLaunchArgument(
        'camera_info_topic', default_value='/camera/camera_info',
        description='Camera info topic for the detector')

    # ── AprilTag detector (apriltag_ros) ─────────────────────────────
    apriltag_node = Node(
        package='apriltag_ros',
        executable='apriltag_node',
        name='apriltag',
        namespace='apriltag',
        remappings=[
            ('image_rect', LaunchConfiguration('image_topic')),
            ('camera_info', LaunchConfiguration('camera_info_topic')),
        ],
        parameters=[params_file],
        output='screen',
    )

    # ── Tag-pose adapter ─────────────────────────────────────────────
    tag_pose_node = Node(
        package='arctos_perception',
        executable='tag_pose_node',
        name='tag_pose',
        parameters=[{
            'target_tag_id': LaunchConfiguration('target_tag_id'),
            'reference_frame': LaunchConfiguration('reference_frame'),
            'tag_family': '36h11',
            'tag_frame_override': LaunchConfiguration('tag_frame_override'),
        }],
        output='screen',
    )

    return LaunchDescription([
        target_tag_id_arg,
        reference_frame_arg,
        tag_frame_override_arg,
        image_topic_arg,
        camera_info_topic_arg,
        apriltag_node,
        tag_pose_node,
    ])
