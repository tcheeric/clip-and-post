#!/usr/bin/env bash
# Read step for several sources at once: transcript for a video, text for an article.
#
#   scripts/batch-read.sh SCRATCH URL [URL...]
#
# Each source gets its own numbered directory (SCRATCH/01, SCRATCH/02, ...) because
# article.py always writes article.html into the current directory, and two articles read
# side by side would overwrite each other's source of truth. All reads run in parallel;
# they are small and network-bound. One failure doesn't stop the others: every source ends
# with a status line, and a failed one keeps its stderr in err.txt.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRATCH="$1"; shift
[[ $# -gt 0 ]] || { echo "usage: batch-read.sh SCRATCH URL [URL...]" >&2; exit 2; }

read_one() {
  local n="$1" url="$2" dir="$SCRATCH/$1"
  mkdir -p "$dir" && cd "$dir" || return
  echo "$url" > url.txt
  if [[ "$url" =~ (youtube\.com|youtu\.be)/ ]]; then
    if "$HERE/transcript.py" "$url" --bucket 30 > transcript.txt 2> err.txt; then
      echo "$n  video    ok      $(grep -m1 '^# title' transcript.txt | cut -c13-)"
    else
      echo "$n  video    FAILED  $(grep -m1 -E 'no captions|ERROR' err.txt)   $url"
    fi
  else
    if "$HERE/article.py" "$url" > article.txt 2> err.txt && [[ -s article.txt ]]; then
      echo "$n  article  ok      $(wc -w < article.txt) words   $url"
    else
      echo "$n  article  FAILED  $(tail -1 err.txt)   $url"
    fi
  fi
}

i=0
for url in "$@"; do
  i=$((i + 1))
  read_one "$(printf '%02d' "$i")" "$url" &
done
wait
