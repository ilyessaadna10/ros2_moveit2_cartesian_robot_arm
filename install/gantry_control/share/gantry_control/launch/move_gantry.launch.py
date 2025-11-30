from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    
    # 1. Load the Configuration
    # Robot name: parallel_beam_gantry (from your URDF)
    # Package name: gantry_moveit_config_2 (your config package)
    moveit_config = MoveItConfigsBuilder("parallel_beam_gantry", package_name="gantry_moveit_config_2").to_moveit_configs()

    # 2. Configure the Node
    program_node = Node(
        package="gantry_control",
        executable="simple_move",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.trajectory_execution,
            moveit_config.planning_scene_monitor,
        ],
    )

    return LaunchDescription([program_node])