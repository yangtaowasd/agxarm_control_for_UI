"""Offscreen GUI checks with real DDS and a hardware-free fake controller."""

import json
import os
import time
from argparse import Namespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PyQt5 import QtCore, QtWidgets as W
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from sensor_msgs.msg import JointState
from std_msgs.msg import Int32MultiArray, String
from std_srvs.srv import Trigger

from agxarm_control_gui.app import MainWindow
from test_model import state


@pytest.fixture
def console():
    app = W.QApplication.instance() or W.QApplication([])
    rclpy.init()
    backend = Node('fake_controller', namespace='/gui_test')
    window = MainWindow(Namespace(demo=False, robot_model='nero', namespace='/gui_test',
                                   keyboard_topic='arm_keyboard_state', config=''))
    window.timer.stop()
    yield app, backend, window
    window.close()
    backend.destroy_node()
    rclpy.try_shutdown()


def pump(window, backend, predicate, timeout=4):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        rclpy.spin_once(backend, timeout_sec=0.005)
        window.tick()
        if predicate():
            return
    raise AssertionError('ROS/GUI timeout: ' + window.status.text() + '\n' +
                         window.log.toPlainText() + '\nstate=' +
                         repr(window.bridge.state if window.bridge else None))


def test_latched_state_hold_release_service_and_estop(console):
    _, backend, window = console
    received = []
    backend.create_subscription(Int32MultiArray, 'arm_keyboard_state',
                                lambda msg: received.append(list(msg.data)), 10)
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    publisher = backend.create_publisher(String, 'arm/interaction_state', qos)
    snapshot = state(execute_motion=False)
    publisher.publish(String(data=json.dumps(snapshot)))

    def change_mode(request, response):
        snapshot['interaction_mode'] = 'impedance'
        publisher.publish(String(data=json.dumps(snapshot)))
        response.success = True
        response.message = 'test impedance accepted'
        return response

    backend.create_service(Trigger, 'arm/set_normal_mode', change_mode)
    backend.create_service(Trigger, 'arm/set_impedance_mode', change_mode)
    pump(window, backend, lambda: window.allowed)
    assert not received  # Connecting for monitoring must not publish zeros.
    window.press([6, 8])
    pump(window, backend, lambda: any(msg[6] and msg[8] for msg in received))
    window.release()
    pump(window, backend, lambda: received[-1] == [0] * 25)
    # Bypassing disabled widgets must not bypass the command-level mode gate.
    window.bridge.state['interaction_mode'] = 'admittance'
    window.allowed = True
    window.press([0, 8])
    assert not window.gate.armed and not any(window.gate.keys)
    window.bridge.state['interaction_mode'] = 'normal'
    window.tick()
    window.focus_changed(QtCore.Qt.ApplicationInactive)
    assert not window.gate.armed
    window.focus_changed(QtCore.Qt.ApplicationActive)
    window.mode_request('impedance')
    assert not window.gate.armed
    pump(window, backend, lambda: window.bridge.pending is None and
         window.bridge.state['interaction_mode'] == 'impedance')
    assert 'test impedance accepted' in window.log.toPlainText()
    window.neutral_until = 0
    window.pulse(11)
    assert window.toggle_waiting == 'joint'
    window.mode_request('joint_remote')
    assert window.bridge.pending is None
    window.press([0, 8])
    assert not window.gate.armed
    window.bridge.state['control_mode'] = 'ik'
    window.tick()
    assert window.toggle_waiting is None
    assert not window.gate.armed
    window.bridge.state['control_mode'] = 'joint'
    window.tick()
    # Feedback/mode changes between UI refresh and click are checked synchronously.
    window.bridge.state['emergency_stopped'] = True
    window.allowed = True
    window.press([0, 8])
    assert not window.gate.armed and not any(window.gate.keys)
    window.emergency_stop()
    pump(window, backend, lambda: any(msg[10] for msg in received))
    assert window.gate.estopped and not window.allowed


def test_conflicting_publisher_and_stale_feedback_disarm(console):
    _, backend, window = console
    backend.create_subscription(Int32MultiArray, 'arm_keyboard_state', lambda _: None, 10)
    backend.create_service(Trigger, 'arm/set_normal_mode', lambda req, res: res)
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    status = backend.create_publisher(String, 'arm/interaction_state', qos)
    feedback = backend.create_publisher(JointState, 'arm_dynamics_state', 10)
    status.publish(String(data=json.dumps(state())))
    sample = JointState(position=[0.] * 7, velocity=[0.] * 7, effort=[0.] * 7)
    feedback.publish(sample)
    pump(window, backend, lambda: window.allowed)
    window.neutral_until = 0
    assert window.press([0, 8])
    window.bridge.feedback_at = time.monotonic() - 1
    window.tick()
    assert not window.allowed and not window.gate.armed
    status.publish(String(data=json.dumps(state(execute_motion=False))))
    pump(window, backend, lambda: window.allowed)
    window.neutral_until = 0
    assert window.press([0, 8])
    competitor = backend.create_publisher(Int32MultiArray, 'arm_keyboard_state', 10)
    pump(window, backend, lambda: window.conflict)
    assert not window.gate.armed and not window.allowed
    backend.destroy_publisher(competitor)
    pump(window, backend, lambda: window.allowed)
    assert not window.gate.armed  # Recovery cannot restart a held command.


def test_preview_and_model_defaults():
    app = W.QApplication.instance() or W.QApplication([])
    window = MainWindow(Namespace(demo=True, robot_model='nero', namespace=None,
                                   keyboard_topic='arm_keyboard_state', config=''))
    window.show()
    app.processEvents()
    assert window.ns.text() == '/nero'
    assert window.config_path.endswith('/nero.yaml')
    assert not hasattr(window, 'arm')
    assert [button.text() for button in window.mode_buttons] == [
        '关节遥控', '阻抗控制', '导纳控制', '笛卡尔控制'
    ]
    assert len(window.mode_buttons) == 4
    assert not any(button.isEnabled() for button in window.mode_buttons)
    window.robot.setCurrentText('piper_l')
    assert window.config_path.endswith('/piper_l.yaml')
    assert window.ns.text() == '/piper_l'
    window.close()
