#!/usr/bin/env bash
# One-command macOS/Linux uninstaller. Configuration is kept unless requested.
# curl -fsSL https://raw.githubusercontent.com/harshit-dev-on/blind-spot/main/scripts/uninstall.sh | bash

set -euo pipefail

BLINDSPOT_HOME="${HOME}/.blindspot"
INSTALL_DIR="${BLINDSPOT_HOME}/bin"
CLEAN_CONFIG=0
FORCE="${BLINDSPOT_UNINSTALL_FORCE:-0}"

for arg in "$@"; do
    case "$arg" in
        --clean-config) CLEAN_CONFIG=1 ;;
        -y|--yes|--force) FORCE=1 ;;
        *) echo "Unknown option: $arg" >&2; exit 2 ;;
    esac
done
if [[ "${BLINDSPOT_CLEAN_CONFIG:-0}" == "1" ]]; then CLEAN_CONFIG=1; fi

if [[ "$FORCE" != "1" ]]; then
    if [[ ! -r /dev/tty ]]; then
        echo "No interactive terminal. Re-run with --force to uninstall." >&2
        exit 2
    fi
    read -r -p "Remove BlindSpot and its managed Python environment? Configuration will be kept. (y/N) " answer </dev/tty
    case "${answer,,}" in y|yes) ;; *) echo "Uninstallation cancelled."; exit 0 ;; esac
fi

for name in blindspot blindspot1; do
    rm -f -- "${INSTALL_DIR}/${name}"
done

clean_profile() {
    local profile="$1" tmp
    [[ -f "$profile" ]] || return 0
    tmp="$(mktemp)"
    awk -v path="$INSTALL_DIR" '
        $0 == "# BlindSpot CLI" {
            if ((getline next_line) > 0) {
                if (index(next_line, path) > 0 && (next_line ~ /^export PATH=/ || next_line ~ /^fish_add_path /)) next
                print
                print next_line
                next
            }
            print
            next
        }
        index($0, path) > 0 && ($0 ~ /^export PATH=/ || $0 ~ /^fish_add_path /) { next }
        { print }
    ' "$profile" > "$tmp"
    cat "$tmp" > "$profile"
    rm -f -- "$tmp"
}

clean_profile "${HOME}/.bashrc"
clean_profile "${HOME}/.zshrc"
clean_profile "${HOME}/.zprofile"
clean_profile "${HOME}/.profile"
clean_profile "${HOME}/.config/fish/config.fish"

remove_managed_dir() {
    local target="$1" expected="$2"
    local parent
    parent="$(cd -- "$(dirname -- "$target")" 2>/dev/null && pwd)"
    if [[ "$parent" != "$expected" ]]; then
        echo "Refusing to remove unexpected path: $target" >&2
        exit 2
    fi
    if [[ -d "$target" && ! -L "$target" ]]; then
        rm -rf -- "$target"
        echo "Removed $target"
    fi
}

remove_managed_dir "${BLINDSPOT_HOME}/venv-py312" "$BLINDSPOT_HOME"
remove_managed_dir "${BLINDSPOT_HOME}/uv" "$BLINDSPOT_HOME"

if [[ "$CLEAN_CONFIG" == "1" ]]; then
    remove_managed_dir "$BLINDSPOT_HOME" "$HOME"
elif [[ -d "$INSTALL_DIR" && -z "$(find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
    rmdir -- "$INSTALL_DIR"
fi

echo "BlindSpot was removed. Open a new terminal to refresh PATH."
if [[ "$CLEAN_CONFIG" != "1" ]]; then
    echo "Saved configuration and bridge data remain under ${BLINDSPOT_HOME}."
    echo "Run again with --clean-config to remove that data too."
fi
