import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro

def generate_launch_description():

    pkg_share = get_package_share_directory('mon_robot')

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # Fichiers
    xacro_file  = os.path.join(pkg_share, 'description', 'robot.urdf.xacro')
    nav2_params = os.path.join(pkg_share, 'config',      'nav2_params.yaml')
    world_file  = os.path.join(pkg_share, 'world',       'labyrinthe.world')
    map_file    = '/home/ros2/ros2_ws/src/map/labyrinthe_map.yaml'
    rviz_config = os.path.join(pkg_share, 'config',      'navigation.rviz')

    # URDF
    robot_description = xacro.process_file(xacro_file).toxml()

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
            'use_sim_time': use_sim_time
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

    # Static transform chassis -> lidar_link
    static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0.1', '0', '0.160', '0', '0', '0', 'chassis', 'lidar_link']
    )

    # Nav2 bringup complet (map_server + amcl + navigation)
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('nav2_bringup'),
                         'launch', 'bringup_launch.py')
        ]),
        launch_arguments={
            'map': map_file,
            'use_sim_time': use_sim_time,
            'params_file': nav2_params
        }.items()
    )

    # RViz avec config pre-chargee
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use Gazebo clock if true'
        ),
        rsp,
        gazebo,
        spawn,
        static_tf,
        nav2,
        rviz,
    ])