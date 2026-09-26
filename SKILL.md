---
name: clip-and-post
description: Turn a YouTube video into a publish-ready clip, or an article into a NIP-84 quote highlight, and publish it to Nostr after approval. Use whenever someone gives a YouTube URL and wants a clip, an excerpt, a highlight, "the interesting bit", a segment cut out, something trimmed for social, or a post drafted from a video; or gives an article, blog post or news URL and wants a quote, a pull-quote, a highlight, or the key passage posted. Also use when asked to find where a named topic is discussed in a long talk, podcast, lecture, interview or livestream, to pull a quote or moment out of a video or a piece of writing, or to compress something long down to its substance. It always lists the topics first, saves them to topics.txt and asks which topic or angle to process, with a recommendation; with --topics, or when asked only what a video or article covers, it stops after the list. Reach for it as soon as a URL appears alongside ffmpeg, yt-dlp, transcripts, timestamps, subtitles, "extract", "highlight", "quote", "schedule" or "post later" — the failure modes below are silent and will waste a long download or publish a misquote if you improvise instead.
---

# Clip and post

Two kinds of source, two kinds of event, one publishing spine.

- **A video** becomes a cut, faded clip and a **kind 1** note (branch A).
- **An article** becomes a **kind 9802** NIP-84 quote highlight (branch B).

Both branches end in the same place: draft, build the event, get approval, publish,
verify. Only the middle differs, and it differs completely — so read the branch you
need and ignore the other.

**The two branches have opposite rules about quoting, and both are right.** Video
captions are machine transcription and must never be quoted verbatim; article text
is what the author actually wrote and a highlight must be *exactly* verbatim. Do not
carry a habit from one branch into the other.

## Which branch

A YouTube or video URL → branch A. Any other page with prose on it → branch B. If
the input is a video *of* an article, or an article *about* a video, ask which one
they mean rather than guessing; the output kinds are different and only one is right.

## The flow: topics first, then the person picks

Every run follows the same order, for both branches:

1. **Read and map.** Run only the read step (**A1** for a video, **B1** for an
   article, or the Reader document when that is the source), then list the topics
   and arguments (format below). Show the list and save it as `topics.txt`.
2. **Ask, in plain text, which topic or angle to process.** End the list with
   your recommendation and one or two alternatives, a line each on why, then ask
   what they'd like. Don't open a fixed-choice picker: people usually come with an
   editorial angle ("how the numbers don't add up", "what the foot-to-glute
   connection is") rather than a topic number, and the best clip often draws on
   several topics. Recommend what stands alone and holds an argument, not an
   introduction, promotion or someone's family story.
3. **Process the chosen topic or angle.** Carry on from **A2** (clip) or **B2**
   (excerpt). A topic number gives the outer boundary; an angle means finding the
   stretches that make that point, across topics if need be, and saying which you
   took. Use the text already in hand. Nothing is fetched twice.
4. **Then the rest as usual:** draft, approval of the text, upload, full event,
   explicit yes, publish, verify.

Two exceptions:

- **The request already names the topic or angle** ("clip the part about X").
  Still list and save the topics, then go ahead without asking and say which
  topics you drew on, so a wrong match is easy to correct.
- **`--topics` in the arguments** means map only: do step 1, then stop instead of
  asking. No download, no cut, no draft, no upload, no event.

This order is cheap on purpose: the text is what every later choice is made from,
so the map costs seconds and the person picks the segment or passage before
anything slow or public happens.

### The topic list

**Save it as `topics.txt`** in the item's folder under `<output>/<slug>/` (see
*collect the output*), as well as showing it. Head it with the title, source URL,
uploader or publication, duration or length, language (and caption track), the
date, and any caveats (mangled names, paywall), then the numbered list, then your
recommended candidates. The clip or highlight goes into the same folder, next to it.

List each distinct topic or argument in the order it appears:

```
1. 01:22–02:22  The proposal: raising a child as a condition to run for president
2. 02:22–03:40  Candidates without children, and the digs at Macron   (name-list)
3. 04:00–07:40  "Childfree" as a label and a market                    (digression)
```

- **Position:** a timestamp range for a video, taken from the cues; for an article,
  the section heading if it has one, else paragraph numbers. For videos over about
  30 minutes, read with `--bucket 30`; the finer pinning happens in A2 anyway.
- **One line, in your own words, in the source's language.** On a video this is a
  paraphrase of auto-captions, so the paraphrase rule below applies here too. On an
  article, don't quote; a topic line is not a highlight and has not been verified.
- **Label what isn't argument:** sponsor reads, housekeeping, name-lists,
  digressions, promotion, third parties' private lives, and the pivot from
  checkable claim into opinion. Those are what the inner cuts usually drop, so
  marking them now saves the person a question later.
- **Chapters, if the video has them,** are the uploader's own map. List them as
  given, and add a topic only where a chapter clearly holds two.
- **Say what you couldn't see.** A paywalled article or a missing caption track
  limits the list to what was readable; say so rather than listing topics you didn't
  read.

---

# Branch A — video → kind 1

The whole design rests on one asymmetry: **captions are tiny and instant, video is
huge and slow.** A 90-minute talk's subtitle track is under a megabyte and arrives in
seconds; the video is hundreds of megabytes and can take many minutes on a slow or
VPN-routed link. So every decision about *what* to cut gets made from the text, and
video is downloaded exactly once, for exactly the range that survived that decision.
Getting this order wrong is the difference between a two-minute task and a
twenty-minute one.

## Prerequisites

`ffmpeg` and `ffprobe` must be present. For yt-dlp, **do not use a system install** —
distribution packages go stale within months and YouTube breaks stale extractors
constantly. Run it through `uvx yt-dlp@latest` (or `pipx run`).

A **JavaScript runtime must be available**, and *which* one matters more than the
skill used to admit. yt-dlp's EJS rejects older Node — Node v20 is refused with the
same "No supported JavaScript runtime could be found" warning you get with none at
all, which is the silent audio-only trap. **Probe before downloading:**

```bash
for rt in "deno" "bun:$(command -v bun)" "node:$(command -v node)"; do
  [ "${rt#*:}" = "" ] && continue
  if uvx yt-dlp@latest --js-runtimes "$rt" --simulate --quiet --print "%(id)s" "URL" 2>&1 \
     | grep -q "No supported JavaScript runtime"; then echo "$rt REJECTED"; else echo "$rt OK"; break; fi
done
```

Use the first runtime that comes back `OK` for every subsequent yt-dlp call. On a
machine with Node 20 and bun installed, that is bun.

## A1. Probe and read the transcript

```bash
scripts/transcript.py "URL" --bucket 20 > transcript.txt
```

This prints title, uploader, duration, detected language, and chapter list if the
video has one, then the full deduplicated cue list. `--bucket 20` groups cues into
20-second chunks, which is the right density for skimming a long video; drop it when
you need cue-level precision.

**If it says `no captions for lang=...`, the language is probably right but the track
name is wrong.** The metadata language can be `en-US` while the only real track is
`en-orig`. List what exists and pass it explicitly:

```bash
uvx yt-dlp@latest --js-runtimes "<working runtime>" --list-subs "URL"
scripts/transcript.py "URL" --lang en-orig --bucket 20 > transcript.txt
```

**If the video has chapters, trust them** — the uploader already told you where the
topics are, and chapter titles are clean text rather than machine transcription. Read
the titles, list them as the topics (see *The flow*). If the person picks a whole
chapter, skip to A3; if they give an angle, pin the stretches in A2 as usual. Check
the chapter times against the cues first: uploaders' chapters can be misaligned.

Most videos have no chapters. Then find candidate regions by searching the cues for
terms the topic would actually use:

```bash
scripts/transcript.py "URL" --grep 'pause|moratoire|régulation'
```

Search in the video's own language, not English.

## A2. Choose the segment, then its sub-segments

Two nested decisions, and they're different in kind.

**The outer boundary** is where a topic starts and stops. Look for the question that
opens it and the pivot that closes it — a moderator changing subject is an
unmistakable boundary marker. Give yourself a few seconds of lead-in so the clip
doesn't open mid-breath.

**The inner cuts** are what makes the clip worth watching rather than merely short.
Read the segment as an argument and find its beats: a claim, the evidence for it, the
conclusion — and, usually, a digression that supports none of them. Tangents,
name-lists, anecdotes that don't land, and throat-clearing are what you drop.

**Watch for the pivot from argument into opinion.** A speaker making a checkable
claim often slides into politics a minute later. Ending the clip at that pivot is
usually the difference between an explainer and a statement — say that you did it and
give the timestamp, so it can be overridden.

Be honest that "interesting" is a judgment call. State plainly which stretch you cut
and why — the person asking knows the material and you do not.

Then pin boundaries to the second using cue-level output, so cuts land on sentence
starts rather than mid-clause:

```bash
scripts/transcript.py "URL" --window 12:00 13:40
```

## A3. Download only the chosen range

```bash
uvx yt-dlp@latest --js-runtimes "<working runtime>" \
  --download-sections "*00:09:50-00:14:36" --force-keyframes-at-cuts \
  -f "bv*[height<=720]+ba/b[height<=720]" --merge-output-format mp4 \
  -o "segment-raw.%(ext)s" "URL"
```

`--force-keyframes-at-cuts` re-encodes at the boundaries so the range starts exactly
where you asked instead of at the nearest keyframe. Cap height at 720 unless asked
otherwise — it's a talking head destined for a phone screen, and it roughly halves
both download time and final size.

**Then immediately verify you got video:**

```bash
scripts/verify.sh segment-raw.mp4
```

## A4. Cut, fade, concatenate

```bash
scripts/cut.sh segment-raw.mp4 clip.mp4 0.7 3-128 208-285
```

Each `IN-OUT` pair is a sub-segment in seconds relative to `segment-raw.mp4`, and
decimals are fine. The script trims each one, fades it in and out, and concatenates —
in a single `filter_complex` pass, so there's one decode and one encode and no
temporary files.

Adjacent sub-segments that are genuinely continuous should be *one* range, not two —
fading across a sentence that was never interrupted looks broken. Only fade where you
actually removed something.

Tune with `CRF=` (higher is smaller, 26 is a good default) and `PRESET=`. Then verify
the fades landed, sampling either side of each join:

```bash
scripts/verify.sh clip.mp4 0 0.5 124.4 124.9 125.3 126 201.9
```

You want a clear dip toward 0 at the join and a recovery on both sides.

## A5. Check the clip fits the publishing cap

Hosts cap uploads, and the cap is enforced on the finished file, not on your estimate
of it. The binding one here is Blossom: `nostr-java-mcp` refuses a blob larger than
`nostr.mcp.blossom.max-blob-bytes` — **16 MiB (16,777,216 bytes) by default** — and it
refuses *before* contacting the server, because the bytes are buffered in memory to be
hashed first. So an oversized clip fails instantly at publish, long after the encode
is done and the post is written.

Target **14 MiB or under**, and measure rather than assume:

```bash
python3 -c "import os;b=os.path.getsize('clip.mp4');print(f'{b:,} bytes — {100*b/16777216:.0f}% of a 16 MiB cap')"
```

The budget is a bitrate, and duration spends it. Total kbps available is roughly
`115000 / duration_seconds` to land near 14 MiB — about 570 kbps for a 3-minute clip,
380 for 5 minutes, 190 for 10. Past five or six minutes at 720p you are fighting the
cap, and the honest fix is a shorter clip rather than a mushier one.

When it comes in over, try in this order — cheapest and least visible first:

1. **Raise `CRF=`.** 28–30 still looks fine for talking heads.
2. **Scale down** — `-vf scale=-2:540`. Text on slides is what suffers; check first.
3. **Shorten the clip.** Drop a sub-segment that was marginal anyway.

---

# Branch B — article → kind 9802 highlight

A highlight is a **verbatim quotation of someone else's writing, published under your
key**. Everything below exists because getting a character wrong turns it into a
misquote with your name on it.

## B1. Fetch the article, and keep the raw text

```bash
scripts/article.py "URL" > article.txt     # also saves article.html
```

Read `article.txt` to choose the excerpt, but treat `article.html` as the source of
truth — it is what the verify step checks against.

**Do not extract the text with a tag-stripping one-liner.** Replacing every tag with
a space splits words at inline markup: `<a>Bitcoin Core</a>’s` comes out as
`Bitcoin Core ’s`, so a correctly copied quote fails the verbatim check and the
tempting fix is to corrupt the quote to match the extractor. `article.py` maps
block-level tags to newlines and inline tags to nothing, which is the whole reason it
exists.

## B2. Choose the excerpt

One to three sentences. It has to stand alone — a reader seeing only the highlight
should get a complete thought, not a fragment that needs the paragraph around it.

Take the **claim**, not the setup and not the throat-clearing. The test is the same
as the inner cuts in branch A: if you removed the sentence, would the point survive?
Then it wasn't the point.

Do not stitch two distant sentences into one quotation. If both matter, either widen
the excerpt to include what is between them or publish two highlights. An ellipsis
spanning paragraphs is how a quote stops meaning what it meant.

## B3. Verify the excerpt is byte-for-byte in the source

**This is branch B's `verify.sh`, and it is not optional.** Put the excerpt in a file
and check it against the page you fetched:

```bash
scripts/article.py --file article.html --verify quote.txt
```

It exits non-zero and refuses on anything that is not an exact match, ignoring only
differences in whitespace runs.

If it fails, the usual cause is a typographic substitution — a straight quote for a
curly one, a hyphen for an em dash, a normal space for a non-breaking one. These
survive copy-paste looking identical. **Fix your copy to match the source, never the
other way around.** If it still fails, you paraphrased without meaning to; go back
to B2.

Also capture the surrounding paragraph for the `context` tag. The spec recommends it
whenever the highlight is part of a paragraph, and it is what stops a quote reading as
if it were the author's whole position.

## B4. Find the author's pubkey, if there is one

NIP-84 suggests parsing the document for a self-declared nostr identity:

```bash
grep -oiE 'nostr:(npub|nprofile)1[a-z0-9]+' article.html | sort -u
grep -oiE '<link[^>]+rel=["'"'"']me["'"'"'][^>]*>' article.html
```

If you find one, tag it `["p", "<hex>", "<relay>", "author"]`. If you don't, **do not
guess** — attributing a quote to the wrong key is worse than not attributing it. Name
the author in the comment text instead.

---

# Shared — collect the output

Everything a job produces lives together under the **output folder**, in one folder
per item. The folder is chosen when the skill is installed, and defaults to
`~/clip-and-post`. Read it first; never assume a path:

```bash
OUT=$(scripts/install.sh --print)   # exits 1 if never installed
```

If that fails, the skill was never installed: run `scripts/install.sh` (it asks for
the folder, defaulting to `~/clip-and-post`), or ask the person where they want the
output and pass it as `scripts/install.sh DIR`. Don't pick one silently.


```
<output>/<slug>/
├── topics.txt         the topic map, written first on every run
├── clip.mp4           branch A only: the finished, faded clip
├── article.html       branch B only: the source of truth for the quote
├── post.md            the drafted text, one heading per destination
└── nostr-event.json   the event, ready to publish
```

The `<slug>` is kebab-case and identifies the item on sight — speaker or publication
plus topic, e.g. `werner-banks-create-money`. Not the raw title. If the folder exists,
suffix it (`-2`) rather than overwriting.

Work in a scratch directory and copy the finished files in at the end. Intermediates
stay in scratch and are not part of the deliverable — scratch is usually under `/tmp`
and won't survive a reboot.

# Shared — draft the text

Write **in the language of the source**, which `transcript.py` reports for video and
the page's `lang` attribute gives for an article, unless the person asks for another
language. The community hashtag below follows the language of the post, not the source. A French source gets a French post,
written natively, not English phrasing rendered into French.

For branch A, offer two lengths: a longer one for LinkedIn/Facebook/Bluesky that can
carry the argument, and a short one for X/Mastodon/Threads. For branch B, the
platform text is the quote plus your comment.

**Tag the language community when posting to Nostr.** Nostr defaults to English, so
the non-English communities find each other by hashtag:

| Source language | Hashtag |
| --- | --- |
| French | `#nostrfr` |
| German | `#nostrde` |
| English | none |

English gets nothing — there is no `#nostren` convention, and inventing one adds noise
to the one audience that needs no help finding the post.

Three rules about tags:

- **They belong to the Nostr version only.** A `#nostrfr` on LinkedIn or X is clutter.
- **Put every tag in the text *and* in the event's `t` tags** — lowercase, no `#`, e.g.
  `["t","nostrfr"]`. Clients render a `#word` as a link, but relay-side discovery
  filters on `t` tags, so a hashtag that exists only in the text is invisible to anyone
  searching for it. Getting this half-right is the common failure: the post looks
  tagged and reaches nobody.
- **On branch B, hashtags go in the `comment`, never in `content`.** The content is a
  verbatim quotation; appending your hashtags to someone else's sentence falsifies it.

Then three things that protect the person posting:

- **Never quote auto-captions verbatim** (branch A). Machine transcription mangles
  proper nouns, and it will be a real person's name that's wrong. Paraphrase, and say
  your summary is a paraphrase to be checked against the clip.
- **Credit the source and link the original.** It's their recording, or their writing.
- **Say it's an excerpt.** A tight clip or a pulled quote invites the "out of context"
  reply; naming it as an excerpt defuses that before it arrives.

# Shared — build the event

Write it to `nostr-event.json` so the exact thing that will be signed can be read
before it is.

## Branch A — kind 1

**First upload the clip**, because the event has to reference a URL that already
works. Blossom returns the hosted URL, the sha256 and the byte count. The upload tool
takes a **URL, not a file path**, so a local clip has to be served over HTTP for the
server to fetch — on loopback, which needs
`nostr.mcp.blossom.allow-private-hosts=true` on that one invocation.

**Uploading is publishing.** The blob goes to public, hash-addressed servers the
moment you upload, before anyone has approved the post. So get approval on the text
*first*, then upload, then show the assembled event. If the answer is no, nothing has
left the machine.

**Read the real numbers off the file** rather than copying them from anywhere:

```bash
sha256sum clip.mp4; stat -c %s clip.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 clip.mp4
```

Content is the Nostr text with the blob URL on its own last line, paragraphs
unwrapped — hard line breaks from a draft file render as ragged text in clients. Tags:

- `imeta` (NIP-92) — `url`, `m video/mp4`, `x <sha256>`, `size <bytes>`, `dim <w>x<h>`.
  This is what makes a client render an inline player instead of a bare link.
- `t` — language community and subject tags, lowercase, no `#`.
- `r` — the original video URL.

Kind 1 and not a NIP-71 video event (21/22): support is far wider, and a landscape
excerpt is not a vertical short anyway.

## Branch B — kind 9802 (NIP-84 quote highlight)

`content` is the excerpt **and nothing else** — no framing, no hashtags, no ellipsis
you added. Your words go in the `comment` tag, which makes it a quote highlight and
renders like a quote repost, so one event does the job of a highlight plus a note.

Because there is a `comment`, NIP-84 switches on two MUST rules about tag attributes:

- the highlighted source URL takes **`source`**, not a bare `r`;
- anything the *comment* introduces — a mentioned pubkey, a URL you linked — takes
  **`mention`**, to keep it separate from the authors.

```json
{
  "kind": 9802,
  "content": "<the excerpt, byte-for-byte from the article>",
  "tags": [
    ["r", "<article url>", "source"],
    ["context", "<the surrounding paragraph>"],
    ["p", "<author hex>", "<relay>", "author"],
    ["comment", "<your take, plus any hashtags>"],
    ["t", "<subject>"]
  ]
}
```

Omit `p` entirely if B4 found no pubkey. Omit `context` only if the excerpt is already
a whole paragraph.

# Shared — ask before publishing. Always.

**Show the full event — content and tags — and wait for an explicit yes.** Not a
summary of it, not "shall I post it": the actual text that will go out under their
name, because that is the only version they can meaningfully approve.

This gate is not optional and does not depend on configuration. `write-policy:
confirm` makes the server hand back a token first, but that is a deployment setting
someone may have set to `allow`; it is not editorial consent. Ask either way.

It matters most because of what both branches produce. Branch A is a **paraphrase of
machine-mangled captions attributed to a named real person**, cut from a longer
conversation. Branch B is a **verbatim quotation of someone's writing, republished
under your key**. Approval is where a human checks that the paraphrase is fair, or
that the quotation is exact and not stripped of its qualifier. A note cannot be
edited, and NIP-09 deletion is a request relays may ignore, so there is no repair
afterwards — only a correction that fewer people will read.

After publishing, **read the event back from the relays by id** and confirm the
content is byte-identical to what was approved. Report the event id and which relays
accepted it. If a relay rejected it, say so plainly rather than reporting a clean
success.

# Shared — scheduling a post for later

Nostr has no scheduling. A relay stores an event when you send it, and most
relays reject an event whose `created_at` is in the future, so "publish now with
a later timestamp" is not a thing. Something on this machine has to hold the
event and send it at the appointed time.

```bash
scripts/schedule.sh nostr-event.json 3h     # 90min, 3h, 3d, "2h 30min"
scripts/schedule.sh --list
scripts/schedule.sh --cancel nostr-post-1790244000.timer
```

That sets a transient systemd user timer which runs `scripts/publish.py` on the
event file. `publish.py` also runs on its own for an immediate send, and takes
`--dry-run` to rehearse everything except the final confirm.

**The event is signed when it publishes, never when it is scheduled.** A nostr
event id is the hash of its contents, `created_at` is one of those contents, and
the signature covers all of it. Sign on Monday, send on Thursday, and you publish
something three days old that lands below everything else in the feed. Confirmed
while testing this: identical content signed 49 seconds apart produced two
different event ids.

Consequences worth stating before you promise anyone a scheduled post:

- **Check linger before scheduling, and offer to enable it.** A transient timer
  lives in the user systemd manager, which with `Linger=no` stops on full logout
  and takes the timer with it, silently. Check it:

  ```bash
  loginctl show-user "$USER" --property=Linger
  ```

  If it says `no`, ask the person whether to run `loginctl enable-linger "$USER"`
  before scheduling. It is a lasting change to their account (user services keep
  running between logins, until `loginctl disable-linger`), so ask rather than
  just doing it; if they decline, tell them to stay logged in until it fires.
  Signing still works with nobody logged in, because the wrapper uses the
  file-based keystore, not the desktop keychain.
- **The machine must still be awake when it fires.** Linger covers logout, not
  sleep: a laptop asleep at the appointed minute may not catch up.
- **Transient timers do not survive a reboot.** Nothing is written to disk, so a
  restart cancels the post silently, linger or not. Fine across hours. For days,
  write a real unit with `Persistent=true` (which needs linger too), or accept
  that a reboot loses it.
- **Uploading is still publishing, and it happens now.** The blob URL has to be in
  the content before the event can be built, so the video goes onto the public
  Blossom servers at approval time, not at post time. Only the note is delayed.
- **Approval still happens up front.** Scheduling is not a way to skip the gate.
  Show the event, get the yes, then schedule it.
- **Both scripts refuse an event that already carries a `published` block**, so a
  double fire or a re-run cannot post the same note twice.

Check afterwards with `--list`, and read `publish.log` next to the event file for
what happened. A scheduled post that failed is silent otherwise.

# Failure modes that actually bite

**Silent audio-only download.** Without a working JS runtime, yt-dlp cannot solve
YouTube's player challenge and a selector like `bv*+ba/b` falls through to the
audio-only fallback. It prints a *warning*, exits 0, and hands you an `.mp4` of the
right duration and a plausible size containing no video track. Probe the runtime
(Prerequisites) and run `verify.sh` on every download.

**An installed runtime that is still rejected.** Node v20 is present, on `PATH`, and
refused. "`node` exists" is not the test; the probe is.

**Caption track named differently from the language.** Metadata says `en-US`, the only
track is `en-orig`, and the script exits "no captions". List the tracks before
concluding there are none.

**Stale yt-dlp.** Errors like `The page needs to be reloaded` mean the extractor is
old, not that the video is broken. Use `uvx yt-dlp@latest`.

**Rolling auto-captions.** Auto-generated cues repeat the tail of the previous cue.
`transcript.py` deduplicates; if you parse VTT by hand, do the same.

**Cutting on round numbers.** A boundary at exactly 2:00 will land mid-word. Confirm
against cue-level timestamps.

**Trusting `-c copy` for cuts with fades.** Fades and frame-accurate boundaries both
require re-encoding.

**A quote that is nearly right.** Curly quotes, em dashes and non-breaking spaces
survive a copy-paste looking identical and break a verbatim claim. Run the B3 check;
never edit the quote to match your draft.

**A highlight stripped of its qualifier.** "X is true, in cases where Y" quoted as
"X is true" is a misquote even though every character is the author's. Widen the
excerpt or don't publish it.

**A scheduled post that silently never happened.** A reboot, a full logout with
linger off, or a laptop asleep at the appointed minute all cancel a transient timer
without telling anyone. Nothing errors, the note simply never appears. Check `--list` and the
`publish.log` rather than assuming it went.

# Reporting back

Say what you kept, what you dropped and why, with timestamps or paragraph positions —
the editorial choice is the part most likely to need changing, and it's cheap to
revise if it's visible.

Branch A: give the folder path, duration and size, and state the compression honestly
as both a length cut and a bitrate reduction rather than one flattering number.
Report the size **against the cap** — "14.5 MB, 87% of the 16 MiB cap" tells the
person whether the next clip has room, where a bare number doesn't.

Branch B: show the excerpt and the context side by side, say whether an author pubkey
was found or not, and state plainly that the quote was verified byte-for-byte against
the fetched source.
