"""Command-level interlocks remain effective when widget callbacks are bypassed."""

import pytest

from agxarm_control_gui.model import InputGate
from test_model import state


@pytest.mark.parametrize('mode', ['admittance', 'hybrid'])
@pytest.mark.parametrize('keys', [[0, 8], [12], [11], [9], [16], [23], [24]])
def test_compliant_modes_reject_keyboard_commands(mode, keys):
    assert not InputGate.command_allowed(keys, state(interaction_mode=mode))


@pytest.mark.parametrize('keys', [[6, 8], [0, 7, 8], [9], [16], [23], [24],
                                 [-1, 8], [0, 0], [True, 8], [12]])
def test_piper_joint_whitelist(keys):
    assert not InputGate.command_allowed(keys, state(robot_model='piper_l'))


def test_joint_and_cartesian_intents_cannot_cross_modes():
    assert InputGate.command_allowed([6, 8], state())
    assert InputGate.command_allowed([5, 7], state(robot_model='piper_l'))
    assert not InputGate.command_allowed([0, 8], state(control_mode='ik'))
    assert InputGate.command_allowed([12], state(control_mode='ik'))
    assert InputGate.command_allowed([11], state())
