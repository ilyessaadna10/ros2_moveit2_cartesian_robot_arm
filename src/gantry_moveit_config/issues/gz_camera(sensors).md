# Adding Cameras in Gazebo Harmonic with ROS2 Bridge

## Overview

This guide explains how to add camera sensors in Gazebo Harmonic and bridge them to ROS2. **Important**: The approach differs significantly from Gazebo Classic and even earlier Gazebo versions (Ignition).

## Key Architectural Difference

### Gazebo Harmonic vs Classic/Ignition

**Gazebo Classic** used individual sensor plugins attached to each sensor:
```xml
<!-- OLD WAY (Gazebo Classic) - DON'T USE -->
<gazebo reference="camera_link">
  <sensor type="camera" name="camera1">
    <plugin name="camera_controller" filename="libgazebo_ros_camera.so"/>
  </sensor>
</gazebo>
```

**Gazebo Harmonic/Ignition** uses a generic **world-level sensor system plugin** that handles ALL sensors:
- Sensors are defined in the robot model (URDF/SDF)
- A single world-level plugin manages all sensors
- No individual sensor plugins needed
- Bridging is handled separately via `ros_gz_bridge` or `ros_gz_image`

---

## Step 1: Configure World File

Your world file **MUST** include the sensors system plugin. Without this, cameras will not work.

### Minimum Required World Configuration

```xml
<?xml version="1.0" ?>
<sdf version="1.8">
  <world name="camera_world">
    
    <!-- Physics System -->
    <plugin filename="gz-sim-physics-system"
            name="gz::sim::systems::Physics">
    </plugin>
    
    <!-- User Commands -->
    <plugin filename="gz-sim-user-commands-system"
            name="gz::sim::systems::UserCommands">
    </plugin>
    
    <!-- Scene Broadcaster -->
    <plugin filename="gz-sim-scene-broadcaster-system"
            name="gz::sim::systems::SceneBroadcaster">
    </plugin>
    
    <!-- CRITICAL: Sensors System Plugin -->
    <!-- This handles ALL sensors (cameras, lidar, IMU, etc.) -->
    <plugin filename="gz-sim-sensors-system"
            name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    
    <!-- Lighting -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>
    
    <!-- Ground Plane -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane><normal>0 0 1</normal></plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane><normal>0 0 1</normal><size>100 100</size></plane>
          </geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    
  </world>
</sdf>
```

**Key Point**: The `gz-sim-sensors-system` plugin with `ogre2` render engine is **mandatory** for any sensor (camera, depth camera, lidar, etc.) to function.

---

## Step 2: Define Camera in URDF/Xacro

### Camera Xacro Macro

Create a file `camera.xacro`:

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">

  <xacro:macro name="camera_sensor" params="*origin name parent:=base_link">
    
    <!-- Camera Link -->
    <link name="${name}_camera_link">
      <visual>
        <origin xyz="0 0 0" rpy="0 0 0"/>
        <geometry>
          <box size="0.03 0.08 0.03"/>
        </geometry>
        <material name="camera_black">
          <color rgba="0.1 0.1 0.1 1.0"/>
        </material>
      </visual>
      
      <collision>
        <origin xyz="0 0 0" rpy="0 0 0"/>
        <geometry>
          <box size="0.03 0.08 0.03"/>
        </geometry>
      </collision>
      
      <inertial>
        <mass value="0.06"/>
        <inertia ixx="1e-6" ixy="0" ixz="0" 
                 iyy="1e-6" iyz="0" 
                 izz="1e-6"/>
      </inertial>
    </link>
    
    <!-- Joint to Parent -->
    <joint name="${name}_camera_joint" type="fixed">
      <parent link="${parent}"/>
      <child link="${name}_camera_link"/>
      <xacro:insert_block name="origin"/>
    </joint>
    
    <!-- Optical Frame (ROS Convention) -->
    <link name="${name}_camera_optical_link"/>
    
    <joint name="${name}_camera_optical_joint" type="fixed">
      <parent link="${name}_camera_link"/>
      <child link="${name}_camera_optical_link"/>
      <!-- Optical frame: X=right, Y=down, Z=forward -->
      <origin xyz="0 0 0" rpy="-1.570796 0 -1.570796"/>
    </joint>
    
    <!-- Gazebo Sensor Definition -->
    <gazebo reference="${name}_camera_link">
      <sensor name="${name}_sensor" type="camera">
        <always_on>true</always_on>
        <update_rate>10</update_rate>
        <visualize>true</visualize>
        <topic>/camera/${name}/image_raw</topic>
        
        <camera name="${name}_camera">
          <horizontal_fov>1.396</horizontal_fov>
          
          <image>
            <width>640</width>
            <height>480</height>
            <format>R8G8B8</format>
          </image>
          
          <clip>
            <near>0.1</near>
            <far>100</far>
          </clip>
          
          <!-- Link to optical frame -->
          <optical_frame_id>${name}_camera_optical_link</optical_frame_id>
          
          <!-- Optional: Add noise for realism -->
          <noise>
            <type>gaussian</type>
            <mean>0.0</mean>
            <stddev>0.007</stddev>
          </noise>
        </camera>
      </sensor>
    </gazebo>
    
  </xacro:macro>

</robot>
```

### Using the Camera Macro

In your main robot xacro file:

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="my_robot">

  <!-- Include camera macro -->
  <xacro:include filename="$(find my_package)/urdf/camera.xacro"/>
  
  <!-- Your robot definition -->
  <link name="base_link">
    <!-- ... -->
  </link>
  
  <!-- Add camera -->
  <xacro:camera_sensor name="front" parent="base_link">
    <!-- Position camera 0.2m forward, 0.1m up -->
    <origin xyz="0.2 0 0.1" rpy="0 0 0"/>
  </xacro:camera_sensor>
  
</robot>
```

### Key Elements Explained

| Element | Purpose |
|---------|---------|
| `<topic>` | Gazebo Transport topic name (used for bridging) |
| `<optical_frame_id>` | Links sensor to ROS optical frame convention |
| `<update_rate>` | Frames per second (10-30 Hz recommended) |
| `<visualize>` | Shows camera view in Gazebo GUI |
| `<always_on>` | Keep sensor active continuously |

---

## Step 3: Bridge Camera to ROS2

There are **two bridging options** for cameras:

### Option A: `ros_gz_image` (Recommended for Cameras)

The `image_bridge` from `ros_gz_image` package is optimized for camera images and supports `image_transport` compression.

```python
from launch_ros.actions import Node

# Bridge camera image
image_bridge = Node(
    package='ros_gz_image',
    executable='image_bridge',
    arguments=['/camera/front/image_raw'],
    output='screen'
)

# Bridge camera info separately
info_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=[
        '/camera/front/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo'
    ],
    output='screen'
)
```

### Option B: `ros_gz_bridge` (Generic)

The generic parameter bridge works but doesn't support image compression (higher bandwidth usage).

```python
from launch_ros.actions import Node

camera_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=[
        '/camera/front/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
        '/camera/front/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo'
    ],
    output='screen'
)
```

### Bridge Direction Syntax

| Syntax | Direction |
|--------|-----------|
| `@` | Bidirectional |
| `[` | Gazebo → ROS2 (one-way) |
| `]` | ROS2 → Gazebo (one-way) |

---

## Step 4: Complete Launch File Example

```python
#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    
    pkg_share = FindPackageShare('my_package')
    world_file = PathJoinSubstitution([pkg_share, 'worlds', 'camera_world.sdf'])
    
    # Launch Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('ros_gz_sim'),
            '/launch/gz_sim.launch.py'
        ]),
        launch_arguments={'gz_args': ['-r ', world_file]}.items()
    )
    
    # Spawn robot
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'my_robot'
        ],
        output='screen'
    )
    
    # Bridge clock
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )
    
    # Bridge camera (recommended method)
    camera_image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['/camera/front/image_raw'],
        output='screen'
    )
    
    camera_info_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/camera/front/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo'
        ],
        output='screen'
    )
    
    return LaunchDescription([
        gazebo,
        spawn_robot,
        clock_bridge,
        camera_image_bridge,
        camera_info_bridge,
    ])
```

---

## Step 5: Verify Camera is Working

### Check Gazebo Topics

```bash
# List all Gazebo topics
gz topic -l

# Echo camera topic
gz topic -e -t /camera/front/image_raw
```

### Check ROS2 Topics

```bash
# List ROS2 topics
ros2 topic list

# Get camera info
ros2 topic info /camera/front/image_raw
ros2 topic echo /camera/front/camera_info

# Check publishing rate
ros2 topic hz /camera/front/image_raw
```

### View Camera Feed

```bash
# Using rqt_image_view
ros2 run rqt_image_view rqt_image_view

# Or using RViz2
rviz2
# Add -> By topic -> /camera/front/image_raw -> Camera
```

---

## Common Issues and Solutions

### 1. Camera Not Publishing

**Problem**: No camera topics visible.

**Solution**: Check that `gz-sim-sensors-system` plugin is in your world file with `ogre2` render engine.

```bash
# Verify world plugins loaded
gz plugin -l
```

### 2. "Frame Not Found" Errors in RViz

**Problem**: RViz shows "Transform from [overhead_camera_optical_link] to [map] is not available"

**Solution**: Ensure you have `robot_state_publisher` running and your optical frame is defined correctly.

### 3. High Bandwidth / Dropped Messages

**Problem**: "Message Filter dropping message: queue is full"

**Solutions**:
- Reduce update rate: `<update_rate>10</update_rate>`
- Reduce resolution: `<width>640</width> <height>480</height>`
- Use `ros_gz_image` instead of `parameter_bridge` for compression

### 4. Black/Dark Images

**Problem**: Camera shows black or very dark images.

**Solutions**:
- Add proper lighting to your world (sun/directional light)
- Increase ambient light values
- Check camera is not inside collision geometry
- Verify `<visualize>true</visualize>` is set

---

## Performance Optimization

### Recommended Camera Settings

| Use Case | Resolution | Update Rate | Format |
|----------|-----------|-------------|---------|
| Navigation | 640x480 | 10 Hz | R8G8B8 |
| Manipulation | 1280x720 | 15 Hz | R8G8B8 |
| High-quality | 1920x1080 | 30 Hz | R8G8B8 |
| Depth cameras | 640x480 | 10 Hz | R_FLOAT32 |

### Multiple Cameras

For robots with multiple cameras, instantiate the macro multiple times:

```xml
<!-- Front camera -->
<xacro:camera_sensor name="front" parent="base_link">
  <origin xyz="0.3 0 0.2" rpy="0 0 0"/>
</xacro:camera_sensor>

<!-- Rear camera -->
<xacro:camera_sensor name="rear" parent="base_link">
  <origin xyz="-0.3 0 0.2" rpy="0 0 3.14159"/>
</xacro:camera_sensor>

<!-- Overhead camera -->
<xacro:camera_sensor name="overhead" parent="world">
  <origin xyz="0 0 5" rpy="0 1.5708 0"/>
</xacro:camera_sensor>
```

Bridge each camera separately in your launch file.

---

## Camera Orientation Guide

Cameras follow ROS optical frame convention: **X=right, Y=down, Z=forward**

### Common Orientations (RPY values)

| Direction | Roll | Pitch | Yaw | RPY Values |
|-----------|------|-------|-----|------------|
| Forward | 0° | 0° | 0° | `0 0 0` |
| Backward | 0° | 0° | 180° | `0 0 3.14159` |
| Left | 0° | 0° | 90° | `0 0 1.5708` |
| Right | 0° | 0° | -90° | `0 0 -1.5708` |
| Down | 0° | 90° | 0° | `0 1.5708 0` |
| Up | 0° | -90° | 0° | `0 -1.5708 0` |

**Note**: Values are in radians (π ≈ 3.14159, π/2 ≈ 1.5708)

---

## Differences from Gazebo Ignition

While Gazebo Harmonic and Ignition share the same architecture, there are some differences:

| Feature | Ignition | Harmonic |
|---------|----------|----------|
| Sensor plugin | World-level | World-level (same) |
| Wide-angle camera | Limited | Full support |
| Optical frame tag | Optional | Recommended |
| Camera distortion | Basic | Enhanced |
| ROS2 bridge package | `ros_ign_bridge` | `ros_gz_bridge` |

**Migration Note**: If migrating from Ignition, rename packages:
- `ros_ign_bridge` → `ros_gz_bridge`
- `ros_ign_image` → `ros_gz_image`
- `ros_ign_sim` → `ros_gz_sim`

---

## Summary Checklist

- ✅ Add `gz-sim-sensors-system` plugin to world file
- ✅ Define camera link with proper inertial properties
- ✅ Create optical frame with correct transformation
- ✅ Configure `<gazebo>` sensor with topic name
- ✅ Use `ros_gz_image` for bridging camera images
- ✅ Bridge `camera_info` separately with `ros_gz_bridge`
- ✅ Verify topics in both Gazebo and ROS2
- ✅ Test visualization in RViz or rqt_image_view

---

## Additional Resources

- [Gazebo Harmonic Documentation](https://gazebosim.org/docs/harmonic)
- [ros_gz Bridge Documentation](https://github.com/gazebosim/ros_gz)
- [SDF Sensor Specification](http://sdformat.org/spec?elem=sensor)
- [ROS2 Image Transport](https://github.com/ros-perception/image_common)

---

**Last Updated**: November 2025  
**Gazebo Version**: Harmonic  
**ROS Version**: ROS2 Humble/Jazzy