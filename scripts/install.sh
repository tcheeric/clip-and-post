#!/usr/bin/env bash
# Chooses where clip-and-post writes its output, once, at install time.
#
#   install.sh              ask, defaulting to ~/clip-and-post (no prompt without a terminal)
#   install.sh DIR          use DIR
#   install.sh --print      print the chosen folder; exits 1 if the skill was never installed
#
# The choice lives outside the skill folder, in ~/.config, so reinstalling or updating the
# skill's files keeps it.
set -euo pipefail

CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/clip-and-post/output-dir"
DEFAULT="$HOME/clip-and-post"

if [[ "${1:-}" == "--print" ]]; then
  [[ -s "$CONFIG" ]] || { echo "clip-and-post is not installed: run scripts/install.sh" >&2; exit 1; }
  cat "$CONFIG"
  exit 0
fi

dir="${1:-}"
if [[ -z "$dir" && -t 0 ]]; then
  read -r -p "Where should clips, highlights and topic lists go? [$DEFAULT] " dir
fi
dir="${dir:-$DEFAULT}"
dir="${dir/#\~/$HOME}"
dir="$(realpath -m "$dir")"

mkdir -p "$dir" "$(dirname "$CONFIG")"
printf '%s\n' "$dir" > "$CONFIG"
echo "clip-and-post output folder: $dir"
