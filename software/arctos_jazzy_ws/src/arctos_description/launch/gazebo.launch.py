from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.substitutions import Command, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    xacro_file = PathJoinSubstitution([
        FindPackageShare('arctos_description'),
        'urdf',
        'arctos_urdf.xacro'
    ])

    robot_description = {
        'robot_description': Command(['xacro ', xacro_file])
    }

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ),
        launch_arguments={
            'gz_args': '-r empty.sdf'
        }.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[robot_description],
        output='screen'
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'arctos',
            '-topic', 'robot_description',
            '-x', '0',
            '-y', '0',
            '-z', '0.05'
        ],
        output='screen'
    )

    return LaunchDescription([
        gz_sim,
        robot_state_publisher,
        TimerAction(
            period=3.0,
            actions=[spawn_robot]
        )
    ])
