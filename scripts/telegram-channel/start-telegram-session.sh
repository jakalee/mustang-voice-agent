#!/bin/bash
# Starts (or reuses) a detached tmux session running Claude Code so the
# Telegram channel stays connected without a visible terminal window.

export PATH="/Users/jakallee/.local/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"

SESSION="claude-telegram"
PROJECT_DIR="/Users/jakallee/Downloads/mustang_ai"
TMUX="/usr/local/bin/tmux"
CLAUDE="/Users/jakallee/.local/bin/claude"

if ! "$TMUX" has-session -t "$SESSION" 2>/dev/null; then
    "$TMUX" new-session -d -s "$SESSION" -c "$PROJECT_DIR" "$CLAUDE --channels plugin:telegram@claude-plugins-official"
fi
