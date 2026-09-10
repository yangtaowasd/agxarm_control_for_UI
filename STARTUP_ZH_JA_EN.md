# 三语操作说明 / 3言語操作ガイド / Trilingual guide

## 中文

右上角选择中文、日本語或 English，即时切换按钮、状态、表头及应用提示。
默认中文，默认机械臂 Nero。切换语言会取消 GUI 操作使能，保留未保存的 YAML。
急停按钮固定在所有页签下方，不随点动区域滚动。ROS 标识符、原始控制器日志、
JSON 和 YAML 内容保留原文。文件浏览器的部分系统导航文字跟随 Qt/系统语言。

## 日本語

右上のセレクターで中文・日本語・Englishを選択すると、ボタン、状態表示、
表の見出し、アプリのメッセージが切り替わります。既定は中国語、機種は Nero です。
言語を切り替えると GUI 操作を無効化します。未保存の YAML 編集は保持されます。
非常停止ボタンはすべてのタブの下に固定され、ジョグ領域と一緒にスクロールしません。
ROS 識別子、コントローラーの生ログ、JSON、YAML は原文のまま表示します。
ファイル選択画面の一部のシステム項目は Qt・OS の言語に従います。

## English

Select 中文, 日本語 or English at the top right to translate buttons, status,
column headings and application messages immediately. Defaults: Chinese and Nero.
Changing language disarms GUI input and preserves unsaved YAML edits. The E-stop
button stays below every tab, outside the scrolling jog area. ROS identifiers,
raw controller logs, JSON and YAML remain verbatim. Some file-browser system
navigation labels follow the Qt/OS language.

## 启动 / 起動 / Launch

```bash
source /home/yang/demo_ws/install/setup.bash
# 中文预览 / 中国語プレビュー / Chinese preview
ros2 run agxarm_control_gui gui --demo --language zh
# 日文预览 / 日本語プレビュー / Japanese preview
ros2 run agxarm_control_gui gui --demo --language ja
# 英文预览 / 英語プレビュー / English preview
ros2 run agxarm_control_gui gui --demo --language en
# Nero 空运行 / Nero ドライラン / Nero dry run
ros2 launch agxarm_control_gui gui.launch.py start_controller:=true language:=ja
```

`language` / `--language`: `zh`（默认 / 既定 / default）、`ja`、`en`。
空运行不连接 CAN；实机仍需显式 `execute_motion:=true`。
ドライランでは CAN に接続しません。実機には明示的に `execute_motion:=true` が必要です。
Dry run does not connect CAN; hardware requires explicit `execute_motion:=true`.

## 界面与实现 / 画面と実装 / Interface and implementation

深色卡片、青绿色状态强调、实机关联的琥珀提示和红色急停；点动区域显示当前角度。
ダークカード、青緑の状態表示、実機用のアンバー表示、赤い非常停止。
ジョグ領域に現在の関節角度を表示します。
Dark cards, teal status accents, amber hardware status and a red E-stop; current
joint angles appear alongside jog controls.

`agxarm_control_gui/i18n.py` stores Chinese/Japanese/English strings with matching
format placeholders. Widgets register translation setters; language changes update
presentation without rebuilding the ROS node or modifying configuration contents.
The UI preserves the original control rates, limits and mode services.

测试 / テスト / Tests:

```bash
QT_QPA_PLATFORM=offscreen PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /usr/bin/python3 -m pytest /home/yang/demo_ws/src/agxarm_control_gui/test -q
```

See [README](README.md) and [学习指南 / 学習ガイド / Study guide](PROJECT_STUDY_GUIDE_ZH_EN.md)
for build instructions, control interfaces, safety boundaries and diagnostics.

## 软件互锁 / ソフトウェアインターロック / Software interlocks

点动和模式请求在发送入口检查状态；导纳/混合禁用点动，关节/笛卡尔模式严格匹配。
模式变化取消使能；关节/IK 切换未确认前锁定新命令。急停仍可发送。

ジョグとモード要求は送信時に状態を検証します。アドミッタンス・ハイブリッドでは
ジョグを禁止し、関節・直交座標の指令を現在のモードに限定します。モード変更で
操作を無効化し、関節/IK 切り替えの確認まで新しい指令をロックします。非常停止は送信できます。

Jog and mode requests validate state at command entry. Admittance/hybrid reject jogs;
joint/Cartesian intents must match the active mode. Mode changes disarm input;
joint/IK toggles block new commands until confirmed. E-stop remains available.
