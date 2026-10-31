#!/usr/bin/env bash
# One-command macOS/Linux installer. Supports running from GitHub or a local checkout.
# curl -fsSL https://raw.githubusercontent.com/harshit-dev-on/blind-spot/master/scripts/install.sh | bash

set -euo pipefail

BLINDSPOT_HOME="${HOME}/.blindspot"
INSTALL_DIR="${BLINDSPOT_HOME}/bin"
VENV_DIR="${BLINDSPOT_HOME}/venv-py312"
UV_INSTALL_DIR="${BLINDSPOT_HOME}/uv"
VENV_PYTHON="${VENV_DIR}/bin/python"

mkdir -p "$INSTALL_DIR" "$BLINDSPOT_HOME"

if command -v uv >/dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
else
    echo "Installing the managed Python/package installer..."
    mkdir -p "$UV_INSTALL_DIR"
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$UV_INSTALL_DIR" UV_NO_MODIFY_PATH=1 sh
    UV_BIN="${UV_INSTALL_DIR}/uv"
fi

run_step() {
    local label="$1"
    shift
    echo "→ ${label}"
    "$@"
}

run_step "Installing Python 3.12" "$UV_BIN" python install 3.12
run_step "Creating an isolated application environment" "$UV_BIN" venv --clear --python 3.12 "$VENV_DIR"

REPO_ROOT=""
SCRIPT_SOURCE="${BASH_SOURCE[0]:-$0}"
if [[ -f "$SCRIPT_SOURCE" ]]; then
    SCRIPT_DIR="$(cd -- "$(dirname -- "$SCRIPT_SOURCE")" && pwd)"
    if [[ -f "${SCRIPT_DIR}/../pyproject.toml" ]]; then
        REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
    fi
fi
if [[ -z "$REPO_ROOT" && -f "./pyproject.toml" ]]; then
    REPO_ROOT="$(pwd)"
fi

if [[ -n "$REPO_ROOT" ]]; then
    run_step "Installing BlindSpot and its Python dependencies" "$UV_BIN" pip install --python "$VENV_PYTHON" --upgrade --editable "$REPO_ROOT"
else
    ZIP_URL="https://github.com/harshit-dev-on/blind-spot/archive/refs/heads/main.zip"
    if ! curl -sI "$ZIP_URL" | grep -q "200\|302"; then
        ZIP_URL="https://github.com/harshit-dev-on/blind-spot/archive/refs/heads/master.zip"
    fi
    run_step "Installing BlindSpot and its Python dependencies" "$UV_BIN" pip install --python "$VENV_PYTHON" --upgrade "$ZIP_URL"
fi

if [[ "$(uname -s)" == Linux* ]]; then
    run_step "Installing Chromium and required Linux browser libraries" "$VENV_PYTHON" -m playwright install --with-deps chromium
else
    run_step "Installing Chromium" "$VENV_PYTHON" -m playwright install chromium
fi

cat > "${INSTALL_DIR}/blindspot1" <<EOF
#!/usr/bin/env bash
exec "${VENV_DIR}/bin/blindspot1" "\$@"
EOF
cat > "${INSTALL_DIR}/blindspot" <<EOF
#!/usr/bin/env bash
exec "${VENV_DIR}/bin/blindspot1" "\$@"
EOF
chmod +x "${INSTALL_DIR}/blindspot1" "${INSTALL_DIR}/blindspot"

add_path() {
    local profile="$1"
    touch "$profile"
    if ! grep -Fq "$INSTALL_DIR" "$profile"; then
        printf '\n# BlindSpot CLI\nexport PATH="%s:$PATH"\n' "$INSTALL_DIR" >> "$profile"
    fi
}

case "${SHELL##*/}" in
    bash) add_path "${HOME}/.bashrc"; add_path "${HOME}/.profile" ;;
    zsh) add_path "${HOME}/.zshrc"; add_path "${HOME}/.zprofile"; add_path "${HOME}/.profile" ;;
    fish)
        fish_config="${HOME}/.config/fish/config.fish"
        mkdir -p "$(dirname "$fish_config")"
        touch "$fish_config"
        if ! grep -Fq "$INSTALL_DIR" "$fish_config"; then
            printf '\n# BlindSpot CLI\nfish_add_path "%s"\n' "$INSTALL_DIR" >> "$fish_config"
        fi
        ;;
    *) add_path "${HOME}/.profile" ;;
esac
export PATH="${INSTALL_DIR}:$PATH"

echo
echo "BlindSpot is installed."
echo "Run 'blindspot1 setup' any time to change providers or model settings."
echo "The default Antigravity mode works without a cloud API key."

USER_CONFIG="${BLINDSPOT_HOME}/config.toml"
if [[ ! -f "$USER_CONFIG" ]]; then
    echo
    echo "Let's configure your first run. Choose the Antigravity default for a no-key setup."
    if [[ -t 0 ]]; then
        "$VENV_PYTHON" -m blindspot1 setup || echo "Installation completed. Run 'blindspot1 setup' to finish configuration."
    elif [[ -e /dev/tty ]]; then
        "$VENV_PYTHON" -m blindspot1 setup </dev/tty || echo "Installation completed. Run 'blindspot1 setup' to finish configuration."
    else
        echo "Run 'blindspot1 setup' in a terminal to complete configuration."
    fi
else
    echo "Existing configuration found at ${USER_CONFIG}; it was left unchanged."
fi

echo
echo "Start an audit with: blindspot1 inspect -u https://example.com -c 'Explore the main user journey' --headed"
echo "If this terminal cannot find the command, open a new terminal window."
