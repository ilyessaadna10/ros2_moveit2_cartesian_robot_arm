from moveit_configs_utils import MoveItConfigsBuilder
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


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
    
    # Build MoveIt configuration
    moveit_config = (
        MoveItConfigsBuilder("parallel_beam_gantry", package_name="gantry_moveit_config_2")
        .to_moveit_configs()
    )
    
    # Path to RViz config file
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("gantry_moveit_config"), "config", "moveit.rviz"]
    )
    
    # RViz node with all necessary MoveIt parameters
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
            {"use_sim_time": use_sim_time},
        ],
    )
    
    return LaunchDescription(declared_arguments + [rviz_node])