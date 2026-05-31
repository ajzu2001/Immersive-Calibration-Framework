from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='arctos_perception',
            executable='mock_tag_pose_node',
            name='mock_tag_pose',
            output='screen',
        ),
    ])
