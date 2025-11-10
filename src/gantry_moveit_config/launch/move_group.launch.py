from moveit_configs_utils import MoveItConfigsBuilder
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation (Gazebo) clock if true",
        )
    )
    
    use_sim_time = LaunchConfiguration("use_sim_time")
    
    moveit_config = (
        MoveItConfigsBuilder("parallel_beam_gantry", package_name="gantry_moveit_config")
        .to_moveit_configs()
    )
    
    # Create move_group node manually with use_sim_time
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": use_sim_time},
        ],
    )
    
    return LaunchDescription(declared_arguments + [move_group_node])