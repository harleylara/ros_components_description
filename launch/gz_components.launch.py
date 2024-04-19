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
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)

from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, EnvironmentVariable


def get_value_or_none(node: yaml.Node, key: str):
    try:
        return node[key]
    except KeyError:
        return 'None'


def get_launch_descriptions_from_yaml_node(
    node: yaml.Node, package: os.PathLike, namespace: str
) -> IncludeLaunchDescription:
    actions = []
    for component in node["components"]:

        actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [package, "/launch/", component["type"], ".launch.py"]
                ),
                launch_arguments={
                    "robot_namespace": namespace,
                    "device_namespace": get_value_or_none(component, "namespace"),
                    "tf_prefix": get_value_or_none(component, "tf_prefix"),
                    "gz_bridge_name": component["namespace"][1:] + "_gz_bridge",
                    "camera_name": get_value_or_none(component, "name"),
                }.items(),
            )
        )

    return actions


def launch_setup(context, *args, **kwargs):
    ros_components_description = get_package_share_directory("ros_components_description")

    components_config_path = LaunchConfiguration("components_config_path").perform(context)
    namespace = LaunchConfiguration("namespace").perform(context)

    components_config = None
    with open(os.path.join(components_config_path), 'r') as file:
        components_config = yaml.safe_load(file)

    actions = []
    if components_config != None:
        actions += get_launch_descriptions_from_yaml_node(
            components_config, ros_components_description, namespace
        )

    return actions


def generate_launch_description():
    declare_components_config_path_arg = DeclareLaunchArgument(
        "components_config_path",
        default_value="None",
        description=(
            "Additional components configuration file. Components described in this file "
            "are dynamically included in Panther's urdf."
            "Panther options are described here "
            "https://husarion.com/manuals/panther/panther-options/"
        ),
    )

    declare_namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value=EnvironmentVariable("ROBOT_NAMESPACE", default_value=""),
        description="Add namespace to all launched nodes",
    )

    actions = [
        declare_components_config_path_arg,
        declare_namespace_arg,
        OpaqueFunction(function=launch_setup),
    ]

    return LaunchDescription(actions)