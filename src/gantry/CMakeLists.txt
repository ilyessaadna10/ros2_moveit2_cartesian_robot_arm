cmake_minimum_required(VERSION 3.8)
project(gantry)

# -----------------------------------------------------------------------------
# Compiler settings
# -----------------------------------------------------------------------------
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# -----------------------------------------------------------------------------
# Find ROS 2 & Gazebo dependencies
# -----------------------------------------------------------------------------
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Gazebo ROS integration
find_package(ros_gz_sim REQUIRED)
find_package(ros_gz_bridge REQUIRED)
find_package(ros_gz_image REQUIRED)

# Other common dependencies
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(xacro REQUIRED)

# -----------------------------------------------------------------------------
# Python package
# -----------------------------------------------------------------------------
ament_python_install_package(${PROJECT_NAME})

# -----------------------------------------------------------------------------
# Install directories
# -----------------------------------------------------------------------------
install(
  DIRECTORY
    launch
    urdf
    worlds
    
    
  DESTINATION
    share/${PROJECT_NAME}/
)

# -----------------------------------------------------------------------------
# Testing (optional but recommended)
# -----------------------------------------------------------------------------
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# -----------------------------------------------------------------------------
# ament package
# -----------------------------------------------------------------------------
ament_package()