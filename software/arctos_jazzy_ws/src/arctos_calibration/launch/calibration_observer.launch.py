from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='arctos_calibration',
            executable='calibration_observer_node',
            name='calibration_observer',
            output='screen',
        ),
    ])
