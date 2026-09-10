"""Qt operator console; all ROS and widget access runs on one event thread."""

import argparse
import math
from pathlib import Path
import shlex
import signal
import sys
import time

from ament_index_python.packages import get_package_share_directory
from PyQt5 import QtCore, QtGui, QtWidgets as W
import rclpy
from rclpy.utilities import remove_ros_args

from armbycontroller import teleop as K

from .bridge import RosBridge
from .model import InputGate, namespace, validate_config
from .i18n import LANGUAGES, LANGUAGE_NAMES, LocalizedError, translate


STYLE = '''
QMainWindow, QWidget { background: #0c121c; color: #e7edf5; font-size: 13px; }
QFrame#card { background: #131e2c; border: 1px solid #25364b; border-radius: 12px; }
QFrame#card QLabel { background: transparent; color: #a3b4c9; }
QLabel#brand { background: #163f42; color: #83ead5; border: 1px solid #28716b;
               border-radius: 14px; font-size: 22px; font-weight: bold; }
QLabel#title { font-size: 25px; font-weight: bold; color: #f2f6fc; }
QLabel#muted { color: #91a4ba; font-size: 12px; padding: 3px 0; }
QLabel#axis { color: #9bafc7; font-size: 13px; font-weight: bold; }
QLabel#jointValue { color: #91e0d4; font-size: 17px; padding: 0 12px; }
QGroupBox { background: #111c2a; border: 1px solid #25364b; border-radius: 12px;
            margin-top: 18px; padding: 16px 16px 12px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 16px; color: #78d5c7; }
QGroupBox QLabel { background: transparent; }
QPushButton { background: #1e3045; border: 1px solid #354c66;
              padding: 9px 15px; border-radius: 8px; font-weight: bold; }
QPushButton:hover { background: #29465a; border-color: #55b9aa; }
QPushButton:pressed { background: #1e6c61; border-color: #86e7d3; }
QPushButton:focus { border: 1px solid #87dccc; }
QPushButton:disabled { color: #7c8ca1; background: #172334; border-color: #26374b; }
QPushButton#estop { background: #8f293d; color: #fff4f5; border: 1px solid #d75e71;
                   font-size: 18px; min-height: 34px; }
QPushButton#estop:hover { background: #b0354c; }
QPushButton#estop:disabled { background: #522735; color: #b9969d; border-color: #6a3845; }
QLineEdit, QComboBox, QPlainTextEdit, QTableWidget {
    background: #101a27; border: 1px solid #2a3e55; border-radius: 6px; padding: 7px;
    selection-background-color: #285c70; }
QLineEdit:focus, QComboBox:focus { border-color: #64c7b5; }
QComboBox { min-height: 22px; padding-right: 22px; }
QComboBox#language { min-width: 104px; }
QComboBox QAbstractItemView { background: #172839; selection-background-color: #285c70; }
QTableWidget { gridline-color: #24364a; alternate-background-color: #142233; }
QHeaderView::section { background: #1b2c40; color: #a9bed5; padding: 10px; border: 0; }
QTabWidget::pane { border: 0; padding-top: 12px; }
QTabBar::tab { background: #121e2d; color: #98acc4; padding: 11px 30px;
                border-bottom: 2px solid #26394e; }
QTabBar::tab:selected { color: #93ead9; background: #193139; border-bottom: 2px solid #72dbc3; }
QTabBar::tab:hover { color: #d7f5ee; }
QCheckBox { padding: 8px 0; spacing: 10px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #62768e; border-radius: 4px; }
QCheckBox::indicator:checked { background: #66cfb7; border: 3px solid #286455; }
QCheckBox:disabled { color: #7d8da2; }
QLabel#status { padding: 12px 16px; background: #152537; border: 1px solid #2c4660;
                border-radius: 8px; color: #b4c8dd; }
QLabel#status[tone="ready"] { background: #14342f; color: #a1ecd9; border-color: #2e675a; }
QLabel#status[tone="live"] { background: #3a2d19; color: #f5d298; border-color: #806036; }
QLabel#status[tone="fault"] { background: #3d202d; color: #f1bac4; border-color: #7f3f50; }
QScrollBar:vertical { background: #101a27; width: 9px; }
QScrollBar::handle:vertical { background: #354c63; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
'''


class MainWindow(W.QMainWindow):
    """Display measured telemetry and send explicitly enabled operator intent."""

    def __init__(self, args):
        super().__init__()
        self.bridge = None
        self.language = getattr(args, 'language', 'zh')
        self.translatable = []
        self.gate = InputGate()
        self.demo = args.demo
        self.pulse_until = 0.0
        self.neutral_until = 0.0
        self.graph_ok = False
        self.conflict = False
        self.next_graph_poll = 0.0
        self.allowed = False
        self.input_context = None
        self.toggle_waiting = None
        self.config_path = ''
        self.config_model = args.robot_model
        self.setWindowTitle(self.text('window_title'))
        self.resize(1240, 900)
        self.setStyleSheet(STYLE)
        root = W.QWidget()
        self.setCentralWidget(root)
        layout = W.QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(16)
        header = W.QHBoxLayout()
        brand = W.QLabel('AGX')
        brand.setObjectName('brand')
        brand.setAlignment(QtCore.Qt.AlignCenter)
        brand.setFixedSize(68, 60)
        header.addWidget(brand)
        identity = W.QVBoxLayout()
        title = W.QLabel('ARM CONSOLE')
        title.setObjectName('title')
        identity.addWidget(title)
        subtitle = self.label('subtitle')
        subtitle.setObjectName('muted')
        identity.addWidget(subtitle)
        header.addLayout(identity, 1)
        header.addSpacing(24)
        self.language_selector = W.QComboBox()
        self.language_selector.setObjectName('language')
        for code, name in zip(LANGUAGES, LANGUAGE_NAMES):
            self.language_selector.addItem(name, code)
        self.language_selector.setCurrentIndex(LANGUAGES.index(self.language))
        self.language_selector.currentIndexChanged.connect(self.change_language)
        header.addWidget(W.QLabel('语言 / 言語 / Language'))
        header.addWidget(self.language_selector)
        layout.addLayout(header)
        connection = W.QHBoxLayout()
        self.robot = W.QComboBox()
        self.robot.addItems(['nero', 'piper_l'])
        self.robot.setCurrentText(args.robot_model)
        self.ns = W.QLineEdit(args.namespace if args.namespace is not None
                              else '/' + args.robot_model)
        self.topic = W.QLineEdit(args.keyboard_topic)
        self.connect_button = self.button('connect')
        self.connect_button.clicked.connect(self.connect_ros)
        self.disconnect_button = self.button('disconnect')
        self.disconnect_button.clicked.connect(self.disconnect_ros)
        self.disconnect_button.setEnabled(False)
        for label, widget in [('robot', self.robot), ('namespace', self.ns),
                              ('input_topic', self.topic)]:
            connection.addWidget(self.label(label))
            connection.addWidget(widget)
        connection.addWidget(self.connect_button)
        connection.addWidget(self.disconnect_button)
        connection.setContentsMargins(16, 12, 16, 12)
        connection_card = W.QFrame()
        connection_card.setObjectName('card')
        connection_card.setLayout(connection)
        layout.addWidget(connection_card)
        self.status = W.QLabel(self.text('disconnected'))
        self.status.setObjectName('status')
        layout.addWidget(self.status)
        tabs = self.tabs = W.QTabWidget()
        layout.addWidget(tabs, 1)
        control = W.QWidget()
        control_layout = W.QVBoxLayout(control)
        self.summary = W.QLabel()
        control_layout.addWidget(self.summary)
        self.arm = self.bind(W.QCheckBox(), 'enable_input')
        self.arm.toggled.connect(self.set_armed)
        control_layout.addWidget(self.arm)
        modes = W.QHBoxLayout()
        self.mode_buttons = []
        for mode, label in [('normal', 'normal'), ('impedance', 'impedance'),
                            ('admittance', 'admittance')]:
            button = self.button(label)
            button.clicked.connect(lambda checked=False, m=mode: self.mode_request(m))
            modes.addWidget(button)
            self.mode_buttons.append(button)
        self.toggle = self.button('toggle_control')
        self.toggle.clicked.connect(lambda: self.pulse(K.KEY_MODE_TOGGLE))
        modes.addWidget(self.toggle)
        control_layout.addLayout(modes)
        jogs = W.QHBoxLayout()
        self.joint_box = self.bind(W.QGroupBox(), 'joint_jog', 'setTitle')
        joint_layout = W.QGridLayout(self.joint_box)
        self.joint_widgets = []
        self.joint_values = []
        for index in range(7):
            label = W.QLabel(f'{index + 1:02d}   J{index + 1}')
            label.setObjectName('axis')
            measured = W.QLabel('— °')
            measured.setObjectName('jointValue')
            self.joint_values.append(measured)
            minus = self.hold_button('−', [index, K.KEY_DECREASE])
            plus = self.hold_button('+', [index, K.KEY_INCREASE])
            for col, widget in enumerate((label, measured, minus, plus)):
                joint_layout.addWidget(widget, index, col)
            self.joint_widgets.append((label, measured, minus, plus))
        jogs.addWidget(self.joint_box)
        self.cart_box = self.bind(W.QGroupBox(), 'cartesian_jog', 'setTitle')
        cart_layout = W.QGridLayout(self.cart_box)
        # Matches control_cycle.apply_cartesian_step and increment_tool_orientation.
        axes = [('X', K.KEY_BACKWARD, K.KEY_FORWARD),
                ('Y', K.KEY_INCREASE, K.KEY_DECREASE),
                ('Z', K.KEY_Z_DOWN, K.KEY_Z_UP),
                ('pitch', K.KEY_ARROW_UP, K.KEY_ARROW_DOWN),
                ('yaw', K.KEY_ARROW_RIGHT, K.KEY_ARROW_LEFT),
                ('roll', K.KEY_ROLL_RIGHT, K.KEY_ROLL_LEFT)]
        for row, (axis, minus, plus) in enumerate(axes):
            cart_layout.addWidget(self.label(axis), row, 0)
            cart_layout.addWidget(self.hold_button('−', [minus]), row, 1)
            cart_layout.addWidget(self.hold_button('+', [plus]), row, 2)
        jogs.addWidget(self.cart_box)
        control_layout.addLayout(jogs)
        notice = self.label('jog_notice')
        notice.setObjectName('muted')
        control_layout.addWidget(notice)
        self.estop = self.button('estop')
        self.estop.setObjectName('estop')
        self.estop.clicked.connect(self.emergency_stop)

        control_scroll = W.QScrollArea()
        control_scroll.setWidgetResizable(True)
        control_scroll.setFrameShape(W.QFrame.NoFrame)
        control_scroll.setWidget(control)
        tabs.addTab(control_scroll, self.text('control_tab'))

        telemetry = W.QWidget()
        tele_layout = W.QVBoxLayout(telemetry)
        self.feedback_status = W.QLabel(self.text('waiting_feedback'))
        tele_layout.addWidget(self.feedback_status)
        self.table = W.QTableWidget(7, 6)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(W.QHeaderView.Stretch)
        self.table.setEditTriggers(W.QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().hide()
        tele_layout.addWidget(self.table)
        self.state_text = W.QPlainTextEdit()
        self.state_text.setReadOnly(True)
        self.state_text.setMaximumHeight(220)
        tele_layout.addWidget(self.state_text)
        tabs.addTab(telemetry, self.text('telemetry_tab'))

        config = W.QWidget()
        config_layout = W.QVBoxLayout(config)
        config_layout.addWidget(self.label('config_notice'))
        config_buttons = W.QHBoxLayout()
        for label, callback in [('robot_defaults', self.load_defaults),
                                ('open_yaml', self.open_config),
                                ('validate', self.check_config),
                                ('save_as', self.save_config)]:
            button = self.button(label)
            button.clicked.connect(callback)
            config_buttons.addWidget(button)
        config_layout.addLayout(config_buttons)
        self.config_label = W.QLabel()
        config_layout.addWidget(self.config_label)
        self.editor = W.QPlainTextEdit()
        self.editor.setFont(QtGui.QFont('monospace', 11))
        self.editor.textChanged.connect(self.config_changed)
        config_layout.addWidget(self.editor, 1)
        config_layout.addWidget(self.label('launch_command'))
        self.command = W.QLineEdit()
        self.command.setReadOnly(True)
        config_layout.addWidget(self.command)
        tabs.addTab(config, self.text('config_tab'))

        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(400)
        self.log.setMaximumHeight(75)
        layout.addWidget(self.estop)
        layout.addWidget(self.label('event_log'))
        layout.addWidget(self.log)
        self.robot.currentTextChanged.connect(self.model_changed)
        self.ns.textChanged.connect(self.update_command)
        self.topic.textChanged.connect(self.update_command)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(50)  # 20 Hz input heartbeat, below controller timeout 0.3 s.
        self.render_at = 0.0
        W.QApplication.instance().applicationStateChanged.connect(self.focus_changed)
        if args.config:
            self.load_config(args.config)
        else:
            self.load_defaults()
        self.update_command()
        if self.demo:
            self.connect_button.setEnabled(False)
            self.status.setText(self.text('demo'))
        else:
            self.connect_ros()
        self.retranslate()
        self.tick()

    def text(self, key, **values):
        return translate(key, self.language, **values)

    def error_text(self, error):
        return error.localized(self.text) if isinstance(error, LocalizedError) else str(error)

    def bind(self, widget, key, method='setText'):
        setter = getattr(widget, method)
        self.translatable.append((setter, key))
        setter(self.text(key))
        return widget

    def label(self, key):
        widget = self.bind(W.QLabel(), key)
        widget.setWordWrap(True)
        return widget

    def button(self, key):
        return self.bind(W.QPushButton(), key)

    def retranslate(self):
        self.setWindowTitle(self.text('window_title'))
        for setter, key in self.translatable:
            setter(self.text(key))
        for index, key in enumerate(('control_tab', 'telemetry_tab', 'config_tab')):
            self.tabs.setTabText(index, self.text(key))
        self.table.setHorizontalHeaderLabels([self.text(key) for key in (
            'joint', 'position_rad', 'position_deg', 'velocity', 'torque', 'external_torque')])
        self.config_changed()
        self.render_at = 0.0

    def change_language(self):
        # A language change never leaves a held jog active.
        self.arm.setChecked(False)
        self.language = self.language_selector.currentData()
        self.retranslate()
        self.tick()

    def choose_config_file(self, save=False):
        """Translate the app-owned dialog labels independently of OS locale."""
        dialog = W.QFileDialog(self)
        dialog.setOption(W.QFileDialog.DontUseNativeDialog, True)
        dialog.setOption(W.QFileDialog.DontConfirmOverwrite, True)
        dialog.setWindowTitle(self.text('save_as' if save else 'open_yaml'))
        dialog.setNameFilter('YAML (*.yaml *.yml)')
        dialog.setAcceptMode(W.QFileDialog.AcceptSave if save else W.QFileDialog.AcceptOpen)
        dialog.setFileMode(W.QFileDialog.AnyFile if save else W.QFileDialog.ExistingFile)
        dialog.setDefaultSuffix('yaml')
        if save:
            dialog.selectFile(str(Path.home() / (self.robot.currentText() + '_gui.yaml')))
        for label, key in ((W.QFileDialog.LookIn, 'file_location'),
                           (W.QFileDialog.FileName, 'file_name'),
                           (W.QFileDialog.FileType, 'file_type'),
                           (W.QFileDialog.Accept, 'save' if save else 'open'),
                           (W.QFileDialog.Reject, 'cancel')):
            dialog.setLabelText(label, self.text(key))
        if dialog.exec_() != W.QDialog.Accepted:
            return ''
        path = dialog.selectedFiles()[0]
        if save and Path(path).exists():
            confirm = W.QMessageBox(self)
            confirm.setWindowTitle(self.text('save_as'))
            confirm.setText(self.text('overwrite', path=path))
            overwrite = confirm.addButton(self.text('save'), W.QMessageBox.AcceptRole)
            cancel = confirm.addButton(self.text('cancel'), W.QMessageBox.RejectRole)
            confirm.setDefaultButton(cancel)
            confirm.exec_()
            if confirm.clickedButton() != overwrite:
                return ''
        return path

    def write_log(self, text):
        self.log.appendPlainText(time.strftime('%H:%M:%S') + '  ' + str(text))

    def hold_button(self, label, keys):
        button = W.QPushButton(label)
        button.setAutoRepeat(False)
        button.pressed.connect(lambda: self.press(keys))
        button.released.connect(self.release)
        return button

    def connect_ros(self):
        if self.bridge is not None:
            return
        try:
            self.bridge = RosBridge(namespace(self.ns.text()), self.topic.text().strip(),
                                    self.write_log, self.text)
        except Exception as error:
            self.write_log(self.text('connect_failed', detail=self.error_text(error)))
            return
        self.gate = InputGate()
        self.graph_ok = False
        self.toggle_waiting = None
        self.pulse_until = 0.0
        self.input_context = None
        self.next_graph_poll = 0.0
        for widget in (self.robot, self.ns, self.topic, self.connect_button):
            widget.setEnabled(False)
        self.disconnect_button.setEnabled(True)
        self.write_log(self.text('connected'))

    def disconnect_ros(self):
        self.arm.setChecked(False)
        self.gate.disarm()
        if self.bridge is not None:
            self.bridge.destroy_node()
            self.bridge = None
        self.graph_ok = False
        for widget in (self.robot, self.ns, self.topic, self.connect_button):
            widget.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.write_log(self.text('disconnected'))

    def set_armed(self, checked):
        if checked and self.command_ready() and not self.gate.estopped:
            self.gate.armed = True
            self.input_context = self.context_signature()
            self.write_log(self.text('input_enabled'))
        else:
            was_armed = self.gate.armed
            self.gate.disarm()
            if was_armed and self.bridge and not self.conflict:
                self.bridge.send(self.gate.keys)
            if checked:
                self.arm.setChecked(False)

    def press(self, keys):
        if (self.gate.armed and self.command_ready()
                and self.input_context == self.context_signature()
                and InputGate.command_allowed(keys, self.bridge.state)
                and time.monotonic() >= self.neutral_until):
            self.gate.press(keys)
            if self.bridge and self.gate.armed:
                self.bridge.send(self.gate.keys)
            return True
        self.arm.setChecked(False)
        self.gate.disarm()
        return False

    def context_signature(self):
        state = self.bridge.state if self.bridge else None
        return tuple(state.get(key) for key in (
            'robot_model', 'execute_motion', 'interaction_mode', 'control_mode')) if state else None

    def command_ready(self):
        """Recheck transport and feedback at each command entry, without cached UI flags."""
        if not self.bridge or not rclpy.ok() or self.gate.estopped or self.toggle_waiting:
            return False
        bridge = self.bridge
        conflict = bridge.count_publishers(bridge.keyboard.topic_name) != 1
        graph = (bridge.count_publishers(bridge.state_topic) == 1
                 and bridge.count_subscribers(bridge.keyboard.topic_name) == 1
                 and bridge.mode_clients['normal'].service_is_ready())
        return InputGate.permission(
            bridge.state, self.robot.currentText(), graph,
            self.valid_feedback(time.monotonic()), conflict,
            bridge.pending is not None, self.text)[0]

    def release(self):
        self.gate.clear()
        self.pulse_until = 0.0
        # Give the backend several control ticks to observe the falling edge.
        self.neutral_until = time.monotonic() + 0.1
        if self.bridge and self.gate.armed and not self.conflict:
            self.bridge.send(self.gate.keys)

    def pulse(self, key):
        if key != K.KEY_MODE_TOGGLE or not self.press([key]):
            return
        self.pulse_until = time.monotonic() + 0.15
        self.toggle_waiting = self.bridge.state['control_mode']

    def emergency_stop(self):
        if not self.bridge:
            return
        self.arm.setChecked(False)
        self.gate.emergency_stop()
        self.bridge.send(self.gate.keys)
        self.pulse_until = time.monotonic() + 0.2
        self.write_log(self.text('estop_sent'))

    def mode_request(self, mode):
        if (mode in ('normal', 'impedance', 'admittance')
                and self.gate.armed and self.command_ready()
                and self.input_context == self.context_signature()):
            self.release()
            self.bridge.request_mode(mode)
            self.arm.setChecked(False)

    def focus_changed(self, state):
        if state != QtCore.Qt.ApplicationActive:
            self.arm.setChecked(False)

    def tick(self):
        now = time.monotonic()
        state = None
        reason = self.text('disconnected')
        self.allowed = False
        if self.bridge:
            if not rclpy.ok():
                self.disconnect_ros()
                return
            # Never wait for a service or DDS message in the UI event loop.
            for _ in range(4):
                rclpy.spin_once(self.bridge, timeout_sec=0)
            self.bridge.poll_request()
            state = self.bridge.state
            if self.toggle_waiting and state and state['control_mode'] != self.toggle_waiting:
                self.toggle_waiting = None
                self.release()
                self.arm.setChecked(False)
            if self.gate.armed and self.input_context != self.context_signature():
                self.arm.setChecked(False)
            if now >= self.next_graph_poll:
                self.graph_ok = (
                    self.bridge.count_publishers(self.bridge.state_topic) == 1
                    and self.bridge.count_subscribers(self.bridge.keyboard.topic_name) == 1
                    and self.bridge.mode_clients['normal'].service_is_ready())
                self.conflict = self.bridge.count_publishers(self.bridge.keyboard.topic_name) > 1
                self.next_graph_poll = now + 0.25
            self.allowed, reason = InputGate.permission(
                state, self.robot.currentText(), self.graph_ok,
                self.valid_feedback(now), self.conflict, self.bridge.pending is not None, self.text)
            if self.gate.estopped:
                self.allowed = False
                reason = self.text('local_estop')
            if not self.allowed and self.gate.armed:
                self.arm.setChecked(False)
            if self.pulse_until and now >= self.pulse_until:
                self.release()
                if self.toggle_waiting:
                    self.arm.setChecked(False)
            if self.toggle_waiting:
                self.allowed = False
                reason = self.text('mode_pending')
            if self.gate.armed and not self.toggle_waiting and not self.command_ready():
                self.arm.setChecked(False)
            if self.gate.armed or (self.pulse_until and self.gate.estopped):
                self.bridge.send(self.gate.keys)
        if self.demo:
            reason = self.text('demo')
        self.status.setText(reason)
        tone = ('fault' if self.gate.estopped or (state and state['emergency_stopped'])
                else 'live' if self.allowed and state and state['execute_motion']
                else 'ready' if self.allowed else 'idle')
        if self.status.property('tone') != tone:
            self.status.setProperty('tone', tone)
            self.status.style().unpolish(self.status)
            self.status.style().polish(self.status)
        self.arm.setEnabled(self.allowed and not self.demo)
        enabled = self.gate.armed and self.allowed
        for button in self.mode_buttons:
            button.setEnabled(enabled)
        active = state.get('interaction_mode') if state else None
        control = state.get('control_mode') if state else None
        jog_allowed = enabled and active in ('normal', 'impedance')
        self.toggle.setEnabled(jog_allowed and not self.pulse_until)
        self.joint_box.setEnabled(jog_allowed and control == 'joint')
        self.cart_box.setEnabled(jog_allowed and control == 'ik')
        self.estop.setEnabled(self.bridge is not None)
        self.summary.setText(self.text('summary', mode=self.text(active or '—'),
                                       control=self.text(control or '—')))
        for widgets in self.joint_widgets[-1:]:
            for widget in widgets:
                widget.setVisible(self.robot.currentText() == 'nero')
        if now >= self.render_at:
            self.render_telemetry(now, state)
            self.render_at = now + 0.2

    def valid_feedback(self, now):
        if not self.bridge or now - self.bridge.feedback_at > 0.5:
            return False
        msg = self.bridge.feedback
        count = 7 if self.robot.currentText() == 'nero' else 6
        return msg is not None and all(
            len(values) == count and all(math.isfinite(v) for v in values)
            for values in (msg.position, msg.velocity, msg.effort))

    def render_telemetry(self, now, state):
        import json
        count = 7 if self.robot.currentText() == 'nero' else 6
        self.table.setRowCount(count)
        fresh = self.valid_feedback(now)
        self.feedback_status.setText(
            self.text('demo_feedback') if self.demo else
            (self.text('measured_feedback') if fresh else self.text('no_feedback')))
        msg = self.bridge.feedback if self.bridge and fresh else None
        ext = (self.bridge.external if self.bridge and
               now - self.bridge.external_at <= 0.5 else None)
        for row in range(count):
            q = math.sin(now * 0.3 + row) * 0.2 if self.demo else None
            if msg is not None:
                q = msg.position[row]
            external = None
            if ext is not None and msg is not None:
                # Observer order may differ; join on the reported joint name.
                name = msg.name[row] if row < len(msg.name) else ''
                if name and name in ext.name:
                    index = list(ext.name).index(name)
                    if index < len(ext.effort):
                        external = ext.effort[index]
            self.joint_values[row].setText(f'{math.degrees(q):.2f} °' if q is not None else '— °')
            values = ['J' + str(row + 1), q,
                      math.degrees(q) if q is not None else None,
                      msg.velocity[row] if msg else None,
                      msg.effort[row] if msg else None, external]
            for col, value in enumerate(values):
                text = (value if isinstance(value, str) else
                        f'{value:.4f}' if value is not None and math.isfinite(value) else '—')
                self.table.setItem(row, col, W.QTableWidgetItem(text))
        self.state_text.setPlainText(json.dumps(state or {}, indent=2, ensure_ascii=False))

    def model_changed(self):
        self.ns.setText('/' + self.robot.currentText())
        if not self.editor.document().isModified():
            self.load_defaults()
        else:
            self.write_log(self.text('unsaved_retained'))
        self.update_command()

    def load_defaults(self):
        try:
            share = Path(get_package_share_directory('agxarm_control_by_gamecontroller'))
            self.load_config(share / 'config' / (self.robot.currentText() + '.yaml'))
        except Exception as error:
            self.write_log(str(error))

    def load_config(self, path):
        try:
            text = Path(path).read_text(encoding='utf-8')
            validate_config(text)
            self.editor.setPlainText(text)
            self.config_path = str(Path(path).resolve())
            self.config_model = self.robot.currentText()
            self.editor.document().setModified(False)
            self.config_changed()
        except Exception as error:
            self.write_log(self.text('config_failed', detail=self.error_text(error)))

    def open_config(self):
        path = self.choose_config_file(save=False)
        if path:
            self.load_config(path)

    def check_config(self):
        try:
            validate_config(self.editor.toPlainText())
            self.write_log(self.text('yaml_valid'))
            return True
        except Exception as error:
            self.write_log(self.text('yaml_invalid', detail=self.error_text(error)))
            return False

    def save_config(self):
        if not self.check_config():
            return
        path = self.choose_config_file(save=True)
        if path:
            try:
                Path(path).write_text(self.editor.toPlainText(), encoding='utf-8')
                self.config_path = str(Path(path).resolve())
                self.config_model = self.robot.currentText()
                self.editor.document().setModified(False)
                self.config_changed()
                self.write_log(self.text('saved'))
            except OSError as error:
                self.write_log(str(error))

    def config_changed(self):
        dirty = self.editor.document().isModified()
        self.config_label.setText((self.config_path or '—') + ('  * ' + self.text('unsaved') if dirty else ''))
        self.update_command()

    def update_command(self):
        if not hasattr(self, 'command'):
            return
        argv = ['ros2', 'launch', 'agxarm_control_gui', 'gui.launch.py',
                'start_controller:=true', 'execute_motion:=false',
                'language:=' + self.language,
                'robot_model:=' + self.robot.currentText(),
                'arm_namespace:=' + self.ns.text(),
                'keyboard_topic:=' + self.topic.text()]
        if self.config_path and self.config_model == self.robot.currentText():
            argv.append('controller_config:=' + self.config_path)
        self.command.setText(shlex.join(argv))

    def closeEvent(self, event):
        self.timer.stop()
        self.disconnect_ros()
        event.accept()


def main(args=None):
    """Start the GUI; --demo previews widgets without creating a ROS node."""
    argv = sys.argv if args is None else ['agxarm_control_gui', *args]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--robot-model', choices=['nero', 'piper_l'], default='nero')
    parser.add_argument('--namespace', default=None)
    parser.add_argument('--keyboard-topic', default='arm_keyboard_state')
    parser.add_argument('--config', default='')
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--language', choices=LANGUAGES, default='zh')
    options = parser.parse_args(remove_ros_args(argv)[1:])
    app = W.QApplication([argv[0]])
    if not options.demo:
        rclpy.init(args=argv)
    window = MainWindow(options)
    window.show()
    signal.signal(signal.SIGINT, lambda *_: window.close())
    signal.signal(signal.SIGTERM, lambda *_: window.close())
    try:
        app.exec_()
    finally:
        if window.bridge is not None:
            window.disconnect_ros()
        if not options.demo:
            rclpy.try_shutdown()


if __name__ == '__main__':
    main()
