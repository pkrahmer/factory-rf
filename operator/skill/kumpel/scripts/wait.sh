#!/bin/sh
# Wait until the factory needs the operator, or until <minutes> have passed (default 9; keep it below
# the shell tool's timeout). Prints exactly one line:
#   event: <the status line that changed or waits>   when a pull request waits on the operator,
#                                                     a story was archived, or nothing is open any more
#   continue: nothing new                            when the time ran out
# Polls GitHub once a minute through status.sh. Call it as the only tool call of its message.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
minutes=${1:-9}
before=$(sh "$here/status.sh")
waiting=$(printf '%s\n' "$before" | grep 'waits:' | head -n 1 || true)
if [ -n "$waiting" ]; then
  echo "event: $waiting"
  exit 0
fi
end=$(( $(date +%s) + minutes * 60 ))
while [ "$(date +%s)" -lt "$end" ]; do
  sleep 60
  now=$(sh "$here/status.sh" 2>/dev/null) || continue
  waiting=$(printf '%s\n' "$now" | grep 'waits:' | head -n 1 || true)
  if [ -n "$waiting" ]; then
    echo "event: $waiting"
    exit 0
  fi
  archive_before=$(printf '%s\n' "$before" | grep '^last archive:' || true)
  archive_now=$(printf '%s\n' "$now" | grep '^last archive:' || true)
  if [ "$archive_now" != "$archive_before" ]; then
    echo "event: $archive_now"
    exit 0
  fi
  # Only a pull request that was open and is gone is news: right after a story starts, the
  # factory needs a tick before it opens one.
  if printf '%s\n' "$before" | grep -q '^#' && ! printf '%s\n' "$now" | grep -q '^#'; then
    echo "event: no work-item pull request is open"
    exit 0
  fi
done
echo "continue: nothing new"
