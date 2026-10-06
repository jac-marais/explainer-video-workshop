#!/usr/bin/env bash
# Extracts 16 evenly spaced key frames per brand video into frames/<slug>/1.jpg..16.jpg.
set -euo pipefail
cd "$(dirname "$0")"

FRAMES=16
MARGIN=4 # seconds skipped at each end, where fades and title cards live

for video in *.mp4; do
  slug="${video%.mp4}"
  mkdir -p "frames/$slug"
  duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$video")
  for i in $(seq 0 $((FRAMES - 1))); do
    t=$(awk -v i="$i" -v n="$FRAMES" -v d="$duration" -v m="$MARGIN" \
      'BEGIN { printf "%.3f", m + (i + 0.5) / n * (d - 2 * m) }')
    ffmpeg -v error -y -ss "$t" -i "$video" -frames:v 1 -vf scale=640:-2 -q:v 4 "frames/$slug/$((i + 1)).jpg"
  done
done
