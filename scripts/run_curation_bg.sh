#!/usr/bin/env sh
# run_curation_bg.sh — launch a long curation run DETACHED (nohup) with a timestamped log, so
# it survives the terminal closing. Thin wrapper around run_curation.sh; all flags pass through.
# Use this for --family ALL (hours on the real model); use run_curation.sh directly for
# --dry-run / --mock (fast, better watched in the foreground).
#
# --db defaults to the operational store (in-place), same as run_curation.sh.
# Clear curation first if regenerating:  uv run sh scripts/reset_l2.sh --curation
#
#   sh scripts/run_curation_bg.sh --family ALL
#   sh scripts/run_curation_bg.sh --family VDA
#
# Writes logs/curate_<family-or-run>_<timestamp>.log (+ a matching .pid). On launch it prints
# the exact `tail -f` command. Monitor / manage:
#   tail -f logs/<the printed log>          # live progress
#   ps -p "$(cat logs/<...>.pid)"           # still running?
#   kill "$(cat logs/<...>.pid)"            # stop it
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"          # project root
RUNNER="$HERE/scripts/run_curation.sh"
LOGDIR="$HERE/logs"
mkdir -p "$LOGDIR"

# Derive a readable label from the args (family value, else 'run').
LABEL="run"
prev=""
for a in "$@"; do
  case "$prev" in --family) LABEL="$a" ;; esac
  prev="$a"
done

TS="$(date +%Y%m%d-%H%M%S)"
LOG="$LOGDIR/curate_${LABEL}_${TS}.log"
PID="$LOGDIR/curate_${LABEL}_${TS}.pid"

# PYTHONUNBUFFERED=1 so progress lines flush to the log live (Python buffers otherwise).
PYTHONUNBUFFERED=1 nohup sh "$RUNNER" "$@" > "$LOG" 2>&1 &
echo "$!" > "$PID"

echo "launched detached: pid $(cat "$PID")"
echo "  args : $*"
echo "  log  : $LOG"
echo "  pid  : $PID"
echo
echo "follow it:   tail -f \"$LOG\""
echo "still up?:   ps -p \"\$(cat \"$PID\")\""
echo "stop it:     kill \"\$(cat \"$PID\")\""
