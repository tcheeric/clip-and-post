#!/usr/bin/env python3
"""Upload a local file to Blossom through a one-off nostr-java-mcp instance.

The upload tool fetches a URL, so the file is served on loopback, and the one-off server is
started with allow-private-hosts. That setting is read as a JVM system property, so it goes in
JAVA_TOOL_OPTIONS; a --nostr.mcp... program argument is silently ignored.

  scripts/upload.py clip.mp4      # prints the tool's structured result as JSON
"""
import functools, http.server, json, os, subprocess, sys, threading

WRAPPER = os.environ.get("NOSTR_MCP_WRAPPER", os.path.expanduser("~/.local/bin/nostr-java-mcp"))

path = os.path.abspath(sys.argv[1])
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=os.path.dirname(path))
httpd = http.server.HTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{httpd.server_port}/{os.path.basename(path)}"

env = dict(os.environ, JAVA_TOOL_OPTIONS="-Dnostr.mcp.blossom.allow-private-hosts=true")
p = subprocess.Popen([WRAPPER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, env=env)

def send(m):
    p.stdin.write(json.dumps(m) + "\n"); p.stdin.flush()

def recv(i):
    for line in p.stdout:
        try:
            m = json.loads(line)
        except ValueError:
            continue
        if m.get("id") == i:
            return m
    sys.exit("nostr-java-mcp exited without answering")

try:
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "clip-and-post", "version": "1"}}})
    recv(1)
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
          "params": {"name": "nostr_blossom_upload", "arguments": {"sourceUrl": url}}})
    result = recv(2)["result"]
finally:
    p.terminate(); httpd.shutdown()

if result.get("isError"):
    sys.exit(result["content"][0]["text"])
print(json.dumps(result.get("structuredContent"), indent=1))
