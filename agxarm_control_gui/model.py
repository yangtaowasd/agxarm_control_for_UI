"""Transport-independent input gate and configuration validation."""

import json
import math
import re

import yaml

from armbycontroller.teleop import KEY_COUNT, KEY_ESTOP
from armbycontroller import teleop as K

from .i18n import LocalizedError, translate


def namespace(value):
    """Normalize a namespace without accepting ROS name substitutions."""
    value = value.strip().strip('/')
    if value and not all(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', part)
                         for part in value.split('/')):
        raise LocalizedError('invalid_namespace')
    return '/' + value if value else ''


def parse_state(text):
    """Reject malformed or incompatible snapshots before enabling input."""
    value = json.loads(text)
    if not isinstance(value, dict) or value.get('schema_version') != 1:
        raise LocalizedError('invalid_schema')
    if value.get('robot_model') not in ('nero', 'piper_l'):
        raise LocalizedError('invalid_robot')
    if value.get('interaction_mode') not in (
            'normal', 'impedance', 'admittance', 'hybrid'):
        raise LocalizedError('invalid_interaction')
    if value.get('control_mode') not in ('joint', 'ik'):
        raise LocalizedError('invalid_control')
    for key in ('execute_motion', 'arm_ready', 'emergency_stopped',
                'interaction_transitioning'):
        if type(value.get(key)) is not bool:
            raise LocalizedError('invalid_boolean', key)
    return value


def validate_config(text):
    """Check ROS YAML structure and finite values, not controller physics."""
    value = yaml.safe_load(text)
    if not isinstance(value, dict) or not value:
        raise LocalizedError('invalid_yaml_mapping')
    def finite(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise LocalizedError('nonfinite_yaml')
        if isinstance(item, dict):
            for child in item.values():
                finite(child)
        elif isinstance(item, list):
            for child in item:
                finite(child)
    for node, section in value.items():
        if not isinstance(node, str) or not isinstance(section, dict):
            raise LocalizedError('invalid_node_section')
        if not isinstance(section.get('ros__parameters'), dict):
            raise LocalizedError('missing_parameters')
    finite(value)
    return value


class InputGate:
    """Latch commands off on faults; reconnect never automatically rearms."""

    def __init__(self):
        self.armed = False
        self.estopped = False
        self.keys = [0] * KEY_COUNT

    def clear(self):
        self.keys = [0] * KEY_COUNT

    def disarm(self):
        self.armed = False
        self.clear()

    def press(self, keys):
        self.clear()
        if self.armed and not self.estopped:
            for key in keys:
                if not 0 <= key < KEY_COUNT:
                    self.clear()
                    raise LocalizedError('invalid_key')
                self.keys[key] = 1

    def emergency_stop(self):
        self.disarm()
        self.estopped = True
        self.keys[KEY_ESTOP] = 1

    @staticmethod
    def command_allowed(keys, state):
        """Whitelist one intent using the confirmed backend mode, not widgets."""
        keys = list(keys)
        if not state or not keys or len(keys) != len(set(keys)):
            return False
        if any(type(key) is not int or not 0 <= key < KEY_COUNT for key in keys):
            return False
        if state.get('interaction_mode') not in ('normal', 'impedance'):
            return False
        if keys == [K.KEY_MODE_TOGGLE]:
            return True
        if state.get('control_mode') == 'joint':
            count = 7 if state.get('robot_model') == 'nero' else 6
            return (len(keys) == 2 and 0 <= keys[0] < count
                    and keys[1] in (K.KEY_DECREASE, K.KEY_INCREASE))
        if state.get('control_mode') == 'ik':
            return len(keys) == 1 and keys[0] in (
                K.KEY_DECREASE, K.KEY_INCREASE, K.KEY_FORWARD, K.KEY_BACKWARD,
                K.KEY_Z_UP, K.KEY_Z_DOWN, K.KEY_ARROW_UP, K.KEY_ARROW_DOWN,
                K.KEY_ARROW_LEFT, K.KEY_ARROW_RIGHT, K.KEY_ROLL_LEFT, K.KEY_ROLL_RIGHT)
        return False

    @staticmethod
    def permission(state, robot, graph_ok, feedback_fresh, conflict, pending,
                   text=translate):
        """Require controller presence and fresh measured feedback on hardware."""
        if conflict:
            return False, text('input_conflict')
        if not state or not graph_ok:
            return False, text('waiting_controller')
        if state['robot_model'] != robot:
            return False, text('robot_mismatch')
        if state['emergency_stopped']:
            return False, text('controller_estop')
        if state['interaction_transitioning'] or pending:
            return False, text('mode_pending')
        if state.get('interaction_fault_reason'):
            return False, str(state['interaction_fault_reason'])
        if not state['arm_ready']:
            return False, text('arm_not_ready')
        if state['execute_motion'] and not feedback_fresh:
            return False, text('feedback_stale')
        return True, (text('live') if state['execute_motion']
                      else text('dry_run'))
