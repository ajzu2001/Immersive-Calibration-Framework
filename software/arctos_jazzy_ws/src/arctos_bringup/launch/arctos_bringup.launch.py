"""Arctos Calibration Framework — integrated software bringup.

Launches the full calibration pipeline:
  - Digital twin:   twin_monitor_node + sync_error_node + optional ESP32 bridge + hardware sensor fusion
  - Perception:     mock_tag_pose  OR  sim_detection + tag_pose  OR  apriltag + tag_pose
  - Calibration:    calibration_observer_node + calibration_manager_node + correction + compensation + model estimator + application
  - Evaluation:     metrics_node + optional experiment_runner_node
  - VR bridge:      optional Unity/VR JSON state bridge

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
    enable_calibration_estimator_arg = DeclareLaunchArgument(
        'enable_calibration_estimator', default_value='true',
        description='Launch the Calibration Parameter Estimation MVP node',
    )
    enable_calibration_application_arg = DeclareLaunchArgument(
        'enable_calibration_application', default_value='true',
        description='Launch the calibration application simulation layer',
    )
    enable_experiment_runner_arg = DeclareLaunchArgument(
        'enable_experiment_runner', default_value='false',
        description='Record experiment metrics and generate CSV/plots',
    )
    enable_unity_bridge_arg = DeclareLaunchArgument(
        'enable_unity_bridge', default_value='false',
        description='Launch the Unity/VR JSON state bridge',
    )
    enable_mock_hardware_sensors_arg = DeclareLaunchArgument(
        'enable_mock_hardware_sensors', default_value='false',
        description='Launch mock ESP32/AS5600/limit/IMU hardware sensor publisher',
    )
    enable_sensor_fusion_arg = DeclareLaunchArgument(
        'enable_sensor_fusion', default_value='false',
        description='Launch MVP encoder-primary sensor fusion node',
    )
    enable_esp32_bridge_arg = DeclareLaunchArgument(
        'enable_esp32_bridge', default_value='false',
        description='Launch ESP32 serial hardware bridge',
    )
    enable_mock_serial_arg = DeclareLaunchArgument(
        'enable_mock_serial', default_value='false',
        description='Launch mock ESP32 JSON serial packet generator',
    )
    esp32_serial_port_arg = DeclareLaunchArgument(
        'esp32_serial_port', default_value='',
        description='ESP32 USB serial port path, for example /dev/ttyUSB0',
    )

    mode = LaunchConfiguration('perception_mode')
    sim_time = LaunchConfiguration('use_sim_time')
    enable_solver = LaunchConfiguration('enable_solver')
    enable_correction = LaunchConfiguration('enable_correction')
    enable_compensation = LaunchConfiguration('enable_compensation')
    enable_calibration_estimator = LaunchConfiguration('enable_calibration_estimator')
    enable_calibration_application = LaunchConfiguration('enable_calibration_application')
    enable_experiment_runner = LaunchConfiguration('enable_experiment_runner')
    enable_unity_bridge = LaunchConfiguration('enable_unity_bridge')
    enable_mock_hardware_sensors = LaunchConfiguration('enable_mock_hardware_sensors')
    enable_sensor_fusion = LaunchConfiguration('enable_sensor_fusion')
    enable_esp32_bridge = LaunchConfiguration('enable_esp32_bridge')
    enable_mock_serial = LaunchConfiguration('enable_mock_serial')
    esp32_serial_port = LaunchConfiguration('esp32_serial_port')
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

    mock_hardware_sensors = Node(
        package='arctos_twin',
        executable='mock_hardware_sensor_node',
        name='mock_hardware_sensors',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(enable_mock_hardware_sensors),
    )
    sensor_fusion = Node(
        package='arctos_twin',
        executable='sensor_fusion_node',
        name='sensor_fusion',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(enable_sensor_fusion),
    )

    esp32_bridge = Node(
        package='arctos_twin',
        executable='esp32_bridge_node',
        name='esp32_bridge',
        parameters=[sim_time_param, {
            'serial_port': esp32_serial_port,
        }],
        output='screen',
        condition=IfCondition(enable_esp32_bridge),
    )
    mock_serial = Node(
        package='arctos_twin',
        executable='mock_serial_packet_node',
        name='mock_serial_packet',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(enable_mock_serial),
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

    # ── Calibration Parameter Estimation MVP (optional) ─────────────
    calibration_estimator = Node(
        package='arctos_calibration',
        executable='calibration_estimator_node',
        name='calibration_estimator',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(enable_calibration_estimator),
    )

    # ── Calibration application simulation (optional) ───────────────
    calibration_application = Node(
        package='arctos_calibration',
        executable='calibration_application_node',
        name='calibration_application',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(enable_calibration_application),
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

    unity_bridge = Node(
        package='arctos_vr',
        executable='unity_bridge_node',
        name='unity_bridge',
        parameters=[sim_time_param],
        output='screen',
        condition=IfCondition(enable_unity_bridge),
    )

    return LaunchDescription([
        perception_mode_arg,
        use_sim_time_arg,
        enable_solver_arg,
        enable_correction_arg,
        enable_compensation_arg,
        enable_calibration_estimator_arg,
        enable_calibration_application_arg,
        enable_experiment_runner_arg,
        enable_unity_bridge_arg,
        enable_mock_hardware_sensors_arg,
        enable_sensor_fusion_arg,
        enable_esp32_bridge_arg,
        enable_mock_serial_arg,
        esp32_serial_port_arg,

        # Twin
        twin_monitor,
        sync_error,
        mock_hardware_sensors,
        sensor_fusion,
        esp32_bridge,
        mock_serial,

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
        calibration_estimator,
        calibration_application,

        # Evaluation
        metrics,
        experiment_runner,

        # VR bridge
        unity_bridge,
    ])
