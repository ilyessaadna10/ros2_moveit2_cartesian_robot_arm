from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # 1. Declare the use_sim_time argument
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation (Gazebo) clock if true",
        )
    )
    
    use_sim_time = LaunchConfiguration("use_sim_time")

    # 2. Load MoveIt Config
    # We point to your specific package: gantry_moveit_config_2
    moveit_config = (
        MoveItConfigsBuilder("parallel_beam_gantry", package_name="gantry_moveit_config_2")
        .to_moveit_configs()
    )

    # 3. Start Move Group Node
    # We manually define this node so we can inject {"use_sim_time": use_sim_time}
    run_move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": use_sim_time},
            # Optional: Allow extra time for trajectories in sim to prevent aborts
            {"trajectory_execution.allowed_execution_duration_scaling": 2.0},
            {"trajectory_execution.allowed_goal_duration_margin": 0.5},
            {"publish_robot_description_semantic": True},
        ],
    )

    return LaunchDescription(declared_arguments + [run_move_group_node])