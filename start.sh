#!/bin/bash
# ============================================
# 青萍小台 MVP - macOS / Linux 启动入口
# 仅作为薄壳调用 start.py（跨平台主脚本）
# ============================================

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PY_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PY_BIN="python"
else
  echo "[错误] 未检测到 Python，请先安装 Python 3.10+"
  echo "下载地址: https://www.python.org/downloads/"
  exit 1
fi

echo "[信息] 调用 $PY_BIN start.py"
exec "$PY_BIN" start.py "$@"