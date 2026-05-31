from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='arctos_twin',
            executable='twin_monitor_node',
            name='twin_monitor',
            output='screen',
        ),
        Node(
            package='arctos_twin',
            executable='sync_error_node',
            name='sync_error',
            output='screen',
        ),
    ])
