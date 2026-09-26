#!/usr/bin/env bash
# Schedule a prepared nostr-event.json to publish later.
#
#   schedule.sh EVENT_JSON DELAY        e.g. schedule.sh nostr-event.json 3h
#   schedule.sh --list
#   schedule.sh --cancel UNIT
#
# DELAY is anything systemd understands: 90min, 3h, 3d, "2h 30min".
#
# Durability, which matters more than the syntax:
#   * the machine must be awake and the user logged in when it fires;
#   * transient timers do not survive a reboot;
#   * with Linger=no the user manager stops on full logout, taking the timer.
# Fine for hours. For days, enable lingering first (loginctl enable-linger "$USER")
# and accept that a reboot still cancels it.
set -euo pipefail

SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "--list" ]]; then
  systemctl --user list-timers 'nostr-post-*' --all
  exit 0
fi
if [[ "${1:-}" == "--cancel" ]]; then
  systemctl --user stop "${2:?unit name required}" 2>/dev/null || true
  systemctl --user reset-failed "${2}" 2>/dev/null || true
  echo "cancelled ${2}"
  exit 0
fi

EVENT="$(readlink -f "${1:?event json required}")"
DELAY="${2:?delay required, e.g. 3h}"
[[ -r "$EVENT" ]] || { echo "cannot read $EVENT" >&2; exit 1; }

# Refuse to schedule something already sent; publishing twice makes two notes.
if python3 -c "import json,sys;d=json.load(open('$EVENT'));sys.exit(0 if d.get('published',{}).get('relays') else 1)"; then
  echo "that event was already published; refusing to schedule it again" >&2
  exit 1
fi

if [[ "$(loginctl show-user "$USER" --property=Linger --value 2>/dev/null)" != "yes" ]]; then
  echo "warning: Linger=no, so logging out cancels this post. Enable with: loginctl enable-linger \"\$USER\"" >&2
fi

UNIT="nostr-post-$(date +%s)"
LOG="${EVENT%/*}/publish.log"

systemd-run --user --on-active="$DELAY" --unit="$UNIT" \
  --description="scheduled nostr post from $EVENT" \
  "$SCRIPTS/publish.py" "$EVENT" --log "$LOG" >/dev/null

echo "scheduled  unit: ${UNIT}.timer"
echo "           when: $(systemctl --user list-timers "${UNIT}.timer" --no-legend | awk '{print $1, $2, $3, $4}')"
echo "            log: $LOG"
echo "         cancel: $SCRIPTS/schedule.sh --cancel ${UNIT}.timer"
