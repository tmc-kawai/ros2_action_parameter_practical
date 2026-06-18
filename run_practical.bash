#!/bin/bash
#
# Environment-independent launcher for the ROS2 action/parameter practical.
#
# Key idea: mount ONLY this workspace (not the host home), so the host's
# conda / pyenv / .bashrc can never leak into the container. The container
# therefore always uses its own /usr/bin/python3, and the build behaves the
# same on every machine. GPU is enabled only if the host has the nvidia
# docker runtime, so it also works on machines without a GPU.
#
# Supported: x86_64 (amd64) Linux with Docker Engine installed and the user
# allowed to run docker (in the `docker` group, or run with sudo). The image
# is amd64-only; ARM / macOS are not supported.
#
# Usage (run once per terminal):
#   ./run_practical.bash
#
# The FIRST call starts the container; every later call (other terminals)
# attaches a new shell to the SAME running container, so all terminals share
# one ROS2 graph and the same /ros2_ws. Inside, ROS2 Jazzy and (if built) the
# workspace overlay are sourced automatically. The workspace is at /ros2_ws.

set -e

_name="ros2-practical"
_image="osrf/ros:jazzy-desktop-full"
_ws_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/ros2_practical_ws" && pwd)"

# --------------------------------------------------------------------------- #
# Preflight checks (clear errors instead of cryptic docker failures)
# --------------------------------------------------------------------------- #

# 1) Docker installed?
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is not installed."
    echo "  Install Docker Engine: https://docs.docker.com/engine/install/"
    exit 1
fi

# 2) Daemon reachable AND we have permission? (one call, reused for GPU check)
if ! _docker_info="$(docker info 2>/dev/null)"; then
    echo "ERROR: cannot talk to the Docker daemon."
    echo "  - Is it running?      sudo systemctl start docker"
    echo "  - Permission denied?  sudo usermod -aG docker \$USER   (then log out/in)"
    echo "                        ...or run this script with sudo."
    exit 1
fi

# 3) Architecture (the image is amd64-only)
_arch="$(uname -m)"
if [ "${_arch}" != "x86_64" ]; then
    echo "ERROR: this practical requires an x86_64 (amd64) machine."
    echo "  Detected: ${_arch}. The ${_image} image is amd64-only (ARM is unsupported)."
    exit 1
fi

# --------------------------------------------------------------------------- #
# If the container is already running, just open another shell in it.
# --------------------------------------------------------------------------- #
if [ -n "$(docker ps -q -f name="^${_name}$")" ]; then
    echo "Attaching a new shell to the running '${_name}' container..."
    exec docker exec -it "${_name}" bash
fi

# --------------------------------------------------------------------------- #
# Optional features, enabled only when the host actually supports them.
# --------------------------------------------------------------------------- #

# GPU only when the nvidia runtime is present.
_gpu=""
if grep -qiE 'Runtimes:.*nvidia' <<<"${_docker_info}"; then
    _gpu="--gpus all"
fi

# X11 only when there is a display and an X11 socket (skip on headless/Wayland;
# avoids creating a stray root-owned /tmp/.X11-unix and snap-docker mount issues).
_x11=()
if [ -n "${DISPLAY}" ] && [ -d /tmp/.X11-unix ]; then
    _x11=(--env=DISPLAY --env=QT_X11_NO_MITSHM=1
          --volume=/tmp/.X11-unix:/tmp/.X11-unix:rw)
    if command -v xhost >/dev/null 2>&1; then
        xhost +local: >/dev/null 2>&1 || true
    fi
fi

# Note: `:z` relabels the bind mount for SELinux distros (Fedora/RHEL/Rocky);
# it is a harmless no-op on non-SELinux systems.
exec docker run --rm -it \
    --name="${_name}" \
    ${_gpu} \
    "${_x11[@]}" \
    --net=host \
    --ipc=host \
    --env="ROS_DOMAIN_ID=42" \
    --env="ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST" \
    --env="HOME=/ros2_ws" \
    --user="$(id -u):$(id -g)" \
    --volume="${_ws_dir}:/ros2_ws:z" \
    --workdir="/ros2_ws" \
    "${_image}" \
    bash
