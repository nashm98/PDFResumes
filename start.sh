#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PORT="${PORT:-8000}"

cd "$ROOT_DIR"

echo "[1/4] Verificando Python..."
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "❌ No se encontró $PYTHON_BIN. Instala Python 3 y vuelve a intentar."
  exit 1
fi

echo "[2/4] Preparando entorno virtual..."
if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "[3/4] Instalando dependencias (si aplica)..."
if [ -f "$ROOT_DIR/requirements.txt" ] && rg -q "^[^#[:space:]]" "$ROOT_DIR/requirements.txt"; then
  PIP_DISABLE_PIP_VERSION_CHECK=1 pip install -r "$ROOT_DIR/requirements.txt" || \
    echo "⚠️ No se pudieron instalar dependencias (red restringida). Continuando en modo local."
else
  echo "ℹ️ No hay dependencias obligatorias para instalar."
fi

APP_URL="http://localhost:$PORT"

echo "[4/4] Iniciando servidor en $APP_URL"
echo "Presiona Ctrl+C para detenerlo."

auto_open_browser() {
  sleep 1
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$APP_URL" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "$APP_URL" >/dev/null 2>&1 || true
  fi
}

auto_open_browser &

export PORT
exec "$VENV_DIR/bin/python" app.py
