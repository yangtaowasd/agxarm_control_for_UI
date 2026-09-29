"""Check the real Nero contract and launch composition without hardware."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from launch import LaunchContext

from agxarm_control_gui.model import parse_state
from nero_arm_control.ros.telemetry import RosTelemetry


@pytest.mark.parametrize('mode', ('normal', 'impedance', 'admittance', 'hybrid'))
def test_gui_accepts_controller_telemetry(mode):
    messages = []
    node = SimpleNamespace(
        robot_model='nero', control_mode='joint', execute_motion=False,
        _current_interaction_mode=lambda: mode,
        interaction_state_publisher=SimpleNamespace(publish=messages.append),
    )
    RosTelemetry.from_controller_publishers(node).publish_interaction_state('test')
    state = parse_state(messages[0].data)
    assert state['interaction_mode'] == mode
    assert state['execute_motion'] is False
    assert state['available_modes'] == ['normal', 'impedance', 'admittance']
    assert json.loads(messages[0].data)['schema_version'] == 1


@pytest.mark.parametrize('model', ('nero', 'piper_l'))
@pytest.mark.parametrize('start', ('false', 'true'))
def test_launch_uses_nero_package_without_keyboard_reader(monkeypatch, model, start):
    path = Path(__file__).resolve().parents[1] / 'launch' / 'gui.launch.py'
    spec = importlib.util.spec_from_file_location('gui_launch_under_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    shares = []

    def share(package):
        shares.append(package)
        return '/installed/' + package

    monkeypatch.setattr(module, 'get_package_share_directory', share)
    monkeypatch.setattr(module, 'Node', lambda **kwargs: kwargs)
    context = LaunchContext()
    context.launch_configurations.update({
        'language': 'zh', 'robot_model': model, 'arm_namespace': '__robot__',
        'controller_config': '', 'common_config': '',
        'keyboard_topic': 'arm_keyboard_state', 'start_controller': start,
        'execute_motion': 'false', 'can_interface': 'can0',
    })
    nodes = module.nodes(context)
    assert shares == ['nero_arm_control']
    assert nodes[0]['package'] == 'agxarm_control_gui'
    assert nodes[0]['arguments'][-1] == '/installed/nero_arm_control/config/' + model + '.yaml'
    assert len(nodes) == (3 if start == 'true' else 1)
    if start == 'false':
        return
    controller, observer = nodes[1:]
    assert controller['package'] == observer['package'] == 'nero_arm_control'
    assert controller['executable'] == 'main.py'
    assert observer['executable'] == 'momentum_observer_node.py'
    assert controller['namespace'] == observer['namespace'] == model
    settings = controller['parameters'][-1]
    assert settings['execute_motion'] is False
    assert settings['move_home_on_start'] is False
    assert settings['reset_emergency_stop_on_start'] is False
    assert settings['keyboard_topic'] == 'arm_keyboard_state'
