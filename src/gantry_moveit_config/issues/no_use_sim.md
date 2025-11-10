# MoveIt2 + Gazebo Simulation Time Synchronization Guide

## Problem Overview

When integrating MoveIt2 with Gazebo in ROS2, you may encounter two critical issues:

### Issue 1: Joint State Timestamp Mismatch
```
[move_group] [ERROR] Didn't receive robot state (joint angles) with recent timestamp 
within 1.000000 seconds. Requested time 1762113340.705246, but latest received 
state has time 33.579000.
```

**Root Cause:** MoveIt's `move_group` node is using wall clock time while Gazebo publishes joint states with simulation time. This desynchronization prevents motion execution.

### Issue 2: Missing SRDF in RViz
```
[rviz2] [ERROR] Could not find parameter robot_description_semantic and did not 
receive robot_description_semantic via std_msgs::msg::String subscription
[rviz2] [ERROR] Unable to parse SRDF
[rviz2] [ERROR] Robot model not loaded
```

**Root Cause:** RViz isn't receiving the necessary MoveIt configuration parameters (especially the SRDF file) needed to display the robot model and planning scene.

---

## Solution Architecture

The fix requires properly propagating `use_sim_time` parameter through all launch files and ensuring all MoveIt parameters are passed to RViz.

### Launch File Hierarchy
```
moveit_gazebo.launch.py (Top level)
├── gazebo.launch.py (Gazebo + Robot State Publisher)
├── move_group.launch.py (MoveIt planning)
└── moveit_rviz.launch.py (Visualization)
```

---

## Step-by-Step Fix

### 1. Gazebo Launch File (`gazebo.launch.py`)

**Key Requirements:**
- Declare `use_sim_time` argument
- Pass `use_sim_time` to ALL nodes (robot_state_publisher, bridges, controller spawners)

```python
from launch import LaunchDescription
from launch.actions import OpaqueFunction, RegisterEventHandler, DeclareLaunchArgument
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, PathJoinSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription


def launch_setup(context, *args, **kwargs):
    use_sim_time = LaunchConfiguration("use_sim_time")
    pkg_share = FindPackageShare("gantry")
    urdf_file = PathJoinSubstitution([pkg_share, "urdf", "parallel_beam_gantry.xacro"])
    
    robot_description_content = ParameterValue(
        Command(["xacro", " ", urdf_file, " ", "use_sim:=true"]),
        value_type=str
    )
    robot_description = {"robot_description": robot_description_content}
    
    # Gazebo simulator
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare("ros_gz_sim"), "/launch/gz_sim.launch.py"]
        ),
        launch_arguments={"gz_args": "-r -v 4 empty.sdf"}.items(),
    )
    
    # Clock bridge - needs use_sim_time
    gz_sim_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )
    
    # Robot state publisher - needs use_sim_time
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}, robot_description],
    )
    
    # Spawn robot
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=["-topic", "robot_description", "-name", "parallel_beam_gantry", 
                   "-allow_renaming", "true"],
    )
    
    # CRITICAL: Controller spawners MUST have use_sim_time
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )
    
    gantry_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gantry_controller", "--controller-manager", "/controller_manager"],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )
    
    # Event handlers for startup sequencing
    delay_joint_state_broadcaster_after_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[joint_state_broadcaster_spawner],
        )
    )
    
    delay_gantry_controller_after_broadcaster = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[gantry_controller_spawner],
        )
    )
    
    return [
        gazebo,
        gz_sim_bridge,
        robot_state_publisher,
        spawn_robot,
        delay_joint_state_broadcaster_after_spawn,
        delay_gantry_controller_after_broadcaster,
    ]


def generate_launch_description():
    # Declare argument so parent launch files can pass it
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation (Gazebo) clock if true",
        )
    )
    
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
```

**Critical Points:**
- Controller spawners MUST have `use_sim_time` parameter
- Without this, controllers publish joint states with wall clock time
- This causes the timestamp mismatch error in MoveIt

---

### 2. Move Group Launch File (`move_group.launch.py`)

**Key Requirements:**
- Accept `use_sim_time` argument
- Pass all MoveIt config parameters AND `use_sim_time` to move_group node

```python
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
    
    # Build MoveIt configuration
    moveit_config = (
        MoveItConfigsBuilder("parallel_beam_gantry", package_name="gantry_moveit_config")
        .to_moveit_configs()
    )
    
    # Create move_group node with use_sim_time parameter
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": use_sim_time},  # Critical for sim time sync
        ],
    )
    
    return LaunchDescription(declared_arguments + [move_group_node])
```

**Why This Works:**
- `generate_move_group_launch()` utility doesn't automatically forward `use_sim_time`
- Manual node creation ensures the parameter is passed correctly
- MoveIt will now request joint states using simulation time

---

### 3. MoveIt RViz Launch File (`moveit_rviz.launch.py`)

**Key Requirements:**
- Accept `use_sim_time` argument
- Pass ALL MoveIt parameters (URDF, SRDF, kinematics, etc.) to RViz
- Include `use_sim_time` parameter

```python
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
        MoveItConfigsBuilder("parallel_beam_gantry", package_name="gantry_moveit_config")
        .to_moveit_configs()
    )
    
    # Path to RViz config file
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("gantry_moveit_config"), "config", "moveit.rviz"]
    )
    
    # RViz node with ALL necessary MoveIt parameters
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            moveit_config.robot_description,           # URDF
            moveit_config.robot_description_semantic,  # SRDF (was missing!)
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
            {"use_sim_time": use_sim_time},
        ],
    )
    
    return LaunchDescription(declared_arguments + [rviz_node])
```

**Critical Parameters:**
- `robot_description_semantic` (SRDF) - Contains planning groups, collision info
- Without SRDF, RViz can't load the MoveIt Motion Planning panel
- `use_sim_time` ensures visualization syncs with simulation

---

### 4. Top-Level Launch File (`moveit_gazebo.launch.py`)

**Key Requirements:**
- Declare `use_sim_time` once at top level
- Pass it to ALL child launch files

```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    use_sim_time = LaunchConfiguration("use_sim_time")
    moveit_config_package = LaunchConfiguration("moveit_config_package")
    
    # Gazebo simulation launch
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("gantry"), "launch", "gazebo.launch.py"]
            )
        ),
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
    
    return [gazebo_launch, moveit_launch, rviz_launch]


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
```

---

## Verification

After implementing the fixes, verify everything works:

### 1. Check Time Synchronization
```bash
# Terminal 1: Launch system
ros2 launch gantry_moveit_config moveit_gazebo.launch.py

# Terminal 2: Check if nodes are using sim time
ros2 param get /move_group use_sim_time
ros2 param get /robot_state_publisher use_sim_time
ros2 param get /rviz2 use_sim_time
```

All should return `Boolean value is: True`

### 2. Check Joint States Timestamps
```bash
# Check joint states timestamp
ros2 topic echo /joint_states --once

# Check Gazebo clock
ros2 topic echo /clock --once
```

Both should show similar time values (simulation time, starting near 0)

### 3. Test Motion Execution
1. Open RViz Motion Planning panel
2. Set a goal state
3. Click "Plan"
4. Click "Execute"
5. Robot should move without timestamp errors

---

## Common Pitfalls

### ❌ Mistake 1: Using `generate_move_group_launch()` Utility
```python
# DON'T DO THIS - it doesn't forward use_sim_time properly
return generate_move_group_launch(moveit_config)
```

### ✅ Solution: Create Node Manually
```python
# DO THIS - explicit parameter passing
move_group_node = Node(
    package="moveit_ros_move_group",
    executable="move_group",
    parameters=[moveit_config.to_dict(), {"use_sim_time": use_sim_time}],
)
```

### ❌ Mistake 2: Forgetting Controller Spawners
```python
# Missing use_sim_time in spawner
spawner = Node(
    package="controller_manager",
    executable="spawner",
    arguments=["joint_state_broadcaster"],
)
```

### ✅ Solution: Add Parameter
```python
spawner = Node(
    package="controller_manager",
    executable="spawner",
    arguments=["joint_state_broadcaster"],
    parameters=[{"use_sim_time": use_sim_time}],  # Critical!
)
```

### ❌ Mistake 3: Missing SRDF in RViz
```python
# Only passing robot_description
parameters=[moveit_config.robot_description]
```

### ✅ Solution: Pass All MoveIt Parameters
```python
parameters=[
    moveit_config.robot_description,
    moveit_config.robot_description_semantic,  # SRDF!
    moveit_config.robot_description_kinematics,
    moveit_config.planning_pipelines,
    moveit_config.joint_limits,
    {"use_sim_time": use_sim_time},
]
```

---

## Summary Checklist

- [ ] Declare `use_sim_time` argument in ALL launch files
- [ ] Pass `use_sim_time` to robot_state_publisher
- [ ] Pass `use_sim_time` to ALL controller spawners
- [ ] Pass `use_sim_time` to move_group node
- [ ] Pass `use_sim_time` to RViz node
- [ ] Pass ALL MoveIt parameters to RViz (especially SRDF)
- [ ] Forward `use_sim_time` through launch_arguments when including child launches
- [ ] Verify all nodes report `use_sim_time=true` via `ros2 param get`

---

## References

- [ROS2 Simulation Time](https://docs.ros.org/en/jazzy/Tutorials/Advanced/Simulators/Simulation-Main.html)
- [MoveIt2 Launch Files](https://moveit.picknik.ai/main/doc/examples/move_group_interface/move_group_interface_tutorial.html)
- [ros2_control with Gazebo](https://control.ros.org/master/doc/gazebo_ros2_control/doc/index.html)