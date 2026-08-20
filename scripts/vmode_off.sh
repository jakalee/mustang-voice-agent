#!/bin/bash
# vmode(음성모드) 끄기 - 마이크브릿지 종료
STATE_DIR="$HOME/.claude/channels/telegram"
touch "$STATE_DIR/vmode.stop"
sleep 2
if [ -f "$STATE_DIR/vmode.pid" ]; then
  kill "$(cat "$STATE_DIR/vmode.pid")" 2>/dev/null
  rm -f "$STATE_DIR/vmode.pid"
fi
echo "stopped"
