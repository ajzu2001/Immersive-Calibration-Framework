from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='arctos_twin',
            executable='joint_command_demo_node',
            name='joint_command_demo',
            output='screen',
            parameters=[{
                'amplitude': 0.3,
                'frequency': 0.2,
                'rate': 20.0,
            }],
        ),
    ])
