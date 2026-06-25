import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():

    pkg_share = get_package_share_directory('mon_robot')

    # URDF
    xacro_file = os.path.join(pkg_share, 'description', 'robot.urdf.xacro')
    robot_description = xacro.process_file(xacro_file).toxml()

    # Fichiers de configuration
    nav2_params = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    world_file  = os.path.join(pkg_share, 'world', 'labyrinthe.world')

    # Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('gazebo_ros'),
                         'launch', 'gazebo.launch.py')
        ]),
        launch_arguments={'world': world_file}.items()
    )

    # robot_state_publisher
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )

    # Spawn robot
    spawn = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'mon_robot',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.05'
        ],
        output='screen'
    )

    # SLAM en mode localisation (utilise la carte existante)
    slam_localization = Node(
        package='slam_toolbox',
        executable='localization_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'map_file_name': '/home/ros2/ros2_ws/map/labyrinthe_map',
            'map_start_at_dock': True,
        }]
    )

    # Nav2 bringup SANS map_server (SLAM s'en occupe)
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('nav2_bringup'),
                         'launch', 'navigation_launch.py')
        ]),
        launch_arguments={
            'use_sim_time': 'true',
            'params_file': nav2_params
        }.items()
    )

    # RViz
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        output='screen'
    )

    return LaunchDescription([
        rsp,
        gazebo,
        spawn,
        slam_localization,
        nav2,
        rviz,
    ])
