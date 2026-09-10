# 项目学习指南 / Project Study Guide

## 1. 目标 / Goal

为 `agxarm_control_by_gamecontroller` 提供独立桌面操作包，默认 Nero，同时支持 Piper-L。
GUI 负责操作意图和状态呈现，原控制器继续负责运动学、控制律、限幅和 CAN。

Provide an independent desktop package for the existing controller, defaulting to
Nero with Piper-L support. The GUI owns operator intent and presentation; the
controller owns kinematics, control laws, limits and CAN.

## 2. 心智模型与架构 / Mental model and architecture

把 GUI 看作“可视化键盘 + 状态仪表”。它不产生电机力矩，不重写控制算法。
Qt 主线程通过 50 ms 定时器非阻塞处理 ROS 回调，因此 ROS 回调和控件没有跨线程访问。
模式切换使用异步 Trigger 服务，成功与否由控制器响应和状态话题决定。

Think of the GUI as a visible keyboard plus instruments. It does not compute motor
torques or duplicate control algorithms. A 50 ms Qt timer services nonblocking ROS
callbacks on the widget thread. Trigger requests are asynchronous; controller
responses and state snapshots determine the actual mode.

```text
Qt press/release -> InputGate -> Int32MultiArray (25 keys)
                             -> arm_keyboard_controller -> SDK -> CAN -> arm
Qt mode request -> Trigger service -> existing mode lifecycle
arm -> controller -> JointState + state JSON + events -> Qt table/log
arm_dynamics_state -> momentum observer -> external torque -> Qt table
YAML editor -> saved file -> next launch -> controller/observer parameters
```

## 3. 数据流与接口 / Data flow and interfaces

下列名称均相对于所选命名空间，默认 `/nero`。
The following names are relative to the selected namespace, default `/nero`.

| 名称 / Name | 类型 / Type | 方向 / Direction |
| --- | --- | --- |
| `arm_keyboard_state` | `std_msgs/Int32MultiArray` | GUI → controller |
| `arm/interaction_state` | `std_msgs/String`, schema v1 JSON | Controller → GUI |
| `arm_dynamics_state` | `sensor_msgs/JointState` | Measured state → GUI |
| `arm_external_joint_torque` | `sensor_msgs/JointState`, effort | Observer → GUI |
| `arm_control_event` | `std_msgs/String`, JSON | Events → GUI |
| `arm/set_normal_mode` | `std_srvs/Trigger` | GUI request |
| `arm/set_impedance_mode` | `std_srvs/Trigger` | GUI request |
| `arm/set_admittance_mode` | `std_srvs/Trigger` | GUI request |

状态订阅使用 reliable + transient-local depth 1，兼容控制器锁存状态；该话题是事件快照，
不是周期心跳。连接判断使用 DDS 图和服务可用性，实机操作还要求完整且有限的 q/dq/τ
反馈在本机单调时钟的 0.5 s 内到达。不会拿两个进程的单调时间戳相减。

The state subscription uses reliable/transient-local depth 1 for the latched
snapshot. It is not a heartbeat. Connection detection uses the DDS graph and service
availability. Hardware input additionally requires complete finite q/dq/τ received
within 0.5 s on the GUI's local monotonic clock. Monotonic timestamps from different
processes are not subtracted.

## 4. 核心原理与公式 / Core principles and equations

GUI 复用控制包的 25 键常量，避免协议漂移。按住按钮连续发送当前键状态，松开清零。
关节编号和增减键在同一个消息发送，控制器先选关节，再更新目标。

The GUI imports the controller's 25-key constants. Held buttons publish key state;
release sends zeros. Joint selection and direction share one message; the backend
selects the joint before updating its target.

```text
q_target[k+1] = clamp(q_target[k] + direction × step_rad, q_min, q_max)
q_degrees = q_radians × 180 / π
nominal jog target speed = step_rad × control_rate
                        = 0.005 rad × 100 Hz = 0.5 rad/s
```

20 Hz GUI 心跳不是关节点动速度；控制器在自己的 100 Hz 循环消费保持键值，实际运动
还受控制器轨迹、速度和安全限幅约束。笛卡尔 X/Y/Z 是控制器基座平移方向；
Pitch/Yaw/Roll 的姿态增量直接沿用控制器 `increment_tool_orientation` 定义。

The 20 Hz GUI heartbeat is not the jog speed. The backend consumes held keys at
100 Hz; trajectory and safety limits still bound motion. Cartesian X/Y/Z follow
the controller's base translation directions. Pitch/yaw/roll increments follow
the existing `increment_tool_orientation` convention.

跨交互模式切换由原控制器执行 `当前 → normal → 目标`。GUI 不推测成功状态，模式服务
8 s 无响应时显示结果未知并保持操作锁定；不自动重试可能已经执行的命令。

Cross-mode requests follow the backend's `current → normal → target` transition.
The GUI does not assume success. After 8 s without a service result it reports an
unknown outcome and keeps input locked, without automatically retrying.

## 5. 模块地图 / Module map

| 文件 / File | 职责 / Responsibility |
| --- | --- |
| `agxarm_control_gui/app.py` | Qt layout, hold/release, focus gate, telemetry, YAML editor |
| `agxarm_control_gui/model.py` | Input gate, state schema, namespace/YAML validation |
| `agxarm_control_gui/bridge.py` | ROS publishers, subscriptions, asynchronous clients |
| `launch/gui.launch.py` | GUI-only or GUI + controller + observer launch |
| `setup.py`, `setup.cfg`, `package.xml` | ament_python packaging and dependencies |
| `test/test_model.py` | Protocol compatibility and gate/config tests |
| `test/test_gui_ros.py` | Offscreen Qt and real DDS with a fake controller |

## 6. 参数、单位和默认值 / Parameters, units and defaults

| 参数 / Setting | 默认 / Default | 含义 / Meaning |
| --- | --- | --- |
| `robot_model` / `--robot-model` | `nero` | `nero` or `piper_l` |
| `arm_namespace` / `--namespace` | model name, `/nero` | ROS namespace |
| `keyboard_topic` / `--keyboard-topic` | `arm_keyboard_state` | Relative or absolute input topic |
| `start_controller` | `false` | Launch existing controller and observer when true |
| `execute_motion` | `false` | Applies to newly launched controller; true enables hardware |
| `can_interface` | `can0` | Used only by newly launched controller |
| `controller_config` / `--config` | installed `config/nero.yaml` | Model parameter file |
| `common_config` | installed `config/common.yaml` | Shared parameters |
| GUI input timer | 50 ms / 20 Hz | Fixed heartbeat |
| GUI telemetry rendering | 200 ms / 5 Hz | Table refresh |
| GUI graph check | 250 ms | Publisher/service discovery check |
| GUI feedback age limit | 0.5 s | Receipt age; does not replace backend watchdog |
| Backend `keyboard_timeout` | 0.3 s | Clears stale keys |
| Backend `step_rad` | 0.005 rad | Joint target increment per control tick |
| Backend `control_rate` | 100 Hz | Configured in common YAML |
| Backend `interaction_feedback_timeout` | 0.10 s | SDK timestamp watchdog |
| GUI command enable | off | Explicitly enable after connection/mode request |

其余阻抗/导纳增益、力矩限幅和速度限幅直接来自控制包 YAML，不在 GUI 中复制默认值。
`execute_motion:=false` 不能改变已运行控制器的实机状态，GUI 以接收到的状态为准。

Other gains and torque/velocity limits come directly from controller YAML; this
package does not duplicate them. `execute_motion:=false` cannot change an already
running controller. The GUI displays the received hardware/dry-run state.

## 7. 安全边界与已知风险 / Safety boundaries and known risks

- 未勾选使能时不发送周期键状态；多发布者冲突时取消使能。DDS 发现存在延迟，这不是
  排他控制锁；必须保证同一控制器只有一个实际输入源。
  Monitoring emits no periodic keys. Publisher conflicts disarm, but discovery is
  delayed and is not an ownership lock. Use one operator input source.
- 松手、失焦、反馈过期、模式请求会清除输入或取消使能，恢复不会自动重发之前命令。
  Release, focus loss, stale feedback and mode requests clear/disarm input. Recovery
  never replays the previous command automatically.
- 清零键值只停止累积点动目标，不撤销已规划运动、不退出阻抗/导纳，也不禁用电机。
  Zero keys stop target increments; they do not cancel planned motion, exit compliant
  modes or disable motors.
- 软件急停无需 GUI 使能或新鲜反馈，但依赖 ROS 传输和控制器循环。急停后本地锁定；
  按原项目流程恢复控制器后重连 GUI。不能通过重连绕过控制器的急停状态。
  Software E-stop bypasses GUI arming/freshness but depends on ROS and the backend
  loop. Restore the backend by its existing procedure, then reconnect; a controller
  E-stop remains authoritative.
- 状态事件不等于实时心跳；空运行没有实测反馈。GUI 预览明确标记合成数据。
  Event snapshots are not heartbeats. Dry run has no measured feedback; preview data
  is explicitly synthetic.
- YAML 校验仅包含结构与非有限数值检查；加载/保存不执行在线参数修改。关闭窗口
  不停止控制器；launch 保持原控制包的 `disable_arm_on_shutdown=false` 行为。
  YAML validation is structural and checks nonfinite values; loading/saving does not
  set live parameters. Closing the window does not stop the controller. Launch retains
  the backend's `disable_arm_on_shutdown=false` behavior.

## 8. 构建、测试、运行 / Build, test and run

完整命令见 [README](README.md)。最短流程 / Minimal sequence:

```bash
cd /home/yang/demo_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to agxarm_control_gui
source install/setup.bash
ros2 launch agxarm_control_gui gui.launch.py start_controller:=true
```

先运行 `ros2 run agxarm_control_gui gui --demo` 检查桌面依赖；再用空运行验证协议。
测试使用伪控制器和 DDS，不访问 CAN。通过软件测试不意味着实机控制稳定性已验证。

Use `--demo` to inspect desktop dependencies, then dry run to verify the protocol.
Tests use a fake controller and DDS without CAN. Passing software tests does not
establish physical control stability.

## 9. 诊断 / Diagnostics

| 症状 / Symptom | 检查 / Check |
| --- | --- |
| Waiting for controller | Namespace, sourced workspace, ROS_DOMAIN_ID, controller process |
| Another input publisher | `ros2 topic info /nero/arm_keyboard_state --verbose`; stop other keyboard readers |
| Hardware feedback stale | `ros2 topic hz /nero/arm_dynamics_state`; inspect backend CAN/SDK logs |
| Service unavailable/timeout | `ros2 service list`; inspect backend errors and actual interaction state |
| Missing Qt/ament imports | Use `/usr/bin/python3`, source ROS/workspace, install declared dependencies |
| No display | Run on desktop; use `QT_QPA_PLATFORM=offscreen` for tests only |
| Edited YAML not active | Save a file, use generated launch command, restart controller |
| Wrong robot defaults | Disconnect GUI, select correct model, load model defaults |

## 10. 学习路径与练习 / Learning path and exercises

1. 阅读原控制包的 `teleop/keyboard.py`，解释为什么 20 Hz 心跳不代表 20 次点动。
   Read the keyboard protocol and explain why a 20 Hz heartbeat is not 20 jog steps.
2. 用 `--demo` 查看三个页签，再启动空运行观察普通/阻抗服务响应。
   Explore the three tabs in demo, then inspect normal/impedance responses in dry run.
3. 阅读输入门控测试，增加一个错误型号或非有限反馈测试。
   Read the gate tests; add a wrong-model or nonfinite-feedback case.
4. 在伪控制器环境加入第二个输入发布者，观察取消使能及恢复后不自动启用。
   Add a competing publisher to a fake-controller run and observe disarming/no auto-rearm.
5. 复制 YAML 修改一个增益，另存为并查看启动命令，解释为何实机参数没有立即改变。
   Edit a copied gain, save it and inspect the launch command; explain why live parameters stay unchanged.

## 11. 术语 / Glossary

| 术语 / Term | 解释 / Meaning |
| --- | --- |
| Jog / 点动 | Hold input incrementally advances the controller target |
| Input gate / 输入门控 | Conditions allowing operator command publication |
| Namespace / 命名空间 | Prefix isolating ROS arm topics and services |
| Transient local / 本地瞬态 | DDS durability delivering the latest retained state to late joiners |
| Dry run / 空运行 | Controller logic without CAN connection or physical motion |
| Impedance / 阻抗 | Position error generates restoring torque/force |
| Admittance / 导纳 | Estimated external wrench drives compliant reference motion |
| Software E-stop / 软件急停 | ROS command handled by backend; not an independent safety circuit |

## 12. 一手来源 / Primary sources

实现合同以同级控制包源码为准 / Interface contracts are defined in sibling source:

- `../agxarm_control_by_gamecontroller/armbycontroller/teleop/keyboard.py`
- `../agxarm_control_by_gamecontroller/armbycontroller/ros/control_cycle.py`
- `../agxarm_control_by_gamecontroller/armbycontroller/ros/telemetry.py`
- `../agxarm_control_by_gamecontroller/armbycontroller/api/interaction.py`
- `../agxarm_control_by_gamecontroller/armbycontroller/ros/parameters.py`
- `../agxarm_control_by_gamecontroller/config/common.yaml`, `config/nero.yaml`, `config/piper_l.yaml`
- `../agxarm_control_by_gamecontroller/PROJECT_STUDY_GUIDE_ZH_EN.md`

平台资料 / Platform references: [ROS 2 Humble](https://docs.ros.org/en/humble/),
[Qt 5 Widgets](https://doc.qt.io/qt-5/qtwidgets-index.html).

## 13. 三语与界面 / Languages and interface

GUI 支持中文、日文、英文，默认中文；CLI `--language zh|ja|en`，launch 参数
`language:=zh|ja|en`。右上角即时切换会取消操作使能但保留未保存 YAML，不重建 ROS 节点。
`i18n.py` 集中管理文案及同名占位符，`test_i18n.py` 检查覆盖、状态保留和急停可见性。
新的深色卡片布局在点动区显示关节角度；软件急停固定在各页签外，滚动后仍可访问。
控制协议、控制器默认参数和安全限幅未变化。原始 ROS 消息、日志和 YAML 保留原文。

The GUI supports Chinese, Japanese and English, defaulting to Chinese. Select
`--language zh|ja|en` or launch `language:=zh|ja|en`. Switching languages disarms
input while preserving unsaved YAML and the ROS node. `i18n.py` owns translated
strings and matching placeholders; `test_i18n.py` covers translation completeness,
state preservation and E-stop visibility. Dark cards show joint angles next to jog
buttons. E-stop remains outside the tabs and scrolling region. Control protocols,
backend defaults and safety limits are unchanged. Raw ROS messages/logs and YAML
remain verbatim. See [trilingual instructions](STARTUP_ZH_JA_EN.md).

## 14. 软件命令互锁 / Software command interlocks

命令入口不依赖按钮是否灰显或上一帧 allowed 标志。使能、点动、模式请求与持续
点动发送会重新检查 ROS 图、状态和反馈。输入话题必须恰好有一个发布者和一个订阅者。
关节点动仅在 normal/impedance + joint 下接受一个有效轴与一个方向；笛卡尔点动仅在
normal/impedance + ik 下接受一个方向。Piper-L 不接受第七轴，导纳/混合不接受点动。
模式、型号或实机/空运行状态变化会取消使能。关节/IK 切换等待状态话题确认，确认前
禁止新命令；未确认时保持锁定，检查控制器后重连。急停不受这些普通命令门控限制。

Command entries do not trust disabled widgets or the previous frame's allowed flag.
Arming, jogging, mode requests and held-jog publication recheck the ROS graph, state
and feedback. The input topic must have exactly one publisher and one subscriber.
Joint jog accepts one valid joint and one direction only in normal/impedance + joint;
Cartesian jog accepts one direction only in normal/impedance + ik. Piper-L rejects J7;
admittance/hybrid reject jogging. Changes to robot, execution state or control modes
disarm input. Joint/IK toggles block new commands until a changed control-mode snapshot
arrives. An unconfirmed toggle remains locked; inspect the controller before reconnecting.
Software E-stop bypasses normal command gating. DDS discovery and event-state delivery
still have latency; these checks supplement the backend interlocks, not a hardware
safety circuit or distributed ownership lock.
