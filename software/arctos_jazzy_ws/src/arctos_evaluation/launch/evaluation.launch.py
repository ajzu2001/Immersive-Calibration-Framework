from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='arctos_evaluation',
            executable='metrics_node',
            name='metrics_node',
            output='screen',
        ),
    ])
