#!/usr/bin/env bash
set -euo pipefail

show_install_help() {
  local tool="$1"
  echo "Missing required dependency: $tool" >&2
  echo >&2
  case "$(uname -s)" in
    Darwin)
      echo "macOS install suggestions:" >&2
      echo "  brew install ffmpeg" >&2
      ;;
    MINGW*|MSYS*|CYGWIN*)
      echo "Windows install suggestions:" >&2
      echo "  winget install Gyan.FFmpeg" >&2
      echo "or" >&2
      echo "  choco install ffmpeg" >&2
      ;;
    *)
      echo "Please install ffmpeg manually and make sure ffmpeg / ffprobe are available in PATH." >&2
      ;;
  esac
}

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <video_path> [--script script_path] [--intensity normal|more]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$SKILL_DIR/.venv"
PY="$VENV_DIR/bin/python"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found in PATH." >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  show_install_help "ffmpeg"
  exit 1
fi

if ! command -v ffprobe >/dev/null 2>&1; then
  show_install_help "ffprobe"
  exit 1
fi

if [ ! -x "$PY" ]; then
  python3 -m venv "$VENV_DIR"
  "$PY" -m pip install faster-whisper
fi

"$PY" "$SCRIPT_DIR/ai_video_edit.py" "$@"
