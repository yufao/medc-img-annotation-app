#!/usr/bin/env bash
set -euo pipefail

# 预留的自动部署脚本，可结合 CI/CD 使用。
# 建议在此脚本中调用仓库根目录的 manage.sh 进行统一管理。

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "[deploy] building images..."
./manage.sh build

echo "[deploy] restarting services..."
./manage.sh restart

echo "[deploy] done."

