#!/usr/bin/env python3
"""Build a hover storyboard from a script, so a reader can check each planned picture against the words it lands on.

  storyboard.py SCRIPT.md --language CODE --out storyboard.html [--css BRAND.css] [--audio AUDIO_DIR]
                [--key-script KEY.md --key-language CODE]

SCRIPT.md has the `## Scene N: title` sections that cues.py reads, each with a `**Narration**` part and then a
`**Visual**` part. Every list item in the Visual part is one shot, and so is any other Visual paragraph that holds a
cue. A shot's cue is its first quoted span, written `On "words"` or `**"words"**`, and must be consecutive words of
that scene's narration, or a sentence cue such as `On s03-02+0.4`. Sentence fractions select an approximate token
position for preview; measured timing remains in cues.py. --language names the script's language for the sentence split in
text_tokens.py, so run this with scripts/run/py, which has Stanza. --key-script checks sentence counts against another script in
--key-language. Words compare as in cues.py. A shot without a cue follows the shot above it, or opens the scene when it
comes first. Markdown images in a shot, `![what it shows](path)`, become its key frames; give the path relative to SCRIPT.md.
A frame whose file does not exist yet shows as not drawn, and the run lists it.

The page shows the narration on the left, with a faint underline under each cue's words. Hovering a phrase shows the
shots that start on it, above a strip of every shot in its scene. Clicking a phrase or a strip shot pins it, and the
arrow keys step through. A header switch, off by default and remembered by the browser, makes a click on the narration
read aloud from that sentence to the end of the storyboard, at 1x to 3x, while the shots move forward with the words;
the next click anywhere on the page, or Esc, stops it. --audio names a folder that scripts/audio/narrate_film.py wrote. A sentence
plays its clip from that folder only when the folder's timing.json records the sentence's ID with the script's exact
text, and the clip's length matches that record. The browser checks the length again before it plays, so a clip voiced
again after the build falls back too. Every other sentence is read in a browser speech voice, which on macOS is a `say`
voice (Samantha by default). The header says how many sentences have a clip, and while a sentence reads, a bar at the
foot of the narration names its source and offers Stop. --css adds a stylesheet after the defaults, so a brand can
override the variables in :root. The run exits 1 when a scene has no Narration part, a cue isn't in its scene's
narration, or a sentence is under the word floor in step 3 of methods/prepare-explainer-video.md; with --key-script, the
floor checks the key script instead.
"""
import argparse, bisect, html, json, os, re, sys, wave
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audio"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "film"))
from text_tokens import norm, tokenize, normalized_tokens, sentences, short_sentences  # noqa: E402
from cues import CUE, SCENE, VISUAL, cue_text, sentence_ref  # noqa: E402
from build_data import scenes, check_sentence_counts  # noqa: E402

NARRATION = re.compile(r"\*\*Narration\.?\*\*")
ITEM = re.compile(r"^(\s*)(?:\d+\.|[-*])\s+(.*)")
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
LENGTH_SLACK = 0.002  # seconds; timing.json rounds each start and end to the millisecond


def inline(md, strip=True):
    s = re.sub(r"\s+", " ", IMAGE.sub("", md))
    s = html.escape(s.strip() if strip else s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"(?<![*\w])\*(?!\s)(.+?)\*", r"<i>\1</i>", s)


def shots_of(visual):
    """Split a Visual part into shots: list items, plus other paragraphs that hold a cue."""
    shots, para = [], []

    def flush():
        if para:
            text = " ".join(para)
            if CUE.search(text):
                shots.append(text)
            para.clear()

    for line in visual.splitlines():
        m = ITEM.match(line)
        if m:
            flush()
            shots.append(m.group(2))
        elif not line.strip():
            flush()
        elif shots and not para and line.startswith((" ", "\t")):
            shots[-1] += " " + line.strip()
        else:
            para.append(line.strip())
    flush()
    return shots


def words_of(text):
    """Each Unicode token with its normalized form and original character span."""
    return [(norm(t), t.start, t.end) for t in tokenize(text) if norm(t)]


def find(words, quote, start):
    toks = normalized_tokens(quote)
    if not toks:
        return None
    for lo in (start, 0):
        for i in range(lo, len(words) - len(toks) + 1):
            if all(words[i + k][0] == toks[k] for k in range(len(toks))):
                return i
    return None


def voiced(audio, page_dir):
    """Each sentence that AUDIO_DIR/timing.json records, by ID: its text, and its clip when the clip's length matches."""
    path = audio / "timing.json"
    if not path.is_file():
        return {}
    rows = {}
    for row in json.loads(path.read_text()).get("sentences", []):
        clip = audio / (row.get("audio") or f"sentences/{row['id']}.wav")
        try:
            with wave.open(str(clip)) as w:
                seconds = w.getnframes() / w.getframerate()
        except (OSError, EOFError, wave.Error):
            seconds = None
        # narrate_film.py writes the clips before timing.json, so a run in progress leaves lengths that disagree.
        good = seconds is not None and abs(seconds - (row["end"] - row["start"])) <= LENGTH_SLACK
        rows[row["id"]] = {"text": row["text"], "src": quote(os.path.relpath(clip, page_dir)) if good else None,
                           "seconds": round(seconds, 4) if good else None}
    return rows


def reading(sid, text, recorded):
    """What the page reads for one sentence: its clip when the voiced text is the script's, else why it has none."""
    item = {"text": text}
    if recorded is None:
        return item
    row = recorded.get(sid)
    if row is None:
        item["why"] = "it is not voiced yet"
    elif row["text"] != text:
        item["why"] = "it changed since it was voiced"
    elif row["src"] is None:
        item["why"] = "its clip is missing or unlike timing.json"
    else:
        item.update(src=row["src"], seconds=row["seconds"])
    return item


def audio_note(said, audio):
    if audio is None:
        return "A system voice reads each sentence. It is a reading aid, not the film's voice."
    played, total = sum("src" in s for s in said.values()), len(said)
    if played == total:
        return f"The film's narration reads all {total} sentences."
    if not played:
        return "No sentence has a narration clip that matches the script yet, so a system voice reads them all."
    rest = total - played
    other = "the other one, which has" if rest == 1 else f"the other {rest}, which have"
    return f"The film's narration reads {played} of {total} sentences. A system voice reads {other} no clip that matches the script."


def picture(alt, src, root):
    """A key frame's image, or the not-drawn placeholder while its file does not exist."""
    if (root / src).is_file():
        return f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" loading="lazy">'
    return '<span class="todo label">Not drawn yet</span>'


def paragraph_spans(text):
    """(start, end) of each blank-line-separated paragraph, without its outer whitespace."""
    spans = []
    for m in re.finditer(r"(?:(?!\n[ \t]*\n).)+", text, re.S):
        a, b = m.start() + len(m.group()) - len(m.group().lstrip()), m.start() + len(m.group().rstrip())
        if a < b:
            spans.append((a, b))
    return spans


def value_at(starts, at):
    """The ID of the last (start, ID) pair that starts at or before at."""
    k = bisect.bisect_right([s for s, _ in starts], at) - 1
    return starts[max(k, 0)][1] if starts else None


def narration_html(text, groups, said_at, marks):
    """The narration's paragraphs, as spans that each keep to one phrase group and one sentence.

    groups and said_at are (start character, ID) pairs in order; marks are the (start, end) characters of cue words."""
    cuts = {c for c, _ in groups} | {c for c, _ in said_at} | {c for span in marks for c in span}
    tabbed, paras = set(), []
    for lo, hi in paragraph_spans(text):
        points = sorted({lo, hi} | {c for c in cuts if lo < c < hi})
        runs = []
        for a, b in zip(points, points[1:]):
            key = (value_at(groups, a), value_at(said_at, a))
            piece = inline(text[a:b], strip=False)
            if any(x <= a and b <= y for x, y in marks):
                piece = f'<span class="k">{piece}</span>'
            if runs and runs[-1][0] == key:
                runs[-1][1].append(piece)
            else:
                runs.append((key, [piece]))
        out = []
        for (g, sid), pieces in runs:
            tab = "" if g in tabbed else ' tabindex="0"'
            tabbed.add(g)
            out.append(f'<span class="g" data-g="{g}" data-s="{sid}"{tab}>{"".join(pieces)}</span>')
        paras.append(f"<p>{''.join(out)}</p>")
    return paras


def build(script, css, language, key_script=None, key_language=None, audio=None, page_dir=None):
    """The page, its errors, its phrase-group count, and what it reads for each sentence ID."""
    errors, left, panels, strips, said = [], [], [], [], {}
    recorded = voiced(audio, page_dir or script.parent) if audio else None
    if key_script:
        key = {num: sentences(text, key_language) for num, text, _ in scenes(key_script)}
        check_sentence_counts({num: len(sentences(text, language)) for num, text, _ in scenes(script)},
                              {num: len(said) for num, said in key.items()})
        # A translation follows its key script's sentences, so the floor holds for the script the writer wrote.
        errors += short_sentences({f"s{num:02d}": [s["text"] for s in said] for num, said in key.items()})
    text = script.read_text()
    title = (re.search(r"^# (.+)$", text, re.M) or [None, script.stem])[1]
    for m in SCENE.finditer(text):
        num, body = int(m.group(1)), m.group(0)
        heading = body.splitlines()[0].split(":", 1)[1].strip()
        parts = NARRATION.split(body, 1)
        if len(parts) < 2:
            errors.append(f"scene {num}: no **Narration** part")
            continue
        narration, *visual = VISUAL.split(parts[1], 1)
        narration, visual = narration.strip(), "".join(visual)
        narration = re.sub(r"\[pause\]", " ", narration, flags=re.I)
        words = words_of(narration)
        sentence_list = sentences(narration, language) if words else []
        if not key_script:
            errors += short_sentences({f"s{num:02d}": [s["text"] for s in sentence_list]})
        ids = [f"s{num:02d}-{i:02d}" for i in range(1, len(sentence_list) + 1)]
        starts, before = [], 0  # the word index where each sentence starts
        for sentence in sentence_list:
            starts.append(before)
            before += len(words_of(sentence["text"]))
        for sid, sentence in zip(ids, sentence_list):
            said[sid] = reading(sid, sentence["text"], recorded)

        shots, groups, cursor = [], [], 0  # each group: [start word index, [shots]]
        for n, shot in enumerate(shots_of(visual), 1):
            quote = CUE.search(shot)
            name = cue_text(quote) if quote else None
            ref = sentence_ref(name) if name else None
            at = find(words, name, cursor) if name and not ref else None
            if ref:
                if ref[0] not in ids:
                    errors.append(f"scene {num}: missing sentence {ref[0]}")
                else:
                    index = ids.index(ref[0])
                    count = len(words_of(sentence_list[index]["text"]))
                    at = starts[index] + min(int(ref[1] * count), max(0, count - 1))
            if quote and at is None:
                errors.append(f'scene {num}: cue not in narration: "{name}"')
            item = {"n": n, "text": shot, "cue": name if at is not None else None, "at": at,
                    "length": 1 if ref else len(normalized_tokens(name or ""))}
            shots.append(item)
            if at is None:
                if not groups:
                    groups.append([0, []])
                groups[-1][1].append(item)
                continue
            cursor = at
            hit = next((g for g in groups if g[0] == at), None)
            if hit:
                hit[1].append(item)
            else:
                groups.append([at, [item]])
        groups.sort(key=lambda g: g[0])
        if not groups:
            groups = [[0, []]]
        marks = []
        for k, (start, members) in enumerate(groups):
            last_word = groups[k + 1][0] - 1 if k + 1 < len(groups) else len(words) - 1
            for item in members:
                item["g"] = len(panels) + k
                if item["at"] is not None:
                    marks.append((words[item["at"]][1], words[min(item["at"] + item["length"] - 1, last_word)][2]))
        groups[0][0] = 0

        left.append(f'<h2><span class="label">Scene {num}</span>{html.escape(heading)}</h2>')
        group_at = [(words[g[0]][1] if words and k else 0, len(panels) + k) for k, g in enumerate(groups)]
        said_at = [(words[min(s, len(words) - 1)][1] if i else 0, sid) for i, (s, sid) in enumerate(zip(starts, ids))]
        left.extend(narration_html(narration, group_at, said_at, marks))

        total = len(shots)

        def label(item, short=False):
            cue = f"“{html.escape(item['cue'])}”" if item["cue"] else None
            if short:
                return f"{item['n']}. {cue or 'No cue'}"
            if cue:
                return f"Shot {item['n']} of {total}, on {cue}"
            return f"Shot {item['n']} of {total} {'follows the shot above' if item['n'] > 1 else 'opens the scene'}, with no cue"

        for _, members in groups:
            cards = []
            for item in members:
                frames = "".join(f'<figure>{picture(alt, src, script.parent)}<figcaption class="label">{html.escape(alt)}</figcaption></figure>'
                                 for alt, src in IMAGE.findall(item["text"]))
                frames = f'<div class="frames">{frames}</div>' if frames else '<div class="todo label">Not drawn yet</div>'
                cards.append(f'<article><p class="label">{label(item)}</p>{frames}<p class="d">{inline(item["text"])}</p></article>')
            panels.append(f'<section class="panel" data-p="{len(panels)}" data-scene="{num}" hidden>'
                          f'{"".join(cards) or f"<p class=label>Scene {num} has no shots yet.</p>"}</section>')
        thumbs = []
        for item in shots:
            frame = IMAGE.search(item["text"])
            thumb = picture(frame[1], frame[2], script.parent) if frame else '<span class="todo label">Not drawn yet</span>'
            thumbs.append(f'<li><button type="button" data-g="{item["g"]}">{thumb}'
                          f'<span class="label name">{label(item, short=True)}</span></button></li>')
        if thumbs:
            strips.append(f'<section class="strip" data-scene="{num}" aria-label="Scene {num} shots" hidden>'
                          f'<p class="label">All {total} shots in scene {num}</p><ol>{"".join(thumbs)}</ol></section>')
    if not left:
        errors.append("no `## Scene N: title` sections found")
    style = f'<link rel="stylesheet" href="{html.escape(css)}">' if css else ""
    data = json.dumps(said, ensure_ascii=False).replace("</", "<\\/")
    page = (PAGE.replace("{{TITLE}}", html.escape(title)).replace("{{CSS}}", style)
            .replace("{{LANG}}", html.escape(language)).replace("{{SCRIPT}}", html.escape(script.name))
            .replace("{{AUDIO_NOTE}}", html.escape(audio_note(said, audio))).replace("{{LEFT}}", "\n".join(left))
            .replace("{{PANELS}}", "\n".join(panels)).replace("{{STRIPS}}", "\n".join(strips))
            .replace("{{SAID}}", data).replace("{{SLACK}}", str(LENGTH_SLACK)))
    return page, errors, len(panels), said


PAGE = """<!doctype html>
<html lang="{{LANG}}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}} (storyboard)</title>
<style>
:root{--font:system-ui,sans-serif;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;--ink:#1c1c1c;--paper:#fff;--panel:#f4f4f2;--muted:#595959;--rule:#d4d4d0;--mark:#8c8c8c;--accent:#2b4c7e;--hover:#e3e9f3;--pin:#c9d5e8;--frame:#111;--pad:40px}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--paper);color:var(--ink);font-family:var(--font);font-size:18px;line-height:1.55;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);grid-template-rows:minmax(0,1fr)}
#script{overflow-y:auto;padding:28px var(--pad) 0;border-right:1px solid var(--rule)}
#board{overflow-y:auto;padding:28px 36px 40px;background:var(--panel)}
.label{font-size:14px;line-height:1.4;font-weight:500;color:var(--muted);margin:0}
header h1{font-size:30px;font-weight:400;line-height:1.15;margin:0 0 8px}
.help{font-size:16px;line-height:1.5;color:var(--muted);margin:0 0 10px}
#tts{display:flex;flex-wrap:wrap;align-items:flex-end;gap:8px 16px;margin:6px 0 8px}
#tts label{display:flex;font-size:16px;cursor:pointer}
#tts .toggle{align-items:center;gap:10px;min-height:44px}
#tts .toggle input{width:20px;height:20px;margin:0;accent-color:var(--ink);cursor:pointer}
#tts .field{flex-direction:column;gap:2px}
#tts select{appearance:none;font:inherit;font-size:16px;color:var(--ink);min-height:44px;padding:0 36px 0 12px;border:1px solid var(--ink);border-radius:0;cursor:pointer;
  background:var(--paper) no-repeat;background-image:linear-gradient(45deg,transparent 50%,currentColor 50%),linear-gradient(135deg,currentColor 50%,transparent 50%);
  background-position:calc(100% - 20px) 50%,calc(100% - 14px) 50%;background-size:6px 6px}
#tts select:disabled{color:var(--muted);border-color:var(--muted);cursor:default}
h2{font-weight:400;font-size:20px;margin:40px 0 10px;border-bottom:1px solid var(--ink);padding-bottom:4px}
h2 .label{margin-right:10px}
p{margin:0 0 14px}
.g{cursor:pointer;outline:none}
.g:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
.k{text-decoration:underline dotted 2px var(--mark);text-underline-offset:.3em}
.g:hover:not(.on){background:var(--hover)}
.g.on{background:var(--hover);box-shadow:0 2px 0 var(--accent)}
.g.on .k{text-decoration-color:transparent}
/* A line above a wrapped phrase would underline the line before it, so a pin only thickens the line below. */
.g.pin{background:var(--pin);box-shadow:0 4px 0 var(--accent)}
#bar{position:sticky;bottom:0;display:flex;align-items:center;gap:16px;margin:0 calc(-1 * var(--pad)) 50vh;padding:0 var(--pad);background:var(--paper)}
#bar.live{padding-block:10px;border-top:1px solid var(--ink)}
#now{flex:1;margin:0;font-size:16px;line-height:1.4}
#stop{font:inherit;font-size:16px;color:var(--ink);min-height:44px;padding:0 16px;border:1px solid var(--ink);border-radius:0;background:var(--paper);cursor:pointer}
article{background:var(--paper);border:1px solid var(--rule);padding:16px;margin-bottom:16px}
article>.label{margin-bottom:10px}
article .d{margin:12px 0 0;font-size:18px;line-height:1.5}
.frames{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(min(160px,100%),1fr))}
figure{margin:0}
.frames img,.strip img{width:100%;aspect-ratio:16/9;object-fit:contain;display:block;background:var(--frame);box-shadow:0 0 0 1px var(--rule)}
figcaption{margin-top:8px}
.todo{width:100%;aspect-ratio:16/9;border:1.5px dashed var(--muted);display:flex;align-items:center;justify-content:center;text-align:center}
.strip{margin-top:28px;padding-top:12px;border-top:1px solid var(--rule)}
.strip ol{list-style:none;margin:12px 0 0;padding:0;display:grid;gap:18px 14px;grid-template-columns:repeat(auto-fill,minmax(128px,1fr))}
.strip button{display:flex;flex-direction:column;gap:6px;width:100%;padding:0;font:inherit;color:inherit;text-align:left;cursor:pointer;background:none;border:0}
.strip button:focus-visible{outline:2px solid var(--ink);outline-offset:4px}
.strip button:hover .name{color:var(--ink)}
.strip button.on img,.strip button.on .todo{outline:2px solid var(--accent);outline-offset:3px}
.strip button.on .name{color:var(--ink)}
.strip .name{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
code{font-family:var(--mono);font-size:.88em}
@media (max-width:760px){
  :root{--pad:20px}
  body{grid-template-columns:minmax(0,1fr);grid-template-rows:minmax(0,46fr) minmax(0,54fr)}
  #board{order:-1;padding:14px 16px 24px;border-bottom:2px solid var(--ink)}
  #script{padding-top:20px;border-right:0}
  #bar{margin-bottom:40vh}
  header h1{font-size:24px}
}
</style>
{{CSS}}
</head>
<body>
<main id="script">
<header><h1>{{TITLE}}</h1>
<p class="help">Built from {{SCRIPT}}. Each underlined phrase starts a shot. Hover a phrase to see its shots, click to pin it, and use the arrow keys to step. With read aloud on, a click reads on from its sentence to the end and moves the shots along with it. Click anywhere or press Esc to stop.</p>
<div id="tts"><label class="toggle"><input type="checkbox" id="speak"> Read aloud</label>
<label class="field" id="voice-field"><span class="label">System voice</span><select id="voice"></select></label>
<label class="field"><span class="label">Speed</span><select id="rate"><option value="1">1×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option><option value="2">2×</option><option value="2.5">2.5×</option><option value="3">3×</option></select></label></div>
<p class="help">{{AUDIO_NOTE}}</p>
</header>
{{LEFT}}
<div id="bar"><p id="now" aria-live="polite"></p><button type="button" id="stop" hidden>Stop</button></div>
</main>
<aside id="board">
{{PANELS}}
{{STRIPS}}
</aside>
<script type="application/json" id="said">{{SAID}}</script>
<script>
const spans=[...document.querySelectorAll('.g')], panels=[...document.querySelectorAll('.panel')];
const board=document.getElementById('board'), strips=[...document.querySelectorAll('.strip')], thumbs=[...document.querySelectorAll('.strip button')];
const motion=matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth';
let cur=-1, pinned=false;
function show(g,scroll){
  if(g===cur)return; cur=g;
  const p=panels[g];
  spans.forEach(s=>s.classList.toggle('on',+s.dataset.g===g));
  panels.forEach(x=>x.hidden=x!==p);
  strips.forEach(x=>x.hidden=x.dataset.scene!==p.dataset.scene);
  thumbs.forEach(t=>{const on=+t.dataset.g===g; t.classList.toggle('on',on); if(on)t.setAttribute('aria-current','true'); else t.removeAttribute('aria-current');});
  board.scrollTop=0;
  if(scroll){const s=spans.find(s=>+s.dataset.g===g); if(s)s.scrollIntoView({block:'center',behavior:motion});}
}
function pin(g){spans.forEach(x=>x.classList.toggle('pin',pinned&&+x.dataset.g===g));}
function activate(s){const g=+s.dataset.g; if(onBox.checked){pinned=true; show(g); pin(g); play(s.dataset.s); return;} pinned=!(pinned&&cur===g); show(g); pin(g);}
spans.forEach(s=>{
  s.addEventListener('mouseenter',()=>{if(!pinned)show(+s.dataset.g)});
  s.addEventListener('focus',()=>show(+s.dataset.g));
  s.addEventListener('click',()=>activate(s));
  s.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault(); activate(s);}});
});
thumbs.forEach(t=>t.addEventListener('click',()=>{const g=+t.dataset.g; pinned=true; show(g,true); pin(g);}));
// Read aloud: the film's clip when the build matched it to the script's sentence, or else a system voice.
const said=JSON.parse(document.getElementById('said').textContent), SLACK={{SLACK}};
const tts=window.speechSynthesis, vSel=document.getElementById('voice'), rSel=document.getElementById('rate');
const onBox=document.getElementById('speak'), bar=document.getElementById('bar'), now=document.getElementById('now'), stopBtn=document.getElementById('stop');
let voices=[], reading=null, clip=null, run=0;
const order=Object.keys(said);
// Where each shot group starts inside a sentence, as a fraction of the sentence's text, so playback can move the shots.
const starts={};
for(const id of order){
  const parts=spans.filter(s=>s.dataset.s===id), total=parts.reduce((n,s)=>n+s.textContent.length,0)||1;
  let at=0; starts[id]=parts.map(s=>{const m={f:at/total,g:+s.dataset.g}; at+=s.textContent.length; return m;});
}
function follow(id,f){
  const marks=starts[id]; if(!marks||!marks.length)return;
  let g=marks[0].g; for(const m of marks)if(m.f<=f)g=m.g;
  if(g!==cur){show(g,true); pin(g);}
}
// The bar sits at the foot of the narration pane, so the reason for a fallback stays in view wherever the reader is.
function status(text){now.textContent=text; bar.classList.toggle('live',!!text); stopBtn.hidden=!text;}
function stop(){run++; reading=null; if(clip){clip.pause(); clip=null;} if(tts)tts.cancel(); status('');}
stopBtn.onclick=stop;
function setOn(on){onBox.checked=on; vSel.disabled=rSel.disabled=!on; if(!on)stop();}
onBox.onchange=()=>{localStorage.setItem('sbSpeak',onBox.checked?'1':'0'); setOn(onBox.checked);};
setOn(localStorage.getItem('sbSpeak')==='1');
rSel.value=localStorage.getItem('sbRate')||'1';
rSel.onchange=()=>{localStorage.setItem('sbRate',rSel.value); if(clip)clip.playbackRate=+rSel.value;};
vSel.onchange=()=>localStorage.setItem('sbVoice',vSel.value);
function loadVoices(){
  voices=tts.getVoices().filter(v=>v.lang.startsWith('en')).sort((a,b)=>a.name.localeCompare(b.name));
  if(!voices.length)return;
  vSel.innerHTML=voices.map(v=>`<option>${v.name}</option>`).join('');
  const want=localStorage.getItem('sbVoice'), pick=voices.find(v=>v.name===want)||voices.find(v=>v.name==='Samantha')||voices.find(v=>v.lang==='en-US')||voices[0];
  vSel.value=pick.name;
}
if(tts){loadVoices(); tts.onvoiceschanged=loadVoices;} else document.getElementById('voice-field').hidden=true;
function play(id){if(!said[id]||!onBox.checked)return; stop(); read(id, run);}
// Each sentence hands on to the next when it ends; stop() bumps run, so a late end event from a stopped sentence does nothing.
function next(id,r){if(r!==run)return; const n=order[order.indexOf(id)+1]; if(n)read(n,r); else stop();}
function read(id,r){
  const s=said[id]; reading=id; follow(id,0);
  if(!s.src)return speak(id,r);
  const a=clip=new Audio(s.src);
  a.defaultPlaybackRate=a.playbackRate=+rSel.value;
  // A clip voiced again after the build has another length, so it never plays against this page's text.
  a.onloadedmetadata=()=>{if(Math.abs(a.duration-s.seconds)>SLACK)fallback(id,a,'its clip changed after this page was built',r);};
  a.onerror=()=>fallback(id,a,'its clip is missing',r);
  a.ontimeupdate=()=>{if(clip===a&&a.duration)follow(id,a.currentTime/a.duration);};
  a.onended=()=>{if(clip===a){clip=null; next(id,r);}};
  a.play().catch(()=>{});
  status(`Playing ${id} from the film's narration. Click anywhere to stop.`);
}
function fallback(id,a,why,r){a.pause(); if(clip!==a)return; clip=null; delete said[id].src; said[id].why=why; speak(id,r);}
function speak(id,r){
  const s=said[id];
  if(!tts){reading=null; status(`This browser has no system voice to read ${id}.`); return;}
  const u=new SpeechSynthesisUtterance(s.text);
  u.voice=voices.find(v=>v.name===vSel.value)||null; u.rate=+rSel.value;
  u.onboundary=e=>{if(r===run)follow(id,e.charIndex/s.text.length);};
  u.onend=()=>{if(r===run&&!clip)next(id,r);};
  tts.speak(u);
  status(`Reading ${id} in a system voice`+(s.why?`, because ${s.why}.`:'.')+' Click anywhere to stop.');
}
// While the page reads, the next click anywhere stops it and does nothing else; the voice and speed controls stay usable.
document.addEventListener('click',e=>{if(reading===null||e.target.closest('#tts'))return; e.preventDefault(); e.stopPropagation(); stop();},true);
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){stop(); return;}
  if((e.key!=='ArrowDown'&&e.key!=='ArrowUp')||e.target.closest('select,input'))return; e.preventDefault();
  const n=Math.max(0,Math.min(panels.length-1,cur+(e.key==='ArrowDown'?1:-1)));
  pinned=true; show(n,true); pin(n);
});
if(panels.length)show(0);
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path)
    ap.add_argument("--language", required=True, help="the script's language code, such as pt")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--key-script", type=Path, help="validate translated sentence counts")
    ap.add_argument("--key-language", help="the --key-script's language code")
    ap.add_argument("--css", type=Path, help="stylesheet to load after the defaults")
    ap.add_argument("--audio", type=Path, metavar="AUDIO_DIR", help="narrate_film.py output whose matching clips the page plays")
    args = ap.parse_args()
    if args.key_script and not args.key_language:
        ap.error("--key-script needs --key-language")
    css = os.path.relpath(args.css, args.out.parent) if args.css else None
    page, errors, groups, said = build(args.script, css, args.language, args.key_script, args.key_language,
                                       args.audio, args.out.parent)
    # Image paths are written relative to the script, so the page must sit beside it.
    if args.out.resolve().parent != args.script.resolve().parent and "<img" in page:
        errors.append("--out must be in the script's folder, because image paths are relative to the script")
    args.out.write_text(page)
    print(f"{args.out}: {groups} phrase groups")
    missing = sorted({src for _, src in IMAGE.findall(args.script.read_text()) if not (args.script.parent / src).is_file()})
    if missing:
        print(f"frames: {len(missing)} not drawn yet: {', '.join(missing)}")
    if args.audio:
        print(f"audio: {sum('src' in s for s in said.values())} of {len(said)} sentences play their clip from {args.audio}")
        for sid, s in said.items():
            if "why" in s:
                print(f"audio: {sid} falls back to a system voice, because {s['why']}")
    for e in errors:
        print("error:", e, file=sys.stderr)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        sys.exit(str(exc))
