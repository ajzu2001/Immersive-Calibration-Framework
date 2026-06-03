"""Arctos Calibration Framework — integrated software bringup.

Launches the full calibration pipeline:
  - Digital twin:   twin_monitor_node + sync_error_node
  - Perception:     mock_tag_pose  OR  sim_detection + tag_pose  OR  apriltag + tag_pose
  - Calibration:    calibration_observer_node + calibration_manager_node + correction + compensation
  - Evaluation:     metrics_node + optional experiment_runner_node

Does NOT launch Gazebo or robot hardware.  Use simulation.launch.py or
display.launch.py separately to provide /joint_states.

Usage:
  ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=mock
  ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=sim_detection
  ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=apriltag
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EqualsSubstitution, LaunchConfiguration, PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # ── Arguments ────────────────────────────────────────────────────
    perception_mode_arg = DeclareLaunchArgument(
        'perception_mode', default_value='mock',
        description='Perception source: mock | apriltag | sim_detection',
        choices=['mock', 'apriltag', 'sim_detection'],
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation clock (/clock topic)',
    )
    enable_solver_arg = DeclareLaunchArgument(
        'enable_solver', default_value='true',
        description='Launch the MVP calibration solver node',
    )
    enable_correction_arg = DeclareLaunchArgument(
        'enable_correction', default_value='true',
        description='Launch the MVP calibration correction output node',
    )
    enable_compensation_arg = DeclareLaunchArgument(
        'enable_compensation', default_value='true',
        description='Launch the raw-vs-compensated target node',
    )
    enable_experiment_runner_arg = DeclareLaunchArgument(
        'enable_experiment_runner', default_value='false',
        description='Record experiment metrics and generate CSV/plots',
    )

    mode = LaunchConfiguration('perception_mode')
    sim_time = LaunchConfiguration('use_sim_time')
    enable_solver = LaunchConfiguration('enable_solver')
    enable_correction = LaunchConfiguration('enable_correction')
    enable_compensation = LaunchConfiguration('enable_compensation')
    enable_experiment_runner = LaunchConfiguration('enable_experiment_runner')
    sim_time_param = {'use_sim_time': sim_time}

    # ── Digital Twin ─────────────────────────────────────────────────
    twin_monitor = Node(
        package='arctos_twin',
        executable='twin_monitor_node',
        name='twin_monitor',
        parameters=[sim_time_param],
        output='screen',
    )
    sync_error = Node(
        package='arctos_twin',
        executable='sync_error_node',
        name='sync_error',
        parameters=[sim_time_param],
        output='screen',
    )

    # ── Perception: mock ─────────────────────────────────────────────
    mock_perception = Node(
        package='arctos_perception',
        executable='mock_tag_pose_node',
        name='mock_tag_pose',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(EqualsSubstitution(mode, 'mock')),
    )

    # ── Perception: sim_detection (fake detections + TF → tag_pose) ──
    sim_detection = Node(
        package='arctos_perception',
        executable='sim_apriltag_detection_node',
        name='sim_apriltag_detection',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(EqualsSubstitution(mode, 'sim_detection')),
    )
    tag_pose_for_sim = Node(
        package='arctos_perception',
        executable='tag_pose_node',
        name='tag_pose',
        parameters=[sim_time_param, {
            'target_tag_id': 0,
            'reference_frame': 'camera_link',
            'tag_family': '36h11',
        }],
        output='screen',
        condition=IfCondition(
            PythonExpression([
                "'", mode, "' == 'sim_detection' or '", mode, "' == 'apriltag'"
            ])
        ),
    )

    # ── Perception: apriltag (real detector — needs camera topics) ───
    apriltag_perception = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('arctos_perception'),
                'launch', 'apriltag_perception.launch.py',
            ])
        ),
        condition=IfCondition(EqualsSubstitution(mode, 'apriltag')),
    )

    # ── Calibration ──────────────────────────────────────────────────
    calibration_observer = Node(
        package='arctos_calibration',
        executable='calibration_observer_node',
        name='calibration_observer',
        parameters=[sim_time_param],
        output='screen',
    )
    calibration_manager = Node(
        package='arctos_calibration',
        executable='calibration_manager_node',
        name='calibration_manager',
        parameters=[sim_time_param],
        output='screen',
    )

    # ── Calibration solver (optional) ───────────────────────────────
    calibration_solver = Node(
        package='arctos_calibration',
        executable='calibration_solver_node',
        name='calibration_solver',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(enable_solver),
    )

    # ── MVP correction output (optional) ────────────────────────────
    calibration_correction = Node(
        package='arctos_calibration',
        executable='calibration_correction_node',
        name='calibration_correction',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(enable_correction),
    )

    # ── Raw-vs-compensated target output (optional) ─────────────────
    correction_compensator = Node(
        package='arctos_calibration',
        executable='correction_compensator_node',
        name='correction_compensator',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(enable_compensation),
    )

    # ── Evaluation ───────────────────────────────────────────────────
    metrics = Node(
        package='arctos_evaluation',
        executable='metrics_node',
        name='metrics',
        parameters=[sim_time_param],
        output='screen',
    )

    experiment_runner = Node(
        package='arctos_evaluation',
        executable='experiment_runner_node',
        name='experiment_runner',
        parameters=[sim_time_param, {
            'perception_mode': mode,
        }],
        output='screen',
        condition=IfCondition(enable_experiment_runner),
    )

    return LaunchDescription([
        perception_mode_arg,
        use_sim_time_arg,
        enable_solver_arg,
        enable_correction_arg,
        enable_compensation_arg,
        enable_experiment_runner_arg,

        # Twin
        twin_monitor,
        sync_error,

        # Perception (only one mode activates)
        mock_perception,
        sim_detection,
        tag_pose_for_sim,
        apriltag_perception,

        # Calibration
        calibration_observer,
        calibration_manager,
        calibration_solver,
        calibration_correction,
        correction_compensator,

        # Evaluation
        metrics,
        experiment_runner,
    ])
