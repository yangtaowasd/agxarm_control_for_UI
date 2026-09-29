"""Regress direct controls and repeated clicks without an enable checkbox."""
import json
import time
import pytest
from PyQt5 import QtCore
from std_msgs.msg import Int32MultiArray, String
from std_srvs.srv import Trigger
from rclpy.qos import QoSProfile, DurabilityPolicy
from test_gui_ros import console, pump
from test_model import state


def ready(console):
    _, backend, window = console
    received = []
    backend.create_subscription(Int32MultiArray, 'arm_keyboard_state',
                                lambda msg: received.append(list(msg.data)), 10)
    backend.create_service(Trigger, 'arm/set_normal_mode', lambda req, res: res)
    pub = backend.create_publisher(String, 'arm/interaction_state',
        QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
    pub.publish(String(data=json.dumps(state(execute_motion=False))))
    pump(window, backend, lambda: window.allowed)
    return backend, window, received


def test_direct_jog_needs_no_enable_checkbox(console):
    backend, window, received = ready(console)
    assert window.press([0, 8])
    pump(window, backend, lambda: any(msg[0] and msg[8] for msg in received))
    window.release()
    pump(window, backend, lambda: received[-1] == [0] * 25)
    assert not any(window.gate.keys)


def test_fast_second_click_does_not_lock_controls(console):
    backend, window, received = ready(console)
    window.press([0, 8])
    window.release()
    window.press([0, 8])  # Inside the falling-edge debounce interval.
    window.tick()
    assert window.joint_box.isEnabled()
    pump(window, backend, lambda: time.monotonic() >= window.neutral_until)
    assert window.press([0, 8])


@pytest.mark.parametrize('initial', ['normal', 'impedance', 'admittance'])
@pytest.mark.parametrize('target,expected,control', [
    ('joint_remote', 'normal', 'joint'),
    ('cartesian_control', 'normal', 'ik'),
    ('impedance', 'impedance', 'joint'),
    ('admittance', 'admittance', 'joint'),
])
def test_four_modes_confirm_backend_and_allow_next_action(console, initial, target, expected, control):
    _, backend, window = console
    snapshot = state(execute_motion=False, interaction_mode=initial)
    publisher = backend.create_publisher(String, 'arm/interaction_state',
        QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
    previous = [False]
    toggles = []

    def publish():
        publisher.publish(String(data=json.dumps(snapshot)))

    def keys(message):
        pressed = bool(message.data[11])
        if pressed and not previous[0]:
            snapshot['control_mode'] = 'ik' if snapshot['control_mode'] == 'joint' else 'joint'
            toggles.append(snapshot['control_mode'])
            publish()
        previous[0] = pressed

    backend.create_subscription(Int32MultiArray, 'arm_keyboard_state', keys, 10)
    for mode in ('normal', 'impedance', 'admittance'):
        def change(request, response, mode=mode):
            snapshot['interaction_mode'] = mode
            publish()
            response.success = True
            return response
        backend.create_service(Trigger, 'arm/set_' + mode + '_mode', change)
    publish()
    pump(window, backend, lambda: window.allowed)
    index = ['joint_remote', 'impedance', 'admittance', 'cartesian_control'].index(target)
    window.mode_buttons[index].click()
    pump(window, backend, lambda: window.allowed and window.desired_control is None
         and window.bridge.pending is None and window.toggle_waiting is None
         and window.bridge.state['interaction_mode'] == expected
         and window.bridge.state['control_mode'] == control)
    assert all(button.isEnabled() for button in window.mode_buttons)
    assert window.mode_buttons[index].isChecked()
    assert len(toggles) == (1 if control == 'ik' else 0)
    window.mode_buttons[index].click()  # Selecting the active mode is idempotent.
    pump(window, backend, lambda: window.allowed and window.desired_control is None
         and window.bridge.pending is None)
    assert len(toggles) == (1 if control == 'ik' else 0)
    # From Cartesian control, selecting joint remote must confirm the reverse toggle.
    if target == 'cartesian_control':
        window.mode_buttons[0].click()
        pump(window, backend, lambda: window.allowed and window.desired_control is None
             and window.bridge.state['control_mode'] == 'joint')
        assert toggles == ['ik', 'joint']


def test_focus_recovery_requires_fresh_press_not_checkbox(console):
    backend, window, received = ready(console)
    assert window.press([0, 8])
    window.focus_changed(QtCore.Qt.ApplicationInactive)
    assert not window.gate.armed and not any(window.gate.keys)
    assert not window.press([0, 8])
    window.focus_changed(QtCore.Qt.ApplicationActive)
    pump(window, backend, lambda: window.allowed and time.monotonic() >= window.neutral_until)
    assert not window.gate.armed
    assert window.press([0, 8])


def test_unconfirmed_toggle_times_out_and_stays_stopped(console):
    backend, window, received = ready(console)
    window.mode_request('cartesian_control')
    pump(window, backend, lambda: window.toggle_waiting is not None)
    window.mode_deadline = time.monotonic() - 1
    window.tick()
    assert window.mode_fault and not window.allowed
    assert not window.gate.armed and not any(window.gate.keys)
    assert not window.press([0, 8])
    assert window.estop.isEnabled()


def test_rejected_normal_mode_does_not_toggle_or_latch_controls(console):
    _, backend, window = console
    received = []
    backend.create_subscription(Int32MultiArray, 'arm_keyboard_state',
                                lambda msg: received.append(list(msg.data)), 10)
    def reject(request, response):
        response.success = False
        response.message = 'test mode rejected'
        return response
    backend.create_service(Trigger, 'arm/set_normal_mode', reject)
    pub = backend.create_publisher(String, 'arm/interaction_state',
        QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
    pub.publish(String(data=json.dumps(state(execute_motion=False, interaction_mode='impedance'))))
    pump(window, backend, lambda: window.allowed)
    window.mode_request('cartesian_control')
    pump(window, backend, lambda: window.bridge.pending is None and window.desired_control is None)
    assert window.allowed and not window.mode_fault
    assert not any(msg[11] for msg in received)
    assert 'test mode rejected' in window.log.toPlainText()
