#!/usr/bin/env python3
"""Fetch an article and extract its text without corrupting the wording.

  article.py URL                     # fetch, save article.html, print text
  article.py URL --verify quote.txt  # also check the quote appears verbatim
  article.py --file article.html     # re-extract from an already-saved page

Why this exists rather than a sed one-liner: replacing every tag with a space
breaks words apart. `<a>Bitcoin Core</a>’s` becomes "Bitcoin Core ’s", so a
correctly copied quote fails a verbatim check and the tempting fix is to corrupt
the quote to match. Block-level tags become newlines, inline tags become nothing.
"""
import argparse, html, pathlib, re, sys, urllib.request

BLOCK = ("p div br hr li ul ol dl dt dd h1 h2 h3 h4 h5 h6 blockquote pre "
         "section article header footer aside nav main figure figcaption "
         "table tr td th tbody thead form").split()
BLOCK_RE = re.compile(r"(?is)</?(?:%s)\b[^>]*>" % "|".join(BLOCK))


def fetch(url, out="article.html"):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (clip-and-post)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    enc = r.headers.get_content_charset() or "utf-8"
    text = raw.decode(enc, errors="replace")
    pathlib.Path(out).write_text(text)
    return text


def extract(doc):
    doc = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", doc)
    doc = re.sub(r"(?s)<!--.*?-->", " ", doc)
    doc = BLOCK_RE.sub("\n", doc)          # block tags -> line break
    doc = re.sub(r"(?s)<[^>]+>", "", doc)  # inline tags -> nothing at all
    doc = html.unescape(doc)
    doc = re.sub(r"[ \t ]+", " ", doc)
    doc = re.sub(r" *\n *", "\n", doc)
    return re.sub(r"\n{3,}", "\n\n", doc).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--file")
    ap.add_argument("--verify", help="file holding the excerpt to check")
    a = ap.parse_args()

    doc = pathlib.Path(a.file).read_text(errors="replace") if a.file else fetch(a.url)
    text = extract(doc)

    if a.verify:
        quote = pathlib.Path(a.verify).read_text().strip()
        flat = lambda s: re.sub(r"\s+", " ", s).strip()
        if flat(quote) in flat(text):
            print("VERBATIM — safe to publish", file=sys.stderr)
        else:
            print("NOT FOUND — do not publish.", file=sys.stderr)
            print("The quote is not in the source as written. Fix the quote to "
                  "match the article, never the article to match the quote.", file=sys.stderr)
            sys.exit(1)
    else:
        print(text)


if __name__ == "__main__":
    main()
