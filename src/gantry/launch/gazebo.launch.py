#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, PathJoinSubstitution, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue


def launch_setup(context, *args, **kwargs):
    # Launch Configurations
    use_sim_time = LaunchConfiguration("use_sim_time")
    world_file = LaunchConfiguration("world_file")
    enable_overhead_camera = LaunchConfiguration("enable_overhead_camera")
    overhead_camera_height = LaunchConfiguration("overhead_camera_height")
    overhead_camera_name = LaunchConfiguration("overhead_camera_name")

    pkg_share = FindPackageShare("gantry")
    urdf_file = PathJoinSubstitution([pkg_share, "urdf", "parallel_beam_gantry.xacro"])

    # Build robot description
    robot_description_content = ParameterValue(
        Command([
            "xacro", " ", urdf_file,
            " use_sim:=true",
            " use_mock_hardware:=false",
            " enable_overhead_camera:=", enable_overhead_camera,
            " overhead_camera_height:=", overhead_camera_height,
            " overhead_camera_name:=", overhead_camera_name,
        ]),
        value_type=str
    )
    robot_description = {"robot_description": robot_description_content}

    # Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("ros_gz_sim"), "/launch/gz_sim.launch.py"]
        ),
        launch_arguments={"gz_args": ["-r -v4 ", world_file]}.items(),
    )

    # Clock bridge
    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Robot State Publisher
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    # Spawn robot
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "parallel_beam_gantry"],
        output="screen",
    )

    # Controller spawners
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    gantry_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gantry_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # Startup sequencing
    delay_joint_state = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[joint_state_broadcaster_spawner],
        )
    )

    delay_gantry_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[gantry_controller_spawner],
        )
    )

    # Base nodes
    nodes = [
        gazebo,
        clock_bridge,
        robot_state_publisher,
        spawn_robot,
        delay_joint_state,
        delay_gantry_controller,
    ]

    # === Overhead RGB Camera Bridge (only if enabled) ===
    if enable_overhead_camera.perform(context) == "true":
        camera_name = overhead_camera_name.perform(context)
        camera_image_topic = f"/camera/{camera_name}/image_raw"
        camera_info_topic = f"/camera/{camera_name}/camera_info"

        image_bridge = Node(
            package="ros_gz_image",
            executable="image_bridge",
            arguments=[camera_image_topic],
            output="screen",
        )

        info_bridge = Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=[f"{camera_info_topic}@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo"],
            output="screen",
            parameters=[{"use_sim_time": use_sim_time}],
        )

        nodes += [image_bridge, info_bridge]

    return nodes


def generate_launch_description():
    # Get path to my_world.sdf in the worlds folder
    pkg_share = FindPackageShare("gantry")
    default_world_path = PathJoinSubstitution([pkg_share, "worlds", "my_world.sdf"])
    
    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true", description="Use sim time"),
        DeclareLaunchArgument("world_file", default_value=default_world_path, description="Gazebo world"),
        DeclareLaunchArgument("enable_overhead_camera", default_value="true", description="Enable overhead RGB camera"),
        DeclareLaunchArgument("overhead_camera_height", default_value="3.0", description="Height of overhead camera"),
        DeclareLaunchArgument("overhead_camera_name", default_value="overhead", description="Camera name prefix"),

        OpaqueFunction(function=launch_setup)
    ])