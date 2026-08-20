#!/bin/bash
# vmode(음성모드) 켜기 - 마이크브릿지 백그라운드 실행
STATE_DIR="$HOME/.claude/channels/telegram"
rm -f "$STATE_DIR/vmode.stop"
cd "$(dirname "$0")/.."
nohup venv/bin/python3 scripts/vmode_mic_bridge.py 5897202655 > /tmp/vmode_bridge.log 2>&1 &
echo $! > "$STATE_DIR/vmode.pid"
sleep 1
cat "$STATE_DIR/vmode.pid"
