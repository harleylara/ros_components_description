# Copyright 2024 Husarion sp. z o.o.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
from launch.conditions import IfCondition, UnlessCondition, LaunchConfigurationNotEquals
from launch.actions import DeclareLaunchArgument, LogInfo
from launch_ros.actions import Node
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import ReplaceString

def generate_launch_description():
    robot_namespace = LaunchConfiguration("robot_namespace")
    device_namespace = LaunchConfiguration("device_namespace")
    tf_prefix = LaunchConfiguration("tf_prefix")

    initial_joint_controllers = PathJoinSubstitution(
        [FindPackageShare("ros_components_description"), "config", "robotiq_controllers.yaml"]
    )

    namespace_warn = LogInfo(
        msg="Namespace is not implemented with manipulators. Look here: https://github.com/ros-controls/ros2_control/issues/1506",
        condition= LaunchConfigurationNotEquals(robot_namespace, "None")
    )

    # Using tf as namespace is caused by
    # https://github.com/ros-controls/ros2_control/issues/1506
    # After this fix the device_namespace should be used.
    namespaced_initial_joint_controllers_path = ReplaceString(
        source_file=initial_joint_controllers,
        replacements={
            "robotiq_85_left_knuckle_joint": [tf_prefix, "robotiq_85_left_knuckle_joint"],
            "  robotiq_gripper_controller:": ["  ", tf_prefix, "robotiq_gripper_controller:"],
            "  robotiq_activation_controller:": ["  ", tf_prefix, "robotiq_activation_controller:"],
        },
    )

    declare_device_namespace = DeclareLaunchArgument(
        "device_namespace",
        default_value="",
        description="Sensor namespace that will appear before all non absolute topics and TF frames, used for distinguishing multiple cameras on the same robot.",
    )

    declare_robot_namespace = DeclareLaunchArgument(
        "robot_namespace",
        default_value=EnvironmentVariable("ROBOT_NAMESPACE", default_value=""),
        description="Namespace which will appear in front of all topics (including /tf and /tf_static).",
    )

    declare_tf_prefix = DeclareLaunchArgument(
        "tf_prefix",
        default_value="",
        description="Prefix added for all links of device. Here used as fix for static transform publisher.",
    )

    robotiq_gripper_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            [tf_prefix, "robotiq_gripper_controller"],
            "-t",
            "position_controllers/GripperActionController",
            "-c",
            "controller_manager",
            "--controller-manager-timeout",
            "10",
            "--namespace",
            device_namespace,
            "--param-file",
            namespaced_initial_joint_controllers_path,
        ],
        namespace=robot_namespace,
    )

    return LaunchDescription(
        [
            declare_device_namespace,
            declare_robot_namespace,
            declare_tf_prefix,
            namespace_warn,
            robotiq_gripper_controller,
        ]
    )