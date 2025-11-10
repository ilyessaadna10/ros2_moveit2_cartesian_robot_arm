from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    # Initialize Arguments
    use_sim_time = LaunchConfiguration("use_sim_time")
    moveit_config_package = LaunchConfiguration("moveit_config_package")
    
    # Gazebo simulation launch
    gazebo_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        PathJoinSubstitution(
            [FindPackageShare("gantry"), "launch", "gazebo.launch.py"]
        )
    ),
    # Add this section
    launch_arguments={
        "use_sim_time": use_sim_time,
    }.items(),
)
    
    # MoveIt2 launch
    moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare(moveit_config_package), "launch", "move_group.launch.py"]
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
        }.items(),
    )
    
    # RViz launch
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare(moveit_config_package), "launch", "moveit_rviz.launch.py"]
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
        }.items(),
    )
    
    nodes_to_launch = [
        gazebo_launch,
        moveit_launch,
        rviz_launch,
    ]
    
    return nodes_to_launch


def generate_launch_description():
    declared_arguments = []
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation (Gazebo) clock if true",
        )
    )
    
    declared_arguments.append(
        DeclareLaunchArgument(
            "moveit_config_package",
            default_value="gantry_moveit_config",
            description="MoveIt config package name",
        )
    )
    
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])