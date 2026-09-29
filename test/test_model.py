"""Exercise the input gate against stale, conflicting and faulted states."""

import json

import pytest

from nero_arm_control.teleop import ArmJointJogState, KEY_COUNT, KEY_ESTOP
from agxarm_control_gui.model import InputGate, namespace, parse_state, validate_config


def state(**updates):
    value = dict(schema_version=1, robot_model='nero', interaction_mode='normal',
                 control_mode='joint', execute_motion=True, arm_ready=True,
                 emergency_stopped=False, interaction_transitioning=False)
    value.update(updates)
    return value


def test_joint_selection_and_release_use_backend_protocol():
    gate = InputGate()
    jog = ArmJointJogState([(-1, 1)] * 7, 0.005)
    gate.press([6, 8])
    assert gate.keys == [0] * KEY_COUNT
    gate.armed = True
    gate.press([6, 8])
    jog.update(gate.keys)
    assert jog.target_joints == [0] * 6 + [0.005]
    gate.clear()
    jog.update(gate.keys)
    assert jog.target_joints[-1] == 0.005
    gate.disarm()
    gate.press([6, 8])
    assert not any(gate.keys)


def test_estop_works_disarmed_and_latches_future_input():
    gate = InputGate()
    gate.emergency_stop()
    assert gate.keys[KEY_ESTOP] == 1 and sum(gate.keys) == 1
    assert gate.estopped and not gate.armed
    gate.armed = True
    gate.press([8])
    assert not any(gate.keys)


@pytest.mark.parametrize('updates,graph,fresh,conflict,pending', [
    ({}, False, True, False, False),
    ({}, True, False, False, False),
    ({}, True, True, True, False),
    ({}, True, True, False, True),
    ({'arm_ready': False}, True, True, False, False),
    ({'emergency_stopped': True}, True, True, False, False),
    ({'interaction_transitioning': True}, True, True, False, False),
    ({'interaction_fault_reason': 'fault'}, True, True, False, False),
    ({'robot_model': 'piper_l'}, True, True, False, False),
])
def test_guard_rejects_unsafe_input(updates, graph, fresh, conflict, pending):
    assert not InputGate.permission(state(**updates), 'nero', graph, fresh,
                                    conflict, pending)[0]


def test_dry_run_does_not_require_fabricated_feedback():
    assert InputGate.permission(state(execute_motion=False), 'nero', True,
                                False, False, False)[0]
    assert InputGate.permission(state(), 'nero', True, True, False, False)[0]


@pytest.mark.parametrize('text', ['null', '[]', '{"schema_version": 2}',
                                 json.dumps(state(execute_motion='false'))])
def test_invalid_state_cannot_enable_input(text):
    with pytest.raises(ValueError):
        parse_state(text)


def test_config_round_trip_and_nonfinite_rejection():
    text = '"/**/arm_keyboard_controller":\n  ros__parameters:\n    mit_kp: [0.3, 0.5]\n'
    assert validate_config(text)['/**/arm_keyboard_controller']['ros__parameters']['mit_kp'] == [0.3, 0.5]
    for bad in ('{}', '[]', 'a: 1', 'a: {ros__parameters: {kp: .nan}}'):
        with pytest.raises(ValueError):
            validate_config(bad)


def test_namespace_validation():
    assert namespace(' /nero/ ') == '/nero'
    assert namespace('/') == ''
    assert namespace('cell/nero') == '/cell/nero'
    for bad in ('/nero//arm', '123', 'a b', 'a;cmd'):
        with pytest.raises(ValueError):
            namespace(bad)
