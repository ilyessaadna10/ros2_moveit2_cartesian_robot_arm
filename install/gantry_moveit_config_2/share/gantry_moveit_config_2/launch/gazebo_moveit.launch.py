from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def launch_setup(context, *args, **kwargs):
    # Initialize Arguments
    use_sim_time = LaunchConfiguration("use_sim_time")
    moveit_config_package = LaunchConfiguration("moveit_config_package")
    
    # 1. Gazebo Simulation Launch
    # This runs the file we edited earlier (spawns robot, controllers, and bridges)
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("gantry"), "launch", "gazebo.launch.py"]
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            # Add any other arguments your simulation.launch.py needs here
            # "world_file": ... 
        }.items(),
    )
    
    # 2. MoveIt2 Move Group Launch
    # This starts the trajectory planning pipeline
    moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare(moveit_config_package), "launch", "move_group.launch.py"]
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            # We tell MoveIt to load the robot description from the URDF/SRDF
            # The generated launch file usually handles this, but use_sim_time is crucial
        }.items(),
    )
    
    # 3. RViz Launch
    # Visualizes the robot state and planning scene
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
    
    # Wait a few seconds for Gazebo to load before starting MoveIt
    # This prevents MoveIt from crashing if the /joint_states topic isn't ready yet
    delayed_moveit = TimerAction(
        period=5.0,
        actions=[moveit_launch]
    )

    delayed_rviz = TimerAction(
        period=7.0,
        actions=[rviz_launch]
    )
    
    nodes_to_launch = [
        gazebo_launch,
        delayed_moveit,
        delayed_rviz,
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
            default_value="gantry_moveit_config_2",
            description="MoveIt config package name",
        )
    )
    
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])