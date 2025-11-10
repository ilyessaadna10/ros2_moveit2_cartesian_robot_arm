from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_demo_launch
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    # Get path to the gantry package
    gantry_package_path = get_package_share_directory("gantry")
    urdf_file = os.path.join(gantry_package_path, "urdf", "parallel_beam_gantry.xacro")
    
    moveit_config = (
        MoveItConfigsBuilder("parallel_beam_gantry", package_name="gantry_moveit_config")
        .robot_description(file_path=urdf_file)
        .to_moveit_configs()
    )
    return generate_demo_launch(moveit_config)