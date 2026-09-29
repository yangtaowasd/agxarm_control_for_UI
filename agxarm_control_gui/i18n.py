"""Chinese, Japanese and English UI text; ROS identifiers stay unchanged."""

LANGUAGES = ('zh', 'ja', 'en')
LANGUAGE_NAMES = ('中文', '日本語', 'English')

# Every entry has the same language order. Keep placeholders identical.
MESSAGES = {
    'event_log': ('事件记录', 'イベントログ', 'EVENT LOG'),
    'window_title': ('AGX 机械臂操作台 · Nero / Piper-L',
                     'AGX ロボットアーム操作パネル · Nero / Piper-L',
                     'AGX Arm Console · Nero / Piper-L'),
    'subtitle': ('机械臂操作台 · ROS 2 / Nero / Piper-L',
                 'ロボットアーム操作パネル · ROS 2 / Nero / Piper-L',
                 'Arm operator console · ROS 2 / Nero / Piper-L'),
    'robot': ('型号', '機種', 'Robot'),
    'namespace': ('命名空间', '名前空間', 'Namespace'),
    'input_topic': ('输入话题', '入力トピック', 'Input topic'),
    'connect': ('连接 ROS', 'ROS に接続', 'Connect ROS'),
    'disconnect': ('断开', '切断', 'Disconnect'),
    'disconnected': ('未连接', '未接続', 'Disconnected'),
    'normal': ('关节/笛卡尔遥控', '関節・直交座標操作', 'Joint/Cartesian teleoperation'),
    'joint_remote': ('关节遥控', '関節操作', 'Joint teleoperation'),
    'cartesian_control': ('笛卡尔控制', '直交座標制御', 'Cartesian control'),
    'selected_mode': ('当前模式：{mode}', '現在のモード：{mode}', 'Current mode: {mode}'),
    'selection_timeout': ('模式确认超时，请断开并重新连接', 'モード確認タイムアウト。再接続してください', 'Mode confirmation timed out; disconnect and reconnect'),
    'focus_paused': ('窗口未激活，已释放输入', 'ウィンドウ非アクティブ・入力解除', 'Window inactive; input released'),
    'impedance': ('阻抗控制', 'インピーダンス制御', 'Impedance control'),
    'admittance': ('导纳控制', 'アドミッタンス制御', 'Admittance control'),
    'hybrid': ('混合', 'ハイブリッド', 'Hybrid'),
    'joint': ('关节', '関節', 'Joint'),
    'ik': ('笛卡尔', '直交座標', 'Cartesian'),
    'joint_jog': ('关节点动 · 按住移动', '関節ジョグ · 押している間移動', 'Joint jog · Hold to move'),
    'cartesian_jog': ('笛卡尔点动 · 按住移动', '直交座標ジョグ · 押している間移動',
                      'Cartesian jog · Hold to move'),
    'pitch': ('俯仰 Pitch', 'ピッチ', 'Pitch'),
    'yaw': ('偏航 Yaw', 'ヨー', 'Yaw'),
    'roll': ('滚转 Roll', 'ロール', 'Roll'),
    'jog_notice': (
        '松开、切走窗口或失联后清除点动输入。\n软件急停不替代物理急停。',
        'ボタンを離す、別のウィンドウに切り替える、または接続が切れるとジョグ入力を解除します。\nソフトウェア非常停止は物理的な非常停止の代わりにはなりません。',
        'Release, focus loss or connection loss clears jog input.\nSoftware E-stop is not a physical E-stop.'),
    'estop': ('软件急停', 'ソフトウェア非常停止', 'SOFTWARE E-STOP'),
    'control_tab': ('操作', '操作', 'Control'),
    'telemetry_tab': ('状态', '状態', 'Telemetry'),
    'config_tab': ('配置', '設定', 'Configuration'),
    'waiting_feedback': ('等待实测反馈', '実測フィードバックを待機中', 'Waiting for measured feedback'),
    'position_rad': ('位置 rad', '位置 rad', 'Position rad'),
    'position_deg': ('位置 °', '位置 °', 'Position °'),
    'velocity': ('速度 rad/s', '速度 rad/s', 'Velocity rad/s'),
    'torque': ('力矩 N·m', 'トルク N·m', 'Torque N·m'),
    'external_torque': ('外力矩 N·m', '外力トルク N·m', 'External torque N·m'),
    'config_notice': (
        '离线编辑；保存后需重启控制器。\n校验仅检查 YAML 结构和有限数值。',
        'オフライン編集です。保存後、適用にはコントローラーの再起動が必要です。\n検証は YAML 構造と有限な数値のみを確認します。',
        'Offline editor; restart the controller after saving to apply.\nValidation checks YAML structure and finite values only.'),
    'robot_defaults': ('加载型号配置', '機種の既定設定を読み込む', 'Load robot defaults'),
    'open_yaml': ('打开 YAML', 'YAML を開く', 'Open YAML'),
    'validate': ('校验', '検証', 'Validate'),
    'save_as': ('另存为', '名前を付けて保存', 'Save as'),
    'launch_command': ('终端启动命令（不执行硬件运动）',
                       '端末起動コマンド（実機を動作させません）',
                       'Terminal launch command (dry run)'),
    'demo': ('界面预览 · 合成数据 · 无 ROS 连接',
             '画面プレビュー · 合成データ · ROS 接続なし',
             'DEMO · Synthetic data · No ROS connection'),
    'connect_failed': ('连接失败：{detail}', '接続に失敗：{detail}', 'Connection failed: {detail}'),
    'connected': ('已连接 ROS；等待控制器', 'ROS に接続済み。コントローラーを待機中',
                  'ROS connected; waiting for controller'),
    'estop_sent': ('已发送软件急停；等待控制器状态确认',
                   'ソフトウェア非常停止を送信。コントローラーの確認を待機中',
                   'E-stop sent; awaiting controller acknowledgement'),
    'local_estop': ('GUI 急停已锁定；恢复控制器后重新连接',
                    'GUI の非常停止がラッチされています。コントローラー復旧後に再接続してください',
                    'GUI E-stop latched; restore the controller before reconnecting'),
    'demo_feedback': ('预览 · 合成示例数据', 'プレビュー · 合成サンプルデータ', 'DEMO · Synthetic example data'),
    'measured_feedback': ('实测反馈', '実測フィードバック', 'Measured feedback'),
    'no_feedback': ('无新鲜反馈', '新しいフィードバックがありません', 'No fresh feedback'),
    'unsaved_retained': ('保留未保存内容；切换型号后请加载对应配置。',
                         '未保存の編集を保持しました。機種に対応する設定を読み込んでください。',
                         'Unsaved edits retained; load the matching robot config.'),
    'config_failed': ('配置加载失败：{detail}', '設定の読み込みに失敗：{detail}', 'Cannot load config: {detail}'),
    'yaml_valid': ('YAML 结构校验通过；参数范围由控制器校验',
                   'YAML 構造は有効です。パラメーター範囲はコントローラーが検証します',
                   'YAML structure valid; the controller validates parameter ranges'),
    'yaml_invalid': ('YAML 校验失败：{detail}', 'YAML 検証に失敗：{detail}', 'Invalid YAML: {detail}'),
    'saved': ('已保存；重启控制器后生效', '保存しました。コントローラーの再起動後に適用されます',
              'Saved; restart the controller to apply'),
    'unsaved': ('未保存', '未保存', 'Unsaved'),
    'input_conflict': ('检测到其他键盘发布者', '別の入力パブリッシャーを検出しました', 'Another input publisher exists'),
    'waiting_controller': ('等待控制器', 'コントローラーを待機中', 'Waiting for controller'),
    'robot_mismatch': ('机械臂型号不匹配', 'ロボットの機種が一致しません', 'Robot model mismatch'),
    'controller_estop': ('急停已锁定；恢复后重连', '非常停止がラッチされています。復旧後に再接続してください',
                         'Emergency stop latched; restore before reconnecting'),
    'mode_pending': ('模式切换中', 'モード切り替え中', 'Mode request pending'),
    'arm_not_ready': ('机械臂未就绪', 'ロボットの準備ができていません', 'Arm not ready'),
    'feedback_stale': ('硬件反馈超时', '実機フィードバックがタイムアウトしました', 'Hardware feedback stale'),
    'live': ('实机控制', '実機制御', 'LIVE HARDWARE'),
    'dry_run': ('空运行：无硬件反馈', 'ドライラン：実機フィードバックなし', 'DRY RUN: no hardware feedback'),
    'invalid_state': ('状态解析失败：{detail}', '状態の解析に失敗：{detail}', 'Invalid state: {detail}'),
    'service_unavailable': ('服务不可用：{mode}', 'サービスを利用できません：{mode}', 'Service unavailable: {mode}'),
    'request_mode': ('请求模式：{mode}', 'モードを要求：{mode}', 'Request mode: {mode}'),
    'service_success': ('成功：{detail}', '成功：{detail}', 'OK: {detail}'),
    'service_failed': ('失败：{detail}', '失敗：{detail}', 'Failed: {detail}'),
    'service_error': ('服务错误：{detail}', 'サービスエラー：{detail}', 'Service error: {detail}'),
    'service_timeout': ('服务超时，执行结果未知；保持锁定直到响应。',
                        'サービスがタイムアウトしました。実行結果は不明です。応答まで操作をロックします。',
                        'Service timeout; outcome unknown, input remains locked until a response.'),
    'invalid_namespace': ('命名空间无效', '名前空間が無効です', 'Invalid ROS namespace'),
    'invalid_schema': ('不支持的状态协议版本', '未対応の状態スキーマです', 'Unsupported interaction-state schema'),
    'invalid_robot': ('不支持的机械臂型号', '未対応のロボット機種です', 'Unsupported robot model'),
    'invalid_interaction': ('交互模式无效', 'インタラクションモードが無効です', 'Invalid interaction mode'),
    'invalid_control': ('坐标控制模式无效', '制御座標モードが無効です', 'Invalid control mode'),
    'invalid_boolean': ('状态缺少布尔字段', '状態のブール値フィールドがありません', 'Missing boolean state field'),
    'invalid_yaml_mapping': ('配置必须包含 ROS 节点映射', '設定には ROS ノードのマッピングが必要です',
                             'Expected ROS node mappings'),
    'nonfinite_yaml': ('不允许 NaN 或无穷值', 'NaN または無限大は使用できません', 'NaN / infinity is not allowed'),
    'invalid_node_section': ('ROS 节点配置无效', 'ROS ノードの設定が無効です', 'Invalid ROS node section'),
    'missing_parameters': ('每个节点都需要 ros__parameters', '各ノードに ros__parameters が必要です',
                           'Each node needs ros__parameters'),
    'invalid_key': ('按键协议索引无效', 'キープロトコルのインデックスが無効です', 'Invalid keyboard protocol index'),
    'file_location': ('位置：', '場所：', 'Look in:'),
    'file_name': ('文件名：', 'ファイル名：', 'File name:'),
    'file_type': ('文件类型：', 'ファイルの種類：', 'Files of type:'),
    'open': ('打开', '開く', 'Open'),
    'save': ('保存', '保存', 'Save'),
    'cancel': ('取消', 'キャンセル', 'Cancel'),
    'overwrite': ('文件已存在，是否覆盖？\n{path}', 'ファイルは既に存在します。上書きしますか？\n{path}',
                  'The file exists. Overwrite it?\n{path}'),
}


def translate(key, language='zh', **values):
    """Translate known UI keys, preserving external diagnostics verbatim."""
    if language not in LANGUAGES:
        raise ValueError('Unsupported GUI language: ' + str(language))
    if key not in MESSAGES:
        return str(key)
    return MESSAGES[key][LANGUAGES.index(language)].format(**values)


class LocalizedError(ValueError):
    """Keep validation independent of the selected presentation language."""

    def __init__(self, key, detail=''):
        self.key = key
        self.detail = detail
        super().__init__(translate(key, 'en') + (': ' + detail if detail else ''))

    def localized(self, translator):
        return translator(self.key) + (': ' + self.detail if self.detail else '')
