#!/usr/bin/env bash
# Confirm an edited clip actually has video (not just audio) and that the
# fades landed where intended. Prints mean luma at each sampled time —
# near 0 means black, so a fade boundary should dip and recover.
#
# Usage: verify.sh CLIP.mp4 [t1 t2 t3 ...]
set -euo pipefail
F=$1; shift
echo "=== streams ==="
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height \
        -of csv=p=0 "$F"
ffprobe -v error -show_entries stream=codec_type -of csv=p=0 "$F" | grep -q '^video$' \
  || { echo "NO VIDEO STREAM — the download fell back to audio-only, see SKILL.md" >&2; exit 1; }
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$F")
printf '=== duration: %.0fs ===\n' "$DUR"
[ $# -gt 0 ] || set -- 0 0.5 "$(echo "$DUR/2" | bc -l)" "$(echo "$DUR-0.3" | bc -l)"
echo "=== mean luma (≈0 = black) ==="
for t in "$@"; do
  v=$(ffmpeg -v error -ss "$t" -i "$F" -frames:v 1 -vf "scale=64:36,format=gray" \
        -f rawvideo - 2>/dev/null | od -An -tu1 \
        | awk '{for(i=1;i<=NF;i++){s+=$i;n++}} END{if(n)printf "%.1f", s/n; else print "n/a"}')
  printf '  t=%-8ss  %s\n' "$t" "$v"
done
