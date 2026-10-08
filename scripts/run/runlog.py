#!/usr/bin/env python3
"""Spend and active time for Claude Code sessions, from their transcript usage records.

  runlog.py cost SESSION... [--from ISO] [--to ISO] [--by-agent] [--json]
  runlog.py mark RUN_STATE.md PHASE SESSION... [--note TEXT]

`cost` adds up the lead and every subagent of each session, optionally inside a UTC window.
`mark` appends a row to the "## Run log" table in RUN_STATE.md, creating it with a start row on
first use, so each row shows spend and active time since the start.

Costs use the list prices below and may differ from contract rates. Streamed records can
undercount output tokens. Active time is the sum of gaps between transcript events that are
shorter than IDLE, so overnight pauses don't count.
"""
import argparse, datetime as dt, glob, json, os, re, sys

PROJECTS = os.path.expanduser("~/.claude/projects")
# USD per million tokens: input, output, cache write, cache read.
PRICES = {"opus": (5, 25, 6.25, 0.50), "fable": (5, 25, 6.25, 0.50), "sonnet": (3, 15, 3.75, 0.30), "haiku": (1, 5, 1.25, 0.10)}
IDLE = 1800  # seconds; long enough that a silent full render still counts as work


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def iso(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def price(model):
    return next((v for k, v in PRICES.items() if k in (model or "")), PRICES["opus"])


def session_files(sid):
    mains = glob.glob(f"{PROJECTS}/*/{sid}*.jsonl")
    if len(mains) != 1:
        sys.exit(f"session {sid}: expected one transcript, found {len(mains)}")
    main = os.path.realpath(mains[0])
    full = os.path.basename(main)[:-6]
    subs = glob.glob(f"{main[:-6]}/**/*.jsonl", recursive=True)
    # Background agents also stream to the harness task folder.
    subs += glob.glob(f"/private/tmp/claude-*/*/{full}/tasks/*.output")
    return main, sorted({os.path.realpath(f) for f in subs} - {main})


def first_prompt(m):
    c = m.get("content")
    if isinstance(c, str):
        return c
    return next((b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text"), "")


def load(sids, start=None, end=None):
    """Return per-file usage (deduped on message id, last record wins) and event times inside the window."""
    calls, times, labels = {}, [], {}
    for sid in sids:
        main, subs = session_files(sid)
        for f in [main] + subs:
            role = "lead" if f == main else "subagent"
            try:
                fh = open(f, errors="ignore")
            except FileNotFoundError:
                continue  # removed between listing and reading
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(d, dict):
                    continue
                m = d.get("message")
                if f not in labels and role == "subagent" and isinstance(m, dict) and m.get("role") == "user":
                    labels[f] = first_prompt(m)[:70].replace("\n", " ")
                t = parse_ts(d.get("timestamp"))
                if t is None or (start and t < start) or (end and t > end):
                    continue
                times.append(t)
                if isinstance(m, dict) and m.get("usage") and m.get("id"):
                    calls[m["id"]] = (m["usage"], m.get("model"), f, role)
    return calls, sorted(times), labels


def dollars(u, model):
    pi, po, pw, pr = price(model)
    return (u.get("input_tokens", 0) * pi + u.get("output_tokens", 0) * po
            + (u.get("cache_creation_input_tokens") or 0) * pw + (u.get("cache_read_input_tokens") or 0) * pr) / 1e6


def active_seconds(times):
    return sum(g for g in ((b - a).total_seconds() for a, b in zip(times, times[1:])) if g <= IDLE)


def summarize(sids, start=None, end=None):
    calls, times, labels = load(sids, start, end)
    out = {"lead": 0.0, "subagent": 0.0, "by_file": {}, "models": {}, "calls": len(calls)}
    for u, model, f, role in calls.values():
        c = dollars(u, model)
        out[role] += c
        out["by_file"][f] = out["by_file"].get(f, 0) + c
        key = re.sub(r"-\d{8}$", "", model or "unknown")
        out["models"][key] = out["models"].get(key, 0) + c
    out["total"] = out["lead"] + out["subagent"]
    out["active_s"] = active_seconds(times)
    out["first"], out["last"] = (iso(times[0]), iso(times[-1])) if times else (None, None)
    out["labels"] = labels
    return out


def hm(seconds):
    return f"{int(seconds // 3600)}h{int(seconds % 3600 // 60):02d}m"


def cmd_cost(a):
    s = summarize(a.sessions, parse_ts(a.start), parse_ts(a.end))
    if a.json:
        s = {k: v for k, v in s.items() if k not in ("by_file", "labels")}
        print(json.dumps(s, indent=1))
        return
    print(f"spend ${s['total']:.2f} (lead ${s['lead']:.2f}, subagents ${s['subagent']:.2f}) over {s['calls']} API calls")
    print(f"active {hm(s['active_s'])} between {s['first']} and {s['last']}")
    print("models: " + ", ".join(f"{k} ${v:.2f}" for k, v in sorted(s["models"].items(), key=lambda x: -x[1])))
    if a.by_agent:
        for f, c in sorted(s["by_file"].items(), key=lambda x: -x[1]):
            print(f"  ${c:7.2f}  {s['labels'].get(f, 'lead')}")


ROW = re.compile(r"^\| (\S+Z) \| ([^|]+?) \| \$([\d.]+) \|")
HEADER = "## Run log\n\n| UTC | Phase | Session total | Since start | Active since start | Note |\n|---|---|---|---|---|---|\n"


def cmd_mark(a):
    now = dt.datetime.now(dt.timezone.utc)
    text = open(a.run_state).read() if os.path.exists(a.run_state) else ""
    total = summarize(a.sessions)["total"]
    lines = text.splitlines(keepends=True)
    rows = [i for i, l in enumerate(lines) if ROW.match(l)]
    if "## Run log" not in text:
        note = f"sessions {' '.join(a.sessions)}" + (f"; {a.note}" if a.note else "")
        row = f"| {iso(now)} | start | ${total:.2f} | $0.00 | 0h00m | {note} |\n"
        lines = [text.rstrip("\n") + ("\n\n" if text else ""), HEADER, row]
    else:
        start = ROW.match(lines[rows[0]])
        active = summarize(a.sessions, parse_ts(start.group(1)))["active_s"]
        row = f"| {iso(now)} | {a.phase} | ${total:.2f} | ${total - float(start.group(3)):.2f} | {hm(active)} | {a.note} |\n"
        # Insert after the last table row so text after the table stays below it.
        lines.insert(rows[-1] + 1, row)
    open(a.run_state, "w").write("".join(lines))
    print(row, end="")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("cost")
    c.add_argument("sessions", nargs="+", help="session ids or unique prefixes")
    c.add_argument("--from", dest="start")
    c.add_argument("--to", dest="end")
    c.add_argument("--by-agent", action="store_true")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_cost)
    m = sub.add_parser("mark")
    m.add_argument("run_state")
    m.add_argument("phase", help="script, voice, build, first-render, revision-N, accepted, ...")
    m.add_argument("sessions", nargs="+")
    m.add_argument("--note", default="")
    m.set_defaults(func=cmd_mark)
    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
