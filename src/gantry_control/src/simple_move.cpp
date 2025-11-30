#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.hpp>

const std::string PLANNING_GROUP = "gantry"; 

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  
  rclcpp::NodeOptions node_options;
  node_options.automatically_declare_parameters_from_overrides(true);
  auto node = rclcpp::Node::make_shared("simple_move_node", node_options);

  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  std::thread([&executor]() { executor.spin(); }).detach();

  using moveit::planning_interface::MoveGroupInterface;
  auto move_group = MoveGroupInterface(node, PLANNING_GROUP);
  move_group.setPlannerId("RRTConnect");

  move_group.setMaxVelocityScalingFactor(0.5); 
  move_group.setMaxAccelerationScalingFactor(0.5);
  move_group.setPlanningTime(10.0);  // Increased timeout

  // =======================================================
  // POINT A: Move sliders to specific positions
  // Joint order: [x_slider_joint, y_slider_joint, z_slider_joint]
  // =======================================================
  RCLCPP_INFO(node->get_logger(), "Moving to POINT A...");
  
  std::vector<double> joint_positions_a = {
    0.6,   // x_slider_joint: move 0.6m along X axis
    0.2,   // y_slider_joint: move 0.2m along Y axis  
    0.0    // z_slider_joint: keep at center Z
  };

  move_group.setJointValueTarget(joint_positions_a);
  
  moveit::planning_interface::MoveGroupInterface::Plan plan_a;
  auto result_a = move_group.plan(plan_a);
  
  if (result_a == moveit::core::MoveItErrorCode::SUCCESS) {
    move_group.execute(plan_a);
    RCLCPP_INFO(node->get_logger(), "✓ Reached Point A.");
  } else {
    RCLCPP_ERROR(node->get_logger(), "✗ Failed to plan to Point A!");
  }

  std::this_thread::sleep_for(std::chrono::seconds(2));

  // =======================================================
  // POINT B: Move to different position
  // =======================================================
  RCLCPP_INFO(node->get_logger(), "Moving to POINT B...");

  std::vector<double> joint_positions_b = {
    -0.6,  // x_slider_joint: move -0.6m along X axis
    -0.2,  // y_slider_joint: move -0.2m along Y axis
    0.1    // z_slider_joint: move down 0.1m
  };

  move_group.setJointValueTarget(joint_positions_b);

  moveit::planning_interface::MoveGroupInterface::Plan plan_b;
  auto result_b = move_group.plan(plan_b);
  
  if (result_b == moveit::core::MoveItErrorCode::SUCCESS) {
    move_group.execute(plan_b);
    RCLCPP_INFO(node->get_logger(), "✓ Reached Point B.");
  } else {
    RCLCPP_ERROR(node->get_logger(), "✗ Failed to plan to Point B!");
  }

  // =======================================================
  //  target "home"
  // =======================================================
  std::this_thread::sleep_for(std::chrono::seconds(2));
  RCLCPP_INFO(node->get_logger(), "Returning to HOME...");
  
  move_group.setNamedTarget("home");
  auto result_home = move_group.move();
  
  if (result_home == moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_INFO(node->get_logger(), "✓ Returned to home.");
  }

  rclcpp::shutdown();
  return 0;
}