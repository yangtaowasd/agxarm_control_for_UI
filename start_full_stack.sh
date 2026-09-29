#!/usr/bin/env bash
# Source-workspace entry: build all four packages and launch the GUI control path.
set -euo pipefail

readonly PACKAGE_DIRECTORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly WORKSPACE_DIRECTORY="$(cd -- "${PACKAGE_DIRECTORY}/../.." && pwd)"
BUILD=true
MOTION=false
CAN_INTERFACE=can0
ARGUMENTS=()
for argument in "$@"; do
  case "${argument}" in
    -h | --help)
      cat <<'HELP'
Usage: ./start_full_stack.sh [--hardware] [--skip-build] [name:=value ...]
Default: build all four packages, then launch GUI + controller + observer in dry run.
--hardware    Configure CAN at 1000000 bit/s, then connect and enable the arm.
              Stop existing CAN controllers before using this option.
--skip-build  Use the current workspace installation without rebuilding.
Examples:
  ./start_full_stack.sh
  ./start_full_stack.sh --hardware language:=zh
  ./start_full_stack.sh --skip-build robot_model:=piper_l
  ./start_full_stack.sh --hardware controller_config:=/absolute/path/nero.yaml
No physical keyboard reader, automatic homing or emergency-stop reset is started.
HELP
      exit 0
      ;;
    --hardware) MOTION=true ;;
    --skip-build) BUILD=false ;;
    execute_motion:=true) MOTION=true ;;
    execute_motion:=false) MOTION=false ;;
    execute_motion:=*) echo "Error: execute_motion must be true or false." >&2; exit 2 ;;
    can_interface:=*) CAN_INTERFACE="${argument#can_interface:=}" ;;
    start_controller:=true) ;;
    start_controller:=*) echo "Error: this entry always starts the controller." >&2; exit 2 ;;
    *=*)
      if [[ "${argument}" != *:=* ]]; then
        echo "Error: use name:=value launch arguments." >&2; exit 2
      fi
      ARGUMENTS+=("${argument}")
      ;;
    *) echo "Error: unknown argument: ${argument}; use --help." >&2; exit 2 ;;
  esac
done
[[ -n "${CAN_INTERFACE}" ]] || { echo "Error: empty CAN interface." >&2; exit 2; }
for package in agx_arm_math agx_arm_controllers nero_arm_control agxarm_control_gui; do
  if [[ ! -f "${WORKSPACE_DIRECTORY}/src/${package}/package.xml" ]]; then
    echo "Error: missing source package ${WORKSPACE_DIRECTORY}/src/${package}." >&2
    exit 1
  fi
done
if [[ ! -f /opt/ros/humble/setup.bash ]]; then
  echo "Error: ROS Humble is required." >&2; exit 1
fi
set +u
# shellcheck source=/dev/null
source /opt/ros/humble/setup.bash
set -u
cd -- "${WORKSPACE_DIRECTORY}"
if [[ "${BUILD}" == true ]]; then
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 colcon build \
    --packages-up-to agxarm_control_gui \
    --cmake-force-configure \
    --cmake-args -DAMENT_CMAKE_SYMLINK_INSTALL=OFF
fi
if [[ ! -f "${WORKSPACE_DIRECTORY}/install/setup.bash" ]]; then
  echo "Error: workspace installation missing; run without --skip-build." >&2; exit 1
fi
set +u
# shellcheck source=/dev/null
source "${WORKSPACE_DIRECTORY}/install/setup.bash"
set -u
if [[ "${MOTION}" == true ]]; then
  ip link show dev "${CAN_INTERFACE}" >/dev/null
  IP_COMMAND=(ip)
  if (( EUID != 0 )); then IP_COMMAND=(sudo ip); fi
  "${IP_COMMAND[@]}" link set dev "${CAN_INTERFACE}" down
  "${IP_COMMAND[@]}" link set dev "${CAN_INTERFACE}" type can bitrate 1000000
  "${IP_COMMAND[@]}" link set dev "${CAN_INTERFACE}" up
fi
exec ros2 launch agxarm_control_gui gui.launch.py \
  start_controller:=true execute_motion:="${MOTION}" \
  can_interface:="${CAN_INTERFACE}" "${ARGUMENTS[@]}"
