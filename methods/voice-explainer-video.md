# Choose and clone a narration voice — v0.1

Status: derived from one bake-off of local voice models, on one Apple Silicon Mac, for one operator's voice. Treat it as a tested procedure, not proof that it generalizes.

The workshop ships no one's voice. The operator's voice setup lives in `local/voice/`, which is git-ignored:

| File | Holds |
|---|---|
| `README.md` | the profile: what the operator chose, when, and any standing decisions |
| `voice.json` | the voices and which one is the default |
| `voice.py` | the narration CLI |
| `reference.wav`, `reference.txt` | a clone's reference recording and its transcript (clone only) |

`templates/voice/` holds the blank copy of the profile, config and CLI.

## First use

1. Read `local/voice/README.md`.
2. If it is missing, copy `templates/voice/` to `local/voice/`. Its default is Kokoro `af_heart`, the voice that runs used before this method existed.
3. Ask the user once: **"Narration uses a stock voice (Kokoro, `af_heart`). Would you like to clone your own voice instead? It needs an Apple Silicon Mac and a one-minute recording."**
4. If they say yes, follow "Clone a voice". Record the answer in `local/voice/README.md` either way, so nobody asks again.

## Pick the voice for a run

- A run keeps the voice that its audio receipt or filled production prompt already names. Changing the voice is a re-recording, so it invalidates everything in the "approved audio bytes" row of the table in step 6 of `methods/prepare-explainer-video.md`.
- A new run uses the default in `local/voice/voice.json`, unless the user names another voice.
- Copy the voice name and the CLI's receipt into the run's `audio-receipt.md`.

## Generate narration

```bash
uv run local/voice/voice.py scene-01.txt scene-02.txt --out-dir production/audio/raw
uv run local/voice/voice.py scene-01.txt --out-dir production/audio/raw --voice kokoro
uv run local/voice/voice.py --list
```

Each text file becomes a WAV (mono, 24 kHz, −16 LUFS) and a JSON receipt of the same name. The model loads once per call, so pass every scene in one call. The text is what the voice says, so put the spoken respellings from `local/pronunciation.md` in it. Pauses, timing and the transcript checks in M1 of `templates/production-prompt.md` stay the run's job.

`voice.json` can name more voices than these two. The CLI has four engines: `kokoro` (a Kokoro voice and speed), `qwen3` (a Qwen3 clone from a reference), `qwen3-preset` (one of Qwen3's stock speakers) and `chatterbox` (a Chatterbox Turbo clone from a reference). To add a voice, add an entry to `voice.json`. The template's two entries show the shape for `kokoro` and `qwen3`; a `qwen3-preset` entry needs `model` and `speaker`, and a `chatterbox` entry needs `model` and `ref_audio`.

These engines were the best local, commercially usable options that a bake-off on 2026-10-07 found for an Apple Silicon Mac. Local speech models improve quickly. If today is more than about three months past that date, assume they are no longer state of the art. Research the current local options before you recommend a voice or a cloning model. Check a current speech-quality leaderboard and each model's licence, then test the strongest candidates. A better model can join as a new engine in `voice.py`.

Kokoro needs eSpeak NG from Homebrew (`brew install espeak-ng`) and the model files that HyperFrames caches in `~/.cache/hyperframes/tts/`. Set `KOKORO_TTS_CACHE` to point at another copy.

## Clone a voice

The clone is Qwen3-TTS 1.7B Base (bf16) through mlx-audio. It is in-context cloning: the model hears the reference recording and its transcript, then continues in that voice. No training happens.

### Requirements

- An Apple Silicon Mac, because mlx-audio runs on MLX. There is no Intel, Linux or Windows path in this method.
- `uv` and `ffmpeg`.
- About 5 GB of disk: 4.2 GB for the model, which downloads on first use, and about 560 MB for the script's Python environment. Kokoro adds 340 MB.
- Memory: MLX peaked at about 15 GB on a 48 GB M4 Pro, even for a short clip. A 16 GB Mac is untested.
- Time: on that machine, a take takes between about real time and twice real time.
- A decent microphone in a quiet room. AirPods Pro worked; set Mic Mode to Standard, not Voice Isolation.

### Steps

1. List the input devices and note the microphone's index:
   ```bash
   ffmpeg -f avfoundation -list_devices true -i ""
   ```
2. Give the user the passage below and the record command. Recording stops when they press `q`. Ask them to act the cues, not read them aloud, and tell them that improvising is fine.
   ```bash
   ffmpeg -f avfoundation -i ":1" -ac 1 -ar 24000 local/voice/reference-raw.wav
   ```
3. Transcribe what they actually said with faster-whisper `medium.en`, which heard words correctly that `small.en` missed:
   ```bash
   uv run --python 3.12 --with faster-whisper --with "av<17" python -c 'from faster_whisper import WhisperModel as W; s,_=W("medium.en",compute_type="int8").transcribe("local/voice/reference-raw.wav",beam_size=5,word_timestamps=True); [print(f"{w.start:.2f} {w.end:.2f} {w.probability:.2f} {w.word}") for x in s for w in x.words]'
   ```
   Write the words to `local/voice/reference.txt`, with numbers spelled out. If a word is unclear, ask the user what they said, or cut that stretch out of the recording.
4. Trim the silence before the first word and after the last, keeping about 0.2 s at each end, and save the result as `local/voice/reference.wav`. Do not denoise it. Count clipped samples (at or above 0.999 of full scale); more than a few dozen means a re-take with the input level turned down.
5. Make a test take of a paragraph from a real script with `--voice clone`, and give the user the WAV to play. Their ear decides. If they accept it, set `"default": "clone"` in `voice.json` and record the clone in `README.md`. Mark the Kokoro verdicts in `local/pronunciation.md` as not applying to the clone, and start a new heading for it.

### Recording passage

About 150 words, or a minute at a natural pace. The cues in brackets are for the reader, not the microphone.

> [warm, easy] Hi. Let me tell you about the morning my kettle broke.
>
> [brisk] It was six o'clock, still dark, and I was already late. I pressed the switch. Nothing. I pressed it again. [frustrated] Still nothing!
>
> [dry] So I did what any reasonable person would do. I shook it. Gently, at first. Then not so gently.
>
> [quick, puzzled] Was it the fuse? The plug? Had I simply forgotten to pay the electricity bill?
>
> [slow] And then I saw it. The plug was lying on the counter, nowhere near the wall.
>
> [laughing] Honestly, I laughed out loud.
>
> [calm, measured] Here's the thing, though. Most problems look enormous at six in the morning. Slow down, check the simple things first, and you'll usually find the plug on the counter.
>
> [bright] Right. The tea's ready. Let's get started.

### Limitations

- **It copies the reference, flaws and all.** Room noise, distance from the microphone, pace and energy all carry into the clone. A flat reading gives a flat clone. Record clean rather than clean up afterwards: in the bake-off, a denoised reference made the clone sound crunchy and synthetic, and the raw recording won.
- **Longer references are better.** The full reference (about 47 s) beat 13 s and 20 s cuts of the same recording. The passage above changes emotion on purpose. In the one trial so far, a plain explainer reading made the preferred clone, so a second take in a calmer register is cheap insurance.
- **Accents drift.** A non-American accent came through, but not perfectly. Fine-tuning would go further; this method does not cover it.
- **Every take is different.** The same paragraph came out between 26 and 29 seconds long across takes. The CLI records the seed in the receipt, and `--seed` with the same text and reference gives a byte-identical take on the same machine. So a take the user likes can be made again.
- **Fix a wrong word; don't re-roll the seed.** Speech-to-text mishears too, so a word it flags is only a lead. Read its guess aloud. If it sounds like the right word, such as "save state" for "saved state", nothing needs fixing. Otherwise listen to the take. A word the voice really gets wrong, it usually gets wrong in every take, so a new seed rarely helps. Respell or reorder it in `local/pronunciation.md`, then re-make the take once to check the fix.
- **Long texts are split.** A single pass stops at 4096 tokens, about 330 s of audio, and slows as the text grows. The CLI splits text over 400 words at sentence ends and joins the parts with 0.25 s of silence; `--max-words` raises that limit for a longer single take. Each part is a fresh take, so the delivery can shift slightly at a join; one file per run (next point) avoids them.
- **Voice the script in runs of 1 to 2 minutes.** Each generation starts lively and settles. In trials, the pitch range inside sentences fell most in a take's first minute, held to about 3 minutes, then sagged, and a 4-minute take sounded monotone. Each new generation also restarts higher, so many short takes jump at every join. Group whole scenes into runs of 60–120 s, and when several groupings fit, take the most even. Cut each run back into its sentences in the pauses between them.
- **Pronunciation verdicts don't carry over.** The clone has no eSpeak phonemizer, so Kokoro's verdicts say nothing about it. M1's pronunciation pass applies to every voice.
- **Licences and consent.** Qwen3-TTS and Kokoro are Apache-2.0 (model cards), and mlx-audio is MIT. Clone only your own voice, or one whose owner has agreed in writing. The reference recording is personal data, so it stays in `local/` and never goes into a commit, an upload or a prompt to a hosted model.
