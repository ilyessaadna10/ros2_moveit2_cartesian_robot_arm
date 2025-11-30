#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import Empty
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped
from moveit_msgs.action import MoveGroup
import time

# Settings
PLANNING_GROUP_ARM = "arm"       # Check this in your SRDF or MoveIt Setup
PLANNING_GROUP_GRIPPER = "gripper"
SPHERE_NAME = "sphere_red"         # MUST match the name in Gazebo Left Panel

class GantryPicker(Node):
    def __init__(self):
        super().__init__('gantry_picker')

        # 1. Publishers for the "Magic Glue" (Gazebo Plugin)
        self.attach_pub = self.create_publisher(Empty, '/gripper/attach', 10)
        self.detach_pub = self.create_publisher(Empty, '/gripper/detach', 10)

        # 2. MoveIt Action Client (We use the action interface directly for simplicity)
        self.move_group_client = ActionClient(self, MoveGroup, 'move_action')
        
        self.get_logger().info("--- Gantry Picker Ready ---")

    def attach_object(self):
            msg = Empty()
            for i in range(5):
                self.attach_pub.publish(msg)
                time.sleep(0.1) # Send it multiple times to be sure
            self.get_logger().info(f">>> ATTACH COMMAND SENT TO {SPHERE_NAME}")

    def detach_object(self):
        """Tells Gazebo to release the sphere"""
        msg = Empty()
        self.detach_pub.publish(msg)
        self.get_logger().info(f">>> DETACHING {SPHERE_NAME} (Gazebo Logic)")

    # NOTE: For a full implementation, we would use the MoveIt Python bindings.
    # However, since you are just starting, setting up the python bindings 
    # environment can be tricky. 
    # Ideally, you should run this logic alongside Rviz using the 'Plan & Execute'
    # button first to test the coordinates, OR use the moveit_py library.
    
    # Below is a placeholder for the logic flow you will execute.
    
def main(args=None):
    rclpy.init(args=args)
    node = GantryPicker()

    # Wait for things to settle
    time.sleep(2.0)

    print("\n=== STARTING PICK SEQUENCE ===")
    
    # ---------------------------------------------------------
    # PART 1: MOVE TO PRE-GRASP (Manually or via MoveIt)
    # ---------------------------------------------------------
    # For this script to actually MOVE the robot, you need 'moveit_py' 
    # or the Action Client. Since setting up the client manually is verbose,
    # I recommend verifying the motion in RViz first, then using this script
    # strictly for the Attach/Detach logic while you command MoveIt.
    
    input("1. Move robot to PRE-GRASP in RViz (Above sphere). Press Enter when done...")

    input("2. Move robot to GRASP pose in RViz (Surrounding sphere). Press Enter when done...")

    # ---------------------------------------------------------
    # PART 2: ATTACH (The Grasp)
    # ---------------------------------------------------------
    # 1. Close Gripper (Visual)
    # You would typically send a command to 'gripper_controller' here.
    print("Simulating Gripper Closing...")
    
    # 2. Activate Physics Link
    node.attach_object()
    
    input("3. Sphere should be attached now! Lift the arm in RViz. Press Enter to DETACH...")

    # ---------------------------------------------------------
    # PART 3: DETACH (The Place)
    # ---------------------------------------------------------
    node.detach_object()
    print("Sphere detached.")

    rclpy.shutdown()

if __name__ == '__main__':
    main()