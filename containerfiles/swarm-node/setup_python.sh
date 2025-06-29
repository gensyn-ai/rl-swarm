#!/bin/bash
set -euo pipefail

PYTHON_KEY="python"

# Get the version
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PYTHON_VERSION=$(jq -r --arg keyvar "$PYTHON_KEY" '.[$keyvar]' "$SCRIPT_DIR/versions.json")

if  ! command -v pyenv &> /dev/null; then
  echo "Installing PyEnv for management of Python versions"
  curl --proto '=https' --tlsv1.2 https://pyenv.run -sSf | sh -s -- --help 

  echo ""
  echo "Adding pyenv to your local environment"
  function append_pyenv_init_to_file () {

	FILE="$1"
	if [[ -f "$FILE" ]]; then
	  ALREADY_INSTALLED=$(grep -c "pyenv" "$FILE") || true 
	  if [ "$ALREADY_INSTALLED" -eq 0 ]; then
		  echo "Appending pyenv preamble to $FILE"
		  {
			  # shellcheck disable=SC2016
			  echo 'export PYENV_ROOT="$HOME/.pyenv"' 
			  # shellcheck disable=SC2016
			  echo 'if [ ! $(command -v pyenv >/dev/null) ]; then if [[ -d "$PYENV_ROOT"/bin ]]; then export PATH="$PYENV_ROOT/bin:$PATH" fi; fi; fi'
			  # shellcheck disable=SC2016
			  echo 'eval "$(pyenv init -)"'
			  # shellcheck disable=SC2016
			  echo 'eval "$(pyenv init --path)"'
		  } >> "$FILE"
	  else
		  echo "$FILE already contains the pyenv preamble."
	  fi
	else
	  echo "Skipping appending to $FILE. It does not exist."
	fi
  }

  export PYENV_ROOT="/home/gensyn/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
  append_pyenv_init_to_file "/home/gensyn/.zshrc"
  append_pyenv_init_to_file "/home/gensyn/.bashrc"
  append_pyenv_init_to_file "/home/gensyn/.profile"
fi

echo ""
echo "Installing Python $PYTHON_VERSION"
pyenv install "$PYTHON_VERSION"

echo ""
echo "Setting Python $PYTHON_VERSION as the default."
pyenv global "$PYTHON_VERSION"

echo "Complete. Please reload your shell."
