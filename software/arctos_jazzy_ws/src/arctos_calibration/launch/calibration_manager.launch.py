from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='arctos_calibration',
            executable='calibration_manager_node',
            name='calibration_manager',
            output='screen',
        ),
    ])
