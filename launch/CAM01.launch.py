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

import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
)

from launch_ros.actions import Node
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from nav2_common.launch import ReplaceString
from ament_index_python import get_package_share_directory


def generate_launch_description():
    ros_components_description = get_package_share_directory("ros_components_description")
    gz_bridge_config_path = os.path.join(
        ros_components_description, "config", "gz_orbbec_astra_remappings.yaml"
    )

    robot_namespace = LaunchConfiguration("robot_namespace")
    tf_prefix = LaunchConfiguration("tf_prefix")
    device_namespace = LaunchConfiguration("device_namespace")
    camera_name = LaunchConfiguration("camera_name")
    gz_bridge_name = LaunchConfiguration("gz_bridge_name")

    namespaced_gz_bridge_config_path = ReplaceString(
        source_file=gz_bridge_config_path,
        replacements={
            "<robot_namespace>": robot_namespace,
            "<device_namespace>": device_namespace,
            "<camera_name>": camera_name,
        },
    )

    declare_device_namespace = DeclareLaunchArgument(
        "device_namespace",
        default_value="",
        description="Sensor namespace that will appear before all non absolute topics and TF frames, used for distinguishing multiple cameras on the same robot.",
    )

    declare_tf_prefix = DeclareLaunchArgument(
        "tf_prefix",
        default_value="",
        description="Prefix added for all links of device. Here used as fix for static transform publisher.",
    )

    declare_robot_namespace = DeclareLaunchArgument(
        "robot_namespace",
        default_value=EnvironmentVariable("ROBOT_NAMESPACE", default_value=""),
        description="Namespace which will appear in front of all topics (including /tf and /tf_static).",
    )

    declare_camera_name = DeclareLaunchArgument(
        "camera_name",
        default_value="camera",
        description="Name of the camera. It will appear before all tfs and topics.",
    )

    declare_gz_bridge_name = DeclareLaunchArgument(
        "gz_bridge_name",
        default_value="gz_bridge",
        description="Name of gz bridge node.",
    )

    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name=gz_bridge_name,
        parameters=[{"config_file": namespaced_gz_bridge_config_path}],
        namespace=robot_namespace,
        output="screen",
    )

    # The frame of the point cloud from ignition gazebo 6 isn't provided by <frame_id>.
    # See https://github.com/gazebosim/gz-sensors/issues/239
    #  panther/base_link//front_cam_ns/front_cam_tf_camera_depth_optical_frame
    # panther/base_link//front_cam_ns/front_cam_tf_camera_depth_optical_frame
    # panther/base_link//front_cam_ns/front_cam_tf_camera_orbbec_astra_depth
    static_transform_publisher = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="point_cloud_tf",
        output="log",
        arguments=[
            "0",
            "0",
            "0",
            "1.57",
            "-1.57",
            "0",
            LaunchConfiguration(
                "parent_frame", default=[tf_prefix, "_", camera_name, "_depth_optical_frame"]
            ),
            LaunchConfiguration(
                "child_frame",
                default=[
                    "panther/base_link//",
                    device_namespace,
                    "/",
                    tf_prefix,
                    "_",
                    camera_name,
                    "_orbbec_astra_depth",
                ],
            ),
        ],
        remappings=[
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
        ],
        parameters=[{"use_sim_time": True}],
        namespace=robot_namespace,
    )

    return LaunchDescription(
        [
            declare_device_namespace,
            declare_robot_namespace,
            declare_tf_prefix,
            declare_camera_name,
            declare_gz_bridge_name,
            gz_bridge,
            static_transform_publisher,
        ]
    )
