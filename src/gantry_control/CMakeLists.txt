cmake_minimum_required(VERSION 3.8)
project(gantry_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(geometry_msgs REQUIRED)

# Build the executable
add_executable(simple_move src/simple_move.cpp)
ament_target_dependencies(simple_move
  rclcpp
  moveit_ros_planning_interface
  geometry_msgs
)

# Install the executable
install(TARGETS
  simple_move
  DESTINATION lib/${PROJECT_NAME}
)

# Install the launch directory
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()