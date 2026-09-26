# clip-and-post

A Claude Code skill that turns a YouTube video into a short, faded clip posted to Nostr as a
kind 1 note, or an article into a NIP-84 quote highlight (kind 9802). Every run maps the source's
topics first, lets you pick a topic or an angle, drafts the text, and publishes only after you
approve the exact event.

`SKILL.md` is the skill itself: the full workflow, the rules about quoting, and the failure
modes. This README only covers installing and maintaining it.

## Requirements

- Linux. It is the only platform tested so far, and macOS and Windows are untested.
- `ffmpeg` and `ffprobe`
- `uv` (yt-dlp runs as `uvx yt-dlp@latest`, never a system install)
- a JavaScript runtime yt-dlp accepts (bun or deno; Node 20 is rejected)
- `nak`, for reading events back from relays
- [nostr-java-mcp](https://github.com/tcheeric/nostr-java) registered as the `nostr` MCP server,
  started through a wrapper script that sets the keystore, identity, relays and Blossom servers

## Install

```bash
git clone <this repo> ~/IdeaProjects/clip-and-post
ln -s ~/IdeaProjects/clip-and-post ~/.claude/skills/clip-and-post
~/IdeaProjects/clip-and-post/scripts/install.sh      # asks for the output folder, default ~/clip-and-post
```

`install.sh` records the output folder in `~/.config/clip-and-post/output-dir`, outside the
repo, so pulling updates keeps it.

Scheduled posts run `scripts/publish.py` headless. It starts the MCP server through
`~/.local/bin/nostr-java-mcp` unless `NOSTR_MCP_WRAPPER` points elsewhere, so put the relay list
in that wrapper rather than in Claude Code's MCP config, or scheduled posts won't see it.
Enable lingering (`loginctl enable-linger "$USER"`) if a scheduled post has to survive logout.

## Layout

```
SKILL.md              the skill: workflow, rules, failure modes
scripts/
  install.sh          choose and print the output folder
  transcript.py       captions: metadata, chapters, bucketed or windowed cues, grep
  cut.sh              trim, fade and concatenate sub-segments in one encode
  verify.sh           check a file has a video track and sample luma for fades
  article.py          fetch an article; verify a quote is verbatim in it
  publish.py          sign and publish nostr-event.json through the MCP server
  schedule.sh         publish later via a transient systemd user timer
```
