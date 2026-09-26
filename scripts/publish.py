#!/usr/bin/env python3
"""Publish a prepared nostr-event.json through the local MCP server.

  publish.py EVENT_JSON [--dry-run] [--log FILE]

Runs headless, so it is what a scheduled job executes. The event is signed at the
moment this runs, never earlier: a nostr event's created_at is covered by its
signature, and clients order feeds by created_at. Signing at schedule time and
sending days later would publish something that is already days old and lands
below everything else in the feed.

--dry-run does everything except the final confirm: it starts the server, unlocks
the keystore, and takes a preview. Use it to prove a schedule will fire without
putting anything on a relay.
"""
import argparse, json, os, pathlib, subprocess, sys, time

# The script that starts nostr-java-mcp over stdio with the keystore and relays set.
WRAPPER = os.environ.get("NOSTR_MCP_WRAPPER", os.path.expanduser("~/.local/bin/nostr-java-mcp"))


def log(msg, handle):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line, file=sys.stderr)
    if handle:
        handle.write(line + "\n"); handle.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("event")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--log")
    a = ap.parse_args()

    handle = open(a.log, "a") if a.log else None
    path = pathlib.Path(a.event)
    event = json.loads(path.read_text())

    if event.get("published", {}).get("relays"):
        log(f"already published as {event.get('id')}, refusing to publish twice", handle)
        return 0

    proc = subprocess.Popen([WRAPPER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)
    n = [0]

    def call(method, params=None):
        n[0] += 1
        msg = {"jsonrpc": "2.0", "id": n[0], "method": method}
        if params is not None:
            msg["params"] = params
        proc.stdin.write(json.dumps(msg) + "\n"); proc.stdin.flush()
        while True:
            line = proc.stdout.readline()
            if not line:
                raise SystemExit("server exited")
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("id") == n[0]:
                return r

    call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                        "clientInfo": {"name": "scheduled-publish", "version": "1"}})
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()

    args = {"kind": event["kind"], "content": event["content"], "tags": event["tags"]}
    first = call("tools/call", {"name": "nostr_publish_event", "arguments": args})
    result = first.get("result", {})
    if result.get("isError"):
        log(f"refused: {result['content'][0]['text']}", handle)
        proc.terminate(); return 1

    structured = result.get("structuredContent") or {}
    token = structured.get("confirmationToken")

    if a.dry_run:
        log(f"DRY RUN ok: previewed kind {event['kind']}, event id would be "
            f"{structured.get('eventId')}. Nothing was sent to a relay.", handle)
        proc.terminate(); return 0

    # write-policy: confirm hands back a token; allow publishes on the first call
    if token:
        args["confirmationToken"] = token
        result = call("tools/call", {"name": "nostr_publish_event",
                                     "arguments": args}).get("result", {})
        if result.get("isError"):
            log(f"refused on confirm: {result['content'][0]['text']}", handle)
            proc.terminate(); return 1
        structured = result.get("structuredContent") or {}

    accepted = structured.get("acceptedBy", [])
    failures = structured.get("failures", [])
    event["id"] = structured.get("eventId")
    event["published"] = {"relays": accepted, "failures": failures,
                          "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    path.write_text(json.dumps(event, ensure_ascii=False, indent=2) + "\n")

    log(f"published {event['id']} to {accepted}" + (f" FAILURES: {failures}" if failures else ""),
        handle)
    proc.terminate()
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main())
