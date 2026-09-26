#!/usr/bin/env bash
# Cut N sub-segments out of a source clip, fade each one in and out, and
# concatenate them into a single file — in one ffmpeg pass, no intermediates.
#
# Usage:
#   cut.sh IN.mp4 OUT.mp4 FADE_SECONDS "IN-OUT" ["IN-OUT" ...]
# Example:
#   cut.sh segment-raw.mp4 clip.mp4 0.7 3-128 208-285
#
# Times are seconds relative to IN.mp4. Re-encodes (necessary: fades and
# frame-accurate cuts can't be done with stream copy).

set -euo pipefail
[ $# -ge 4 ] || { sed -n '2,12p' "$0"; exit 1; }

IN=$1; OUT=$2; FADE=$3; shift 3
CRF=${CRF:-26}; PRESET=${PRESET:-slow}; ABR=${ABR:-96k}

fc=""; maps=""; n=0; total=0
for seg in "$@"; do
  s=${seg%%-*}; e=${seg##*-}
  d=$(echo "$e - $s" | bc -l)
  o=$(echo "$d - $FADE" | bc -l)
  # Guard: a segment shorter than the fade would produce a clip that never
  # reaches full brightness, which reads as a glitch rather than a transition.
  if (( $(echo "$o <= 0" | bc -l) )); then
    echo "segment $seg is $(printf %.1f "$d")s, shorter than the ${FADE}s fade" >&2; exit 1
  fi
  fc+="[0:v]trim=${s}:${e},setpts=PTS-STARTPTS,fade=t=in:st=0:d=${FADE},fade=t=out:st=${o}:d=${FADE}[v${n}];"
  fc+="[0:a]atrim=${s}:${e},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=${FADE},afade=t=out:st=${o}:d=${FADE}[a${n}];"
  maps+="[v${n}][a${n}]"
  total=$(echo "$total + $d" | bc -l); n=$((n+1))
done
fc+="${maps}concat=n=${n}:v=1:a=1[v][a]"

ffmpeg -y -hide_banner -loglevel error -stats -i "$IN" -filter_complex "$fc" \
  -map '[v]' -map '[a]' \
  -c:v libx264 -crf "$CRF" -preset "$PRESET" -pix_fmt yuv420p \
  -c:a aac -b:a "$ABR" -movflags +faststart "$OUT"

echo
printf 'segments: %d   duration: %.0fs   ' "$n" "$total"
ls -lh "$OUT" | awk '{print "size: "$5}'
