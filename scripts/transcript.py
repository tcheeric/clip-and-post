#!/usr/bin/env python3
"""Fetch a YouTube video's metadata + captions and emit clean, deduplicated cues.

Auto-captions arrive as a rolling window: each cue repeats the tail of the
previous one, so a naive parse yields ~4x duplicated text that is useless for
locating boundaries. This strips the markup, drops repeats, and prints one
line per new utterance with both absolute seconds and HH:MM:SS.

Usage:
  transcript.py URL                       # metadata + full cue list
  transcript.py URL --lang fr             # force a caption language
  transcript.py URL --grep 'pause|moratoire'
  transcript.py URL --window 9:50 14:36   # only cues in a time range
  transcript.py URL --window 9:50 14:36 --bucket 15   # grouped, for skimming
"""
import argparse, json, re, subprocess, sys, tempfile, os, glob

YTDLP = ["uvx", "yt-dlp@latest"]
# A JS runtime is required or YouTube silently withholds most formats.
RUNTIME_FLAGS = ["--js-runtimes", "node,bun,deno"]


def tc(s):
    """'9:50' / '00:09:50' / '590' -> seconds."""
    s = str(s).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    parts = [float(p) for p in s.split(":")]
    out = 0.0
    for p in parts:
        out = out * 60 + p
    return out


def hms(sec):
    sec = int(sec)
    return f"{sec//3600:02d}:{sec%3600//60:02d}:{sec%60:02d}"


def run(args):
    return subprocess.run(args, capture_output=True, text=True)


def probe(url):
    r = run([*YTDLP, *RUNTIME_FLAGS, "--skip-download",
             "--print", "%(title)s", "--print", "%(duration)s",
             "--print", "%(uploader)s", "--print", "%(language)s",
             "--print", "%(chapters)j", url])
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    if len(lines) < 5:
        sys.exit(f"probe failed:\n{r.stderr[-1500:]}")
    title, dur, uploader, lang, chapters = lines[-5:]
    try:
        chapters = json.loads(chapters)
    except Exception:
        chapters = None
    return dict(title=title, duration=float(dur or 0), uploader=uploader,
                language=(lang if lang not in ("NA", "None", "") else None),
                chapters=chapters)


def fetch_cues(url, lang):
    with tempfile.TemporaryDirectory() as td:
        r = run([*YTDLP, *RUNTIME_FLAGS, "--skip-download",
                 "--write-auto-subs", "--write-subs", "--sub-langs", lang,
                 "--sub-format", "vtt", "-o", os.path.join(td, "s.%(ext)s"), url])
        hits = glob.glob(os.path.join(td, "*.vtt"))
        if not hits:
            sys.exit(f"no captions for lang={lang}:\n{r.stderr[-1500:]}")
        raw = open(hits[0], encoding="utf-8").read()

    cues, ts, seen, out = [], None, set(), []
    for line in raw.splitlines():
        m = re.match(r"(\d\d:\d\d:\d\d)\.\d+ --> ", line)
        if m:
            ts = m.group(1)
            continue
        if ts and line.strip():
            t = re.sub(r"<[^>]+>", "", line).strip()
            if t:
                cues.append((ts, t))
    for ts, t in cues:
        if t in seen:
            continue
        seen.add(t)
        out.append((tc(ts), t))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--lang")
    ap.add_argument("--grep")
    ap.add_argument("--window", nargs=2, metavar=("START", "END"))
    ap.add_argument("--bucket", type=int, default=0,
                    help="group cues into N-second buckets (skim mode)")
    ap.add_argument("--offset", default="0",
                    help="subtract this from printed times (clip-relative output)")
    a = ap.parse_args()

    meta = probe(a.url)
    lang = a.lang or meta["language"] or "en"
    print(f"# title     {meta['title']}")
    print(f"# uploader  {meta['uploader']}")
    print(f"# duration  {hms(meta['duration'])}")
    print(f"# language  {lang}" + ("" if a.lang else "  (auto-detected)"))
    if meta["chapters"]:
        print("# chapters:")
        for c in meta["chapters"]:
            print(f"#   {hms(c['start_time'])}-{hms(c['end_time'])}  {c['title']}")
    else:
        print("# chapters  none - locate segments from the cues below")
    print()

    cues = fetch_cues(a.url, lang)
    off = tc(a.offset)
    lo, hi = (tc(a.window[0]), tc(a.window[1])) if a.window else (0, 10**9)
    pat = re.compile(a.grep, re.I) if a.grep else None

    sel = [(s, t) for s, t in cues if lo <= s <= hi and (not pat or pat.search(t))]
    if a.bucket:
        buf = {}
        for s, t in sel:
            buf.setdefault(int(s) // a.bucket * a.bucket, []).append(t)
        for k in sorted(buf):
            print(f"{k-off:>7.0f}s  {hms(k-off)}  {' '.join(buf[k])}")
    else:
        for s, t in sel:
            print(f"{s-off:>7.0f}s  {hms(s-off)}  {t}")


if __name__ == "__main__":
    main()
