# P18: how does a job execution end? Two questions F0047 depends on (S0006's restart, S0008's idle exit):
#   A. When the main process exits 0 while a background child still runs (the token refresher), does the
#      execution end at once, as succeeded?
#   B. At the task timeout, does the platform send SIGTERM first, and how long before the kill?
# One script answers both. It starts a background child that traps SIGTERM, traps SIGTERM itself, and then:
#   with PROBE_MODEL=exit it exits 0 after 20 s with the child still running (question A);
#   otherwise it waits until the task timeout ends it (question B; run it with a short task timeout).
# PROBE_MODEL is reused as the switch because run_probe.sh passes no other free variable to the job.
# Needs no secret, no proxy and no model API.
echo "=====BEGIN-RESULTS====="
t0=$(date +%s)
stamp() { echo "$(( $(date +%s) - t0 )) s: $*"; }
stamp "start, pid $$ (1 means the job's first process), mode ${PROBE_MODEL:-timeout}"
( trap 'echo "$(( $(date +%s) - t0 )) s: the child got SIGTERM"; exit 0' TERM; while :; do sleep 5; done ) &
child=$!
stamp "background child $child started"
trap 'stamp "the main process got SIGTERM"; kill $child 2>/dev/null; sleep 2; stamp "the main process exits 0 after SIGTERM"; echo "PROBE DONE"; exit 0' TERM
if [ "${PROBE_MODEL:-}" = "exit" ]; then
  sleep 20
  if kill -0 $child 2>/dev/null; then running=yes; else running=no; fi
  stamp "the main process exits 0 now; the child is still running: $running"
  echo "PROBE DONE"
  exit 0
fi
while :; do
  sleep 5
  stamp "alive"
done
