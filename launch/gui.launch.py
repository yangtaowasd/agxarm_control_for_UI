"""Launch the console, optionally with its exclusive controller input path."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from pathlib import Path


def nodes(context):
    def value(name):
        return LaunchConfiguration(name).perform(context)

    def flag(name):
        text = value(name).lower()
        if text not in ('true', 'false'):
            raise ValueError(name + ' must be true or false')
        return text == 'true'

    language = value('language')
    if language not in ('zh', 'ja', 'en'):
        raise ValueError('language must be zh, ja or en')
    model = value('robot_model')
    if model not in ('nero', 'piper_l'):
        raise ValueError('robot_model must be nero or piper_l')
    ns = value('arm_namespace')
    if ns == '__robot__':
        ns = model
    share = Path(get_package_share_directory('nero_arm_control'))
    config = value('controller_config') or str(share / 'config' / (model + '.yaml'))
    common = value('common_config') or str(share / 'config' / 'common.yaml')
    result = [Node(
        package='agxarm_control_gui', executable='gui', output='screen',
        arguments=['--language', language, '--robot-model', model, '--namespace', ns,
                   '--keyboard-topic', value('keyboard_topic'), '--config', config],
    )]
    if flag('start_controller'):
        result.extend([
            Node(
                package='nero_arm_control', executable='main.py',
                name='arm_keyboard_controller', namespace=ns, output='screen',
                parameters=[common, config, {
                    'robot_model': model, 'can_interface': value('can_interface'),
                    'keyboard_topic': value('keyboard_topic'),
                    'execute_motion': flag('execute_motion'),
                    'move_home_on_start': False,
                    'reset_emergency_stop_on_start': False,
                    'disable_arm_on_shutdown': False,
                }],
            ),
            Node(
                package='nero_arm_control',
                executable='momentum_observer_node.py', name='arm_momentum_observer',
                namespace=ns, output='screen',
                parameters=[common, config, {'robot_model': model}],
            ),
        ])
    return result


def generate_launch_description():
    defaults = {
        'robot_model': 'nero', 'arm_namespace': '__robot__', 'language': 'zh',
        'start_controller': 'false', 'execute_motion': 'false',
        'can_interface': 'can0', 'keyboard_topic': 'arm_keyboard_state',
        'controller_config': '', 'common_config': '',
    }
    return LaunchDescription([
        *[DeclareLaunchArgument(key, default_value=value) for key, value in defaults.items()],
        OpaqueFunction(function=nodes),
    ])
