"""Nonblocking ROS transport, serviced on the Qt event thread."""

import time

from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
from rclpy.validate_topic_name import validate_topic_name
from sensor_msgs.msg import JointState
from std_msgs.msg import Int32MultiArray, String
from std_srvs.srv import Trigger

from .model import namespace, parse_state
from .i18n import LocalizedError, translate


class RosBridge(Node):
    """Own subscriptions and one optional operator input publisher."""

    def __init__(self, arm_namespace, keyboard_topic, log, text=translate):
        validate_topic_name(keyboard_topic)
        super().__init__('agxarm_control_gui', namespace=namespace(arm_namespace))
        self.log = log
        self.text = text
        self.state = None
        self.feedback = None
        self.feedback_at = float('-inf')
        self.external = None
        self.external_at = float('-inf')
        self.pending = None
        self.pending_at = None
        self.timeout_reported = False
        try:
            self._create_transport(keyboard_topic)
        except Exception:
            self.destroy_node()
            raise

    def _create_transport(self, keyboard_topic):
        self.keyboard = self.create_publisher(Int32MultiArray, keyboard_topic, 10)
        self.state_topic = 'arm/interaction_state'
        state_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(String, self.state_topic, self._state, state_qos)
        self.create_subscription(JointState, 'arm_dynamics_state',
                                 self._feedback, qos_profile_sensor_data)
        self.create_subscription(JointState, 'arm_external_joint_torque',
                                 self._external, qos_profile_sensor_data)
        self.create_subscription(String, 'arm_control_event',
                                 lambda msg: self.log(msg.data), 20)
        self.mode_clients = {
            mode: self.create_client(Trigger, 'arm/set_' + mode + '_mode')
            for mode in ('normal', 'impedance', 'admittance')}

    def _state(self, message):
        try:
            self.state = parse_state(message.data)
        except (ValueError, TypeError) as error:
            self.state = None
            detail = error.localized(self.text) if isinstance(error, LocalizedError) else str(error)
            self.log(self.text('invalid_state', detail=detail))

    def _feedback(self, message):
        self.feedback = message
        self.feedback_at = time.monotonic()

    def _external(self, message):
        self.external = message
        self.external_at = time.monotonic()

    def send(self, keys):
        self.keyboard.publish(Int32MultiArray(data=list(keys)))

    def request_mode(self, mode):
        if self.pending is not None:
            return
        client = self.mode_clients[mode]
        if not client.service_is_ready():
            self.log(self.text('service_unavailable', mode=self.text(mode)))
            return
        self.pending = client.call_async(Trigger.Request())
        self.pending_at = time.monotonic()
        self.timeout_reported = False
        self.log(self.text('request_mode', mode=self.text(mode)))

    def poll_request(self):
        if self.pending is None:
            return
        if self.pending.done():
            try:
                result = self.pending.result()
                self.log(self.text('service_success' if result.success else 'service_failed',
                                   detail=result.message))
            except Exception as error:
                self.log(self.text('service_error', detail=str(error)))
            self.pending = None
        elif time.monotonic() - self.pending_at > 8 and not self.timeout_reported:
            self.timeout_reported = True
            self.log(self.text('service_timeout'))
