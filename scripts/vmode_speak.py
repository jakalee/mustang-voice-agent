#!/usr/bin/env python3
"""
vmode(음성모드) 워키토키 - 텔레그램 텍스트 -> 노트북 스피커 출력.
사용법: venv/bin/python3 scripts/vmode_speak.py <텍스트가 담긴 파일경로>
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.tts import speak_piper

MUTE_FILE = Path.home() / ".claude" / "channels" / "telegram" / "vmode.mute"


def main():
    if len(sys.argv) < 2:
        return
    text = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
    if not text:
        return

    MUTE_FILE.parent.mkdir(parents=True, exist_ok=True)
    MUTE_FILE.touch()
    try:
        speak_piper(text, blocking=True)
    finally:
        time.sleep(0.5)  # 스피커 잔향이 마이크에 잡히지 않도록 여유
        MUTE_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
