# GUI working agreements

## Language preference / 实现语言偏好

- 优先使用 C++ 实现新增软件，尤其是 GUI、ROS 节点与控制逻辑。
- 只有必须依赖 Python 库或现有接口存在实际限制时才使用 Python，并说明原因。
- 本偏好不等于自动重写现有 Python 代码；迁移应在明确任务范围内进行。
- Prefer C++ for new implementations, particularly GUIs, ROS nodes and control logic.
  Use Python when required by a Python-only library or a concrete existing-interface
  constraint, and explain why. Do not infer an automatic rewrite of existing Python code.
