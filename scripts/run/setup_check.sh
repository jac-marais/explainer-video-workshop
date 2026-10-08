#!/bin/sh
# Read-only check of the local tools a production needs: sh scripts/run/setup_check.sh [PATH_TO_hyperframes_BIN]
# Prints OK/FAIL per item and exits 1 on any FAIL. Without the argument it skips the HyperFrames CLI check.
set -u
WS="$(cd "$(dirname "$0")/../.." && pwd)"
HF="${1:-}"
HFHUB="${HF_HOME:-$HOME/.cache/huggingface}/hub"
KOKORO="${KOKORO_TTS_CACHE:-$HOME/.cache/hyperframes/tts}"
ESPEAK="${AGENT_PROTOCOL_ESPEAK_NG_PREFIX:-/opt/homebrew/opt/espeak-ng}"
CHROME="/Applications/Google Chrome.app"
fails=0

ok()   { printf 'OK    %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; fails=$((fails + 1)); }
note() { printf '      %s\n' "$1"; }
check() { if [ "$1" = 0 ]; then ok "$2"; else fail "$3"; fi; }
# A Hugging Face model counts only when a snapshot holds at least one file.
snapshot() { [ -n "$(ls "$HFHUB/models--$1/snapshots"/*/* 2>/dev/null | head -1)" ]; }

echo "== ffmpeg"
command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null
check $? "ffmpeg and ffprobe: $(command -v ffmpeg)" "ffmpeg or ffprobe is not on PATH"
if ffmpeg -hide_banner -filters 2>/dev/null | grep -q ' drawtext '; then
  ok "ffmpeg drawtext filter"
else
  ok "ffmpeg has no drawtext, so render labels with the PIL fallback (Pillow draws the text into a PNG, ffmpeg overlays it)"
fi

echo "== voice"
command -v uv >/dev/null
check $? "uv: $(command -v uv)" "uv is not on PATH"
if command -v uv >/dev/null; then
  tmp="$(mktemp)"
  # --offline makes uv resolve the script header from its cache and never download.
  uv run --offline "$WS/local/voice/voice.py" --list >"$tmp" 2>&1
  check $? "uv run --offline resolves local/voice/voice.py" "uv run --offline cannot resolve voice.py (cache cold?): $(tail -1 "$tmp")"
  rm -f "$tmp"
fi
if [ -f "$WS/local/voice/voice.json" ]; then
  ok "voice.json: $(python3 -c "import json,sys; c=json.load(open(sys.argv[1])); print(', '.join(k + (' (default)' if k == c['default'] else '') for k in c['voices']))" "$WS/local/voice/voice.json")"
  # Each voice needs its model snapshot and reference files.
  python3 - "$WS/local/voice" "$HFHUB" <<'PY'
import json, os, sys
d, hub = sys.argv[1:]
bad = 0
for name, v in json.load(open(f"{d}/voice.json"))["voices"].items():
    need = [f"{d}/{v[k]}" for k in ("ref_audio", "ref_text") if k in v]
    miss = [os.path.basename(p) for p in need if not os.path.isfile(p)]
    if "model" in v:
        snaps = f"{hub}/models--{v['model'].replace('/', '--')}/snapshots"
        if not (os.path.isdir(snaps) and os.listdir(snaps)):
            miss.append(v["model"])
    bad += bool(miss)
    print(("FAIL  " if miss else "OK    ") + f"voice '{name}' ({v['engine']})" + (f" missing: {', '.join(miss)}" if miss else ""))
sys.exit(bad)
PY
  fails=$((fails + $?))
else
  fail "local/voice/voice.json is missing"
fi
for f in models/kokoro-v1.0.onnx voices/voices-v1.0.bin; do
  [ -s "$KOKORO/$f" ]; check $? "Kokoro $f" "Kokoro file missing: $KOKORO/$f"
done
[ -f "$ESPEAK/lib/libespeak-ng.dylib" ]; check $? "espeak-ng library" "espeak-ng library missing: $ESPEAK/lib/libespeak-ng.dylib (brew install espeak-ng)"
[ -d "$ESPEAK/share/espeak-ng-data" ]; check $? "espeak-ng data" "espeak-ng data missing: $ESPEAK/share/espeak-ng-data"

echo "== whisper"
snapshot mlx-community--whisper-large-v3-turbo
check $? "mlx-whisper large-v3-turbo snapshot" "mlx-whisper large-v3-turbo snapshot missing in $HFHUB"
snapshot Systran--faster-whisper-small.en
check $? "faster-whisper small.en snapshot" "faster-whisper small.en snapshot missing in $HFHUB"

echo "== renderer"
command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 22 ] 2>/dev/null
check $? "node $(node -v 2>/dev/null) (22+ needed)" "node 22+ is not on PATH (hf.sh uses ~/.nvm/versions/node/v24.12.0/bin)"
if [ -z "$HF" ]; then
  printf 'SKIP  HyperFrames CLI: pass the route'"'"'s HyperFrames CLI as the argument\n'
else
  [ -x "$HF" ]; check $? "HyperFrames CLI: $HF" "HyperFrames CLI missing: $HF"
fi
[ -d "$CHROME" ]; check $? "Google Chrome: $CHROME" "Google Chrome missing: $CHROME"

echo "== HyperFrames environment (set these before check/render; hf.sh does)"
note 'export HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_NO_AUTO_INSTALL=1   # else a background self-update breaks render ("Missing manifest")'
note 'export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1'
note 'export HYPERFRAMES_BROWSER_PATH="'"$CHROME"'/Contents/MacOS/Google Chrome"   # host Chrome, so WebGL uses the GPU'
note 'unset GEMINI_API_KEY GOOGLE_API_KEY   # snapshot would send frames to Gemini'
if [ -n "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}" ]; then note "this shell has a Gemini/Google key set"; fi

echo
if [ "$fails" -eq 0 ]; then echo "All checks passed."; else echo "$fails check(s) failed."; exit 1; fi
