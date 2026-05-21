from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_share = FindPackageShare("arctos_description")
    xacro_file = PathJoinSubstitution([pkg_share, "urdf", "arctos_urdf.xacro"])
    robot_description = {"robot_description": Command(["xacro ", xacro_file])}

    #for running the gazebo
    gazebo = ExecuteProcess(cmd=["gz", "sim", "-r", PathJoinSubstitution([pkg_share, "worlds", "arctos_empty.sdf"])], output="screen")

    #publisher for the robotic state
    rsp = Node(package="robot_state_publisher", executable="robot_state_publisher", parameters=[robot_description], output="screen")

    #clock Bridge
    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen"
    )

    #to load the Robot
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-name", "arctos", "-topic", "robot_description"],
        output="screen"
    )

    #to load the joint state broadcaster
    load_jsb = ExecuteProcess(
        cmd=["ros2", "control", "load_controller", "--set-state", "active", "joint_state_broadcaster"],
        output="screen"
    )

    #to activate Arm Controller
    load_arm_controller = ExecuteProcess(
        cmd=[
            "ros2", "control", "load_controller",
            "--set-state", "active",
            "arm_position_controller"
        ],
        output="screen"
    )

    return LaunchDescription([
        SetEnvironmentVariable(name="GZ_SIM_SYSTEM_PLUGIN_PATH", value="/opt/ros/jazzy/lib"),
        gazebo,
        rsp,
        clock_bridge,
        TimerAction(
            period=5.0,
            actions=[spawn_robot]
        ),
        TimerAction(
            period=8.0,
            actions=[load_jsb]
        ),
        TimerAction(
            period=15.0,
            actions=[load_arm_controller]
        ),
    ])
