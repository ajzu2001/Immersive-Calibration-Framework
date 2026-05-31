"""Launch the full AprilTag simulation stack for calibration testing.

Brings up:
  1. Gazebo with apriltag_test_world (camera + AprilTag board)
  2. Robot state publisher + spawn robot into Gazebo
  3. ros_gz_bridge for clock
  4. ros_gz_image bridge for camera image
  5. Static TF for camera_link (camera is in the world, not in the URDF)
  6. AprilTag perception stack (apriltag_ros detector + tag_pose_node)
  7. Joint state broadcaster + arm controller (existing controllers)
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription,
    SetEnvironmentVariable, TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    desc_share = FindPackageShare('arctos_description')
    perc_share = FindPackageShare('arctos_perception')

    xacro_file = PathJoinSubstitution([desc_share, 'urdf', 'arctos_urdf.xacro'])
    robot_description = {'robot_description': Command(['xacro ', xacro_file])}

    world_file = PathJoinSubstitution(
        [desc_share, 'worlds', 'apriltag_test_world.sdf'])

    # Point GZ_SIM_RESOURCE_PATH at the models directory so Gazebo
    # can resolve  model://apriltag_board .
    model_path = PathJoinSubstitution([desc_share, 'models'])

    # ── Gazebo ───────────────────────────────────────────────────────
    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_file],
        output='screen',
        additional_env={'GZ_SIM_RESOURCE_PATH': model_path},
    )

    # ── Robot state publisher ────────────────────────────────────────
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[robot_description],
        output='screen',
    )

    # ── Clock bridge (Gazebo → ROS2) ────────────────────────────────
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen',
    )

    # ── Camera image bridge (Gazebo → ROS2) ──────────────────────────
    # Gazebo publishes on /calibration_camera/image_raw (gz transport).
    # Bridge to ROS2 /camera/image_raw using ros_gz_image.
    image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['calibration_camera/image_raw'],
        remappings=[
            ('calibration_camera/image_raw', '/camera/image_raw'),
        ],
        output='screen',
    )

    # ── Camera info publisher (synthetic) ────────────────────────────
    # Gazebo camera sensor doesn't publish camera_info to ROS2 by
    # default.  We publish a synthetic CameraInfo matching the SDF
    # sensor parameters (640×480, hfov=60°).
    # fx = width / (2 * tan(hfov/2)) = 640 / (2 * tan(0.5236)) ≈ 554.26
    camera_info_pub = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/calibration_camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        remappings=[
            ('/calibration_camera/camera_info', '/camera/camera_info'),
        ],
        output='screen',
    )

    # ── Static TF: world → camera_link ───────────────────────────────
    # Matches the camera model pose in apriltag_test_world.sdf:
    #   x=0.6  y=0  z=0.5  roll=0  pitch=0.4  yaw=π
    static_tf_camera = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x', '0.6', '--y', '0', '--z', '0.5',
            '--roll', '0', '--pitch', '0.4', '--yaw', '3.14159',
            '--frame-id', 'world',
            '--child-frame-id', 'camera_link',
        ],
        output='screen',
    )

    # ── Spawn robot ──────────────────────────────────────────────────
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'arctos', '-topic', 'robot_description'],
        output='screen',
    )

    # ── Joint state broadcaster ──────────────────────────────────────
    load_jsb = ExecuteProcess(
        cmd=[
            'ros2', 'control', 'load_controller',
            '--set-state', 'active', 'joint_state_broadcaster',
        ],
        output='screen',
    )

    # ── Arm controller ───────────────────────────────────────────────
    load_arm = ExecuteProcess(
        cmd=[
            'ros2', 'control', 'load_controller',
            '--set-state', 'active', 'arm_position_controller',
        ],
        output='screen',
    )

    # ── AprilTag perception (detector + adapter) ─────────────────────
    apriltag_perception = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                perc_share, 'launch', 'apriltag_perception.launch.py',
            ])
        ),
        launch_arguments={
            'image_topic': '/camera/image_raw',
            'camera_info_topic': '/camera/camera_info',
            'target_tag_id': '0',
            'reference_frame': 'camera_link',
        }.items(),
    )

    return LaunchDescription([
        SetEnvironmentVariable(
            name='GZ_SIM_SYSTEM_PLUGIN_PATH', value='/opt/ros/jazzy/lib'),
        gazebo,
        rsp,
        clock_bridge,
        static_tf_camera,
        # Image bridge — give Gazebo a moment to start the sensor
        TimerAction(period=4.0, actions=[image_bridge]),
        TimerAction(period=4.0, actions=[camera_info_pub]),
        # Spawn robot after Gazebo is running
        TimerAction(period=5.0, actions=[spawn_robot]),
        # Controllers after robot is spawned
        TimerAction(period=8.0, actions=[load_jsb]),
        TimerAction(period=15.0, actions=[load_arm]),
        # AprilTag perception after camera is ready
        TimerAction(period=6.0, actions=[apriltag_perception]),
    ])
