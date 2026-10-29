import os

from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node, SetParameter
from launch_ros.descriptions import ParameterValue
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import (
    generate_move_group_launch,
    generate_moveit_rviz_launch,
)


def generate_launch_description():
    """Build the PX150 Gazebo bringup and its dependent controller/MoveIt launches.

    The robot is spawned from the same Xacro description used to configure
    MoveIt. Event handlers defer controller startup until model creation exits,
    then defer MoveIt until all requested controllers have been spawned.
    """
    # Convert the launch argument to a boolean ROS parameter for every node.
    use_sim_time = ParameterValue(
        LaunchConfiguration("use_sim_time"), value_type=bool
    )

    # Use the installed description package so the launch works after install.
    description_path = (
        get_package_share_path("custom_interbotix_xarms_description")
        / "urdf"
        / "px150.urdf.xacro"
    )
    # Enable the Gazebo ros2_control hardware plugin in the robot description.
    robot_description = ParameterValue(
        Command(["xacro ", str(description_path), " gz_sim:=true"]),
        value_type=str,
    )

    robot_state_publisher = Node(
        name="robot_state_publisher",
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": use_sim_time,
            }
        ],
    )

    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_path("ros_gz_sim"),
                "launch",
                "gz_sim.launch.py",
            )
        ),
        launch_arguments={"gz_args": "-r -v 4"}.items(),
    )

    # Forward Gazebo's simulation clock to ROS for use_sim_time consumers.
    clock_bridge = Node(
        name="clock_bridge",
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Insert the same description published by robot_state_publisher into Gazebo.
    gz_model_create = Node(
        name="gz_model_create",
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "/robot_description", "-name", "px150"],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    def controller_spawner(controller_name):
        """Create a controller_manager spawner for the named controller."""
        return Node(
            name=f"{controller_name}_spawner",
            package="controller_manager",
            executable="spawner",
            arguments=[
                controller_name,
                "--controller-manager",
                "/controller_manager",
                "--controller-manager-timeout",
                "120",
            ],
            parameters=[{"use_sim_time": use_sim_time}],
        )

    # These are configured controllers: arm, gripper, then joint-state publisher.
    arm_controller_spawner = controller_spawner("arm_controller")
    gripper_controller_spawner = controller_spawner("gripper_controller")
    joint_state_broadcaster_spawner = controller_spawner(
        "joint_state_broadcaster"
    )

    # Share the Gazebo-enabled Xacro with MoveIt so its planning model matches
    # the robot instantiated in simulation.
    moveit_config = (
        MoveItConfigsBuilder(
            "px150", package_name="custom_interbotix_xarms_moveit"
        )
        .robot_description(
            file_path=str(description_path),
            mappings={"gz_sim": "true"},
        )
        .to_moveit_configs()
    )
    move_group_launch = generate_move_group_launch(moveit_config)
    moveit_rviz_launch = generate_moveit_rviz_launch(moveit_config)

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use simulation clock time",
            ),
            # Set the default for nested launch actions, including MoveIt.
            SetParameter(name="use_sim_time", value=use_sim_time),
            robot_state_publisher,
            gz_sim_launch,
            clock_bridge,
            # Keep controller and MoveIt startup ordered after each process exits.
            RegisterEventHandler(
                OnProcessExit(
                    target_action=gz_model_create,
                    on_exit=[arm_controller_spawner],
                )
            ),
            RegisterEventHandler(
                OnProcessExit(
                    target_action=arm_controller_spawner,
                    on_exit=[gripper_controller_spawner],
                )
            ),
            RegisterEventHandler(
                OnProcessExit(
                    target_action=gripper_controller_spawner,
                    on_exit=[joint_state_broadcaster_spawner],
                )
            ),
            RegisterEventHandler(
                OnProcessExit(
                    target_action=joint_state_broadcaster_spawner,
                    on_exit=(
                        move_group_launch.entities + moveit_rviz_launch.entities
                    ),
                )
            ),
            gz_model_create,
        ]
    )
