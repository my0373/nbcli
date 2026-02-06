#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SHELL_NAME="${SHELL##*/}"

if [[ "${SHELL_NAME}" == "zsh" ]]; then
  echo "Detected zsh. Run:"
  echo ""
  echo "autoload -Uz compinit"
  echo "compinit"
  echo "fpath=(${REPO_ROOT}/completions \$fpath)"
  echo "autoload -Uz _nbcli"
  echo "compdef _nbcli nbcli"
  echo ""
  echo "Add the above to your ~/.zshrc to persist."
  exit 0
fi

if [[ "${SHELL_NAME}" == "bash" ]]; then
  echo "Detected bash. Run:"
  echo ""
  echo "source ${REPO_ROOT}/completions/nbcli.bash"
  echo ""
  echo "Add the above to your ~/.bashrc to persist."
  exit 0
fi

echo "Unknown shell: ${SHELL_NAME}"
echo "Zsh: autoload -Uz compinit; compinit; fpath=(${REPO_ROOT}/completions \$fpath); compdef _nbcli nbcli"
echo "Bash: source ${REPO_ROOT}/completions/nbcli.bash"
