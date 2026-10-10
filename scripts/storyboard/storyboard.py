#!/usr/bin/env python3
"""Build a hover storyboard from a script, so a reader can check each planned picture against the words it lands on.

  storyboard.py SCRIPT.md --out storyboard.html [--css BRAND.css]

SCRIPT.md has the `## Scene N: title` sections that cues.py reads, each with a `**Narration**` part and then a
`**Visual**` part. Every list item in the Visual part is one shot, and so is any other Visual paragraph that holds a
cue. A shot's cue is its first quoted span, written `On "words"` or `**"words"**`, and must be consecutive words of
that scene's narration. Words compare as in cues.py. A shot without a cue follows the shot above it. Markdown images
in a shot, `![what it shows](path)`, become its key frames; give the path relative to SCRIPT.md.

The page shows the narration on the left. Hovering a phrase shows the shots that start on it, clicking pins it, and
the arrow keys step through. --css adds a stylesheet after the defaults, so a brand can override the variables in
:root. The run exits 1 when a scene has no Narration part or a cue isn't in its scene's narration.
"""
import argparse, html, os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audio"))
from cues import CUE, SCENE, VISUAL, norm  # noqa: E402

NARRATION = re.compile(r"\*\*Narration\.?\*\*")
ITEM = re.compile(r"^(\s*)(?:\d+\.|[-*])\s+(.*)")
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")


def inline(md):
    s = html.escape(re.sub(r"[ \t]+", " ", IMAGE.sub("", md)).strip(), quote=False)
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
    """Each word with its normalized form and its character span in text."""
    return [(norm(m.group()), m.start(), m.end()) for m in re.finditer(r"\S+", text) if norm(m.group())]


def find(words, quote, start):
    toks = [norm(t) for t in quote.split() if norm(t)]
    for lo in (start, 0):
        for i in range(lo, len(words) - len(toks) + 1):
            if all(words[i + k][0] == toks[k] for k in range(len(toks))):
                return i
    return None


def build(script, css):
    text = script.read_text()
    title = (re.search(r"^# (.+)$", text, re.M) or [None, script.stem])[1]
    errors, left, panels = [], [], []
    for m in SCENE.finditer(text):
        num, body = int(m.group(1)), m.group(0)
        heading = body.splitlines()[0].split(":", 1)[1].strip()
        parts = NARRATION.split(body, 1)
        if len(parts) < 2:
            errors.append(f"scene {num}: no **Narration** part")
            continue
        narration, *visual = VISUAL.split(parts[1], 1)
        narration, visual = narration.strip(), "".join(visual)
        words = words_of(narration)
        groups, cursor = [], 0  # each group: [start word index, [shots]]
        for shot in shots_of(visual):
            quote = CUE.search(shot)
            at = find(words, quote.group(1), cursor) if quote else None
            if quote and at is None:
                errors.append(f'scene {num}: cue not in narration: "{quote.group(1)}"')
            if at is None:
                if not groups:
                    groups.append([0, []])
                groups[-1][1].append((None, shot))
                continue
            cursor = at
            hit = next((g for g in groups if g[0] == at), None)
            if hit:
                hit[1].append((quote.group(1), shot))
            else:
                groups.append([at, [(quote.group(1), shot)]])
        groups.sort(key=lambda g: g[0])
        if groups:
            groups[0][0] = 0
        else:
            groups = [[0, []]]

        left.append(f"<h2><span>Scene {num}</span>{html.escape(heading)}</h2>")
        bounds = [words[g[0]][1] if words else 0 for g in groups] + [len(narration)]
        bounds[0] = 0
        paras, cur = [], []
        for k, (_, shots) in enumerate(groups):
            gid = len(panels)
            for j, piece in enumerate(re.split(r"\n\s*\n", narration[bounds[k]:bounds[k + 1]])):
                if j:
                    paras.append("".join(cur))
                    cur = []
                if piece.strip():
                    cur.append(f'<span class="g" data-g="{gid}" tabindex="0">{inline(piece)} </span>')
            cards = []
            for cue, shot in shots:
                frames = "".join(
                    f'<figure><img src="{html.escape(src)}" alt="{html.escape(alt)}" loading="lazy">'
                    f"<figcaption>{html.escape(alt)}</figcaption></figure>"
                    for alt, src in IMAGE.findall(shot))
                frames = f'<div class="frames">{frames}</div>' if frames else '<div class="todo">Not drawn yet</div>'
                label = f"“{html.escape(cue)}”" if cue else "No cue · follows the shot above"
                cards.append(f'<article><div class="cue{"" if cue else " none"}">{label}</div>{frames}<p>{inline(shot)}</p></article>')
            panels.append(f'<div class="panel" data-p="{gid}" hidden><div class="sc">Scene {num}</div>'
                          f'{"".join(cards) or "<p class=none>No shots on this phrase.</p>"}</div>')
        paras.append("".join(cur))
        left.extend(f"<p>{p}</p>" for p in paras if p)
    if not left:
        errors.append("no `## Scene N: title` sections found")
    style = f'<link rel="stylesheet" href="{html.escape(css)}">' if css else ""
    page = (PAGE.replace("{{TITLE}}", html.escape(title)).replace("{{CSS}}", style)
            .replace("{{SCRIPT}}", html.escape(script.name)).replace("{{LEFT}}", "\n".join(left))
            .replace("{{PANELS}}", "\n".join(panels)))
    return page, errors, len(panels)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}} · storyboard</title>
<style>
:root{--font:system-ui,sans-serif;--mono:ui-monospace,monospace;--ink:#1c1c1c;--paper:#fff;--panel:#f4f4f2;--muted:#6b6b6b;--rule:#d4d4d0;--accent:#2b4c7e;--hover:#e3e9f3;--pin:#c9d5e8;--frame:#111}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--paper);color:var(--ink);font-family:var(--font);font-size:18px;line-height:1.55;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.15fr)}
#script{overflow-y:auto;height:100vh;padding:28px 40px 50vh;border-right:1px solid var(--rule)}
header{font-size:14px;color:var(--muted)}
header h1{font-size:30px;font-weight:400;color:var(--ink);line-height:1.15;margin:0 0 6px}
h2{font-weight:400;font-size:20px;margin:40px 0 10px;border-bottom:1px solid var(--ink);padding-bottom:4px}
h2 span{font-family:var(--mono);font-size:13px;color:var(--muted);margin-right:10px}
p{margin:0 0 14px}
.g{cursor:pointer;border-radius:3px;outline:none}
.g:hover,.g.on{background:var(--hover);box-shadow:0 2px 0 var(--accent)}
.g.pin{background:var(--pin)}
#board{overflow-y:auto;height:100vh;padding:28px 36px 40px;background:var(--panel)}
.sc{font-family:var(--mono);font-size:13px;color:var(--muted);margin-bottom:12px}
article{background:var(--paper);border:1px solid var(--rule);padding:14px;margin-bottom:16px}
article p{margin:10px 0 0;font-size:16px;line-height:1.45}
.cue{font-size:15px;color:var(--accent);margin-bottom:8px}
.none{color:var(--muted);font-style:italic}
.frames{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(160px,1fr))}
figure{margin:0}
figure img{width:100%;aspect-ratio:16/9;object-fit:contain;display:block;background:var(--frame)}
figcaption{font-size:12px;color:var(--muted);margin-top:2px}
.todo{aspect-ratio:16/9;max-height:200px;border:1.5px dashed var(--muted);color:var(--muted);display:flex;align-items:center;justify-content:center;font-size:14px}
code{font-family:var(--mono);font-size:.88em}
</style>
{{CSS}}
</head>
<body>
<main id="script">
<header><h1>{{TITLE}}</h1>Built from {{SCRIPT}}. Hover a phrase to see its shots, click to pin it, and use the arrow keys to step.</header>
{{LEFT}}
</main>
<aside id="board">
{{PANELS}}
</aside>
<script>
const spans=[...document.querySelectorAll('.g')], panels=[...document.querySelectorAll('.panel')];
let cur=-1, pinned=false;
function show(g,scroll){
  if(g===cur)return; cur=g;
  spans.forEach(s=>s.classList.toggle('on',+s.dataset.g===g));
  panels.forEach(p=>p.hidden=+p.dataset.p!==g);
  document.getElementById('board').scrollTop=0;
  if(scroll){const s=spans.find(s=>+s.dataset.g===g); if(s)s.scrollIntoView({block:'center',behavior:'smooth'});}
}
function pin(g){spans.forEach(x=>x.classList.toggle('pin',pinned&&+x.dataset.g===g));}
spans.forEach(s=>{
  s.addEventListener('mouseenter',()=>{if(!pinned)show(+s.dataset.g)});
  s.addEventListener('focus',()=>show(+s.dataset.g));
  s.addEventListener('click',()=>{const g=+s.dataset.g; pinned=!(pinned&&cur===g); show(g); pin(g);});
});
document.addEventListener('keydown',e=>{
  if(e.key!=='ArrowDown'&&e.key!=='ArrowUp')return; e.preventDefault();
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
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--css", type=Path, help="stylesheet to load after the defaults")
    args = ap.parse_args()
    css = os.path.relpath(args.css, args.out.parent) if args.css else None
    page, errors, groups = build(args.script, css)
    # Image paths are written relative to the script, so the page must sit beside it.
    if args.out.resolve().parent != args.script.resolve().parent and "<img" in page:
        errors.append("--out must be in the script's folder, because image paths are relative to the script")
    args.out.write_text(page)
    print(f"{args.out}: {groups} phrase groups")
    for e in errors:
        print("error:", e, file=sys.stderr)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
