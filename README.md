# AGX Arm GUI

独立 ROS 2 / PyQt5 操作台，默认 **Nero / `/nero` / `nero.yaml`**，可切换 Piper-L。
控制器来自同级 `agxarm_control_by_gamecontroller` 包，本包不直接访问 CAN。

Independent ROS 2 / PyQt5 console. Defaults to **Nero**, namespace `/nero`, and
`nero.yaml`. Piper-L is selectable. All hardware access stays in the sibling
`agxarm_control_by_gamecontroller` package.

功能 / Features:

- 七轴 Nero / 六轴 Piper-L 按住点动，关节与笛卡尔切换。
  Hold-to-jog joint and Cartesian controls for seven/six axes.
- 普通、阻抗、导纳模式服务；显示实际返回结果和控制器状态。
  Normal, impedance and admittance services with actual results.
- 关节位置、速度、实测力矩、观测外力矩、事件日志。
  Joint positions, velocities, measured torques, estimated external torques and events.
- 软件急停、窗口失焦取消使能、反馈过期锁定、输入发布者冲突检查。
  Software E-stop, focus-loss disarming, stale-feedback gate and input conflict detection.
- YAML 加载、结构校验、另存为，以及对应的空运行启动命令。
  YAML loading, structural validation, save-as and generated dry-run launch command.

## 构建 / Build

依赖包括 ROS 2 Humble、`python3-pyqt5`、`python3-yaml`，以及控制包已有的
`pyAgxArm`/运动学依赖。使用系统 Python 与 ROS 环境。依赖缺失时可在工作空间
运行 `rosdep install --from-paths src/agxarm_control_gui --ignore-src -r -y`。

Requires ROS 2 Humble, PyQt5, PyYAML, and the existing controller's SDK/kinematics
dependencies. Use the system Python with the ROS environment sourced.

```bash
cd /home/yang/demo_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-up-to agxarm_control_gui
source install/setup.bash
```

## 启动 / Run

仅预览界面，不创建 ROS 节点 / Preview with synthetic data, without creating a ROS node:

```bash
ros2 run agxarm_control_gui gui --demo
```

GUI 与 Nero 控制器一起空运行，不连接 CAN、不执行硬件运动。
空运行需要 SDK/模型，且不生成虚假的实测反馈。
Launch GUI plus Nero controller in dry run, with no CAN connection or physical motion.
Dry run still needs the SDK/models and does not fabricate measured feedback:

```bash
ros2 launch agxarm_control_gui gui.launch.py start_controller:=true
```

启动真实 Nero 控制器；此命令会连接并使能机械臂。
Launch the real Nero controller; this connects and enables the arm:

```bash
ros2 launch agxarm_control_gui gui.launch.py \
  start_controller:=true execute_motion:=true can_interface:=can0
```

仅连接已经运行的控制器 / Attach to an existing controller:

```bash
ros2 run agxarm_control_gui gui
# Piper-L:
ros2 run agxarm_control_gui gui --robot-model piper_l --namespace /piper_l
```

已经运行控制器时不要再传 `start_controller:=true`。同一输入话题不能同时运行
实体键盘发布者；出现第二个发布者时 GUI 会锁定操作。新 launch 不启动键盘读取器。
Do not start a second controller when attaching. Stop other input publishers on the
same topic; the GUI locks input when another publisher is detected. This launch does
not start the physical keyboard reader.

界面启动后先检查状态，再勾选“启用 GUI 操作”。松开点动按钮、切走窗口、状态异常
都会清除输入或取消使能，恢复连接后需重新勾选。模式请求后也需重新勾选。
Check controller status before enabling GUI input. Release clears jog input; focus
loss and faults disarm. Re-enable explicitly after recovery or a mode request.

关闭 GUI 只释放输入；不会自动退出阻抗/导纳、断开 CAN 或停止由 launch 启动的控制器。
控制器结束仍由启动终端的 Ctrl+C 管理。软件急停需要健康的 ROS/控制器路径，不能代替
物理急停。GUI 不提供自动急停复位、回零或混合模式入口。
Closing the GUI releases input but does not exit compliant modes, disconnect CAN or
stop launched controller nodes. Use Ctrl+C in the launch terminal to stop those nodes.
Software E-stop depends on ROS and a responsive controller; it is not a physical E-stop.
No automatic E-stop reset, homing or hybrid-mode entry is provided.

## 配置与测试 / Configuration and tests

“配置”页默认读取已安装控制包的 `config/nero.yaml`。加载其他文件可以直接编辑源文件
副本。另存为后复制生成的启动命令；编辑不会写入正在运行的 ROS 参数。通用参数文件可
通过 `common_config:=/absolute/path/common.yaml` 指定。结构校验不验证控制稳定性或所有
参数范围，控制器仍执行自己的校验。

The editor initially reads the installed controller's `config/nero.yaml`. Open any
other YAML as needed, save a copy and use the generated launch command. Edits never
change live ROS parameters. Pass `common_config:=/absolute/path/common.yaml` to select
a shared parameter file. Structural validation does not establish physical stability
or validate every parameter range; the controller performs its own checks.

```bash
cd /home/yang/demo_ws
source install/setup.bash
QT_QPA_PLATFORM=offscreen PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /usr/bin/python3 -m pytest src/agxarm_control_gui/test -q
```

详见 [中英学习指南 / Bilingual study guide](PROJECT_STUDY_GUIDE_ZH_EN.md)。

## 三语界面 / 3言語 UI / Three-language UI

支持中文、日本語、English；右上角即时切换，默认中文和 Nero。
中国語・日本語・英語に対応。右上で切り替えます。既定は中国語と Nero です。
Chinese, Japanese and English are selectable at the top right; defaults are Chinese and Nero.

`ros2 run agxarm_control_gui gui --language ja`

详见 [三语说明 / 3言語ガイド / Trilingual guide](STARTUP_ZH_JA_EN.md)。

软件互锁 / Software interlocks: command entry points recheck state and feedback;
mode changes disarm held input, joint/Cartesian commands cannot cross modes, and
unconfirmed joint/IK toggles block new commands. See the study guide, section 14.
# agxarm_control_for_UI
