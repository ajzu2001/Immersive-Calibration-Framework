"""Launch the Unity/VR bridge MVP."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation clock (/clock topic)',
    )
    use_sim_time = LaunchConfiguration('use_sim_time')

    unity_bridge = Node(
        package='arctos_vr',
        executable='unity_bridge_node',
        name='unity_bridge',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    return LaunchDescription([
        use_sim_time_arg,
        unity_bridge,
    ])
