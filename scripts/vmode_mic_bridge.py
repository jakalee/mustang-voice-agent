#!/usr/bin/env python3
"""
vmode(음성모드) 워키토키 - 마이크 -> STT -> 텔레그램 전송.

클로드코드-텔레그램 채널 봇 토큰(~/.claude/channels/telegram/.env)을 그대로 재사용해
sendMessage만 직접 호출한다. getUpdates(폴링)는 절대 건드리지 않으므로
채널 플러그인의 기존 폴링과 충돌하지 않는다.

사용법: venv/bin/python3 scripts/vmode_mic_bridge.py <chat_id>
종료: STATE_DIR/vmode.stop 파일을 만들면 다음 루프에서 종료.
"""
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

import requests

STATE_DIR = Path.home() / ".claude" / "channels" / "telegram"
ENV_FILE = STATE_DIR / ".env"
STOP_FILE = STATE_DIR / "vmode.stop"
MUTE_FILE = STATE_DIR / "vmode.mute"


def load_token() -> str:
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(f"TELEGRAM_BOT_TOKEN not found in {ENV_FILE}")


def send_message(token: str, chat_id: str, text: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception as e:
        print(f"[vmode_mic_bridge] send failed: {e}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print("usage: vmode_mic_bridge.py <chat_id>", file=sys.stderr)
        sys.exit(1)
    chat_id = sys.argv[1]
    token = load_token()

    import pyaudio
    from core.stt import record_audio, transcribe

    pa = pyaudio.PyAudio()
    print("[vmode_mic_bridge] started", flush=True)
    try:
        while not STOP_FILE.exists():
            if MUTE_FILE.exists():
                # 스피커가 재생 중 - 마이크는 쉬고 대기
                time.sleep(0.2)
                continue

            audio = record_audio(pa, abort_check=lambda: MUTE_FILE.exists())

            if STOP_FILE.exists():
                break
            if MUTE_FILE.exists() or not audio:
                # 녹음 도중 TTS가 시작되면 abort_check가 즉시 녹음을 버리지만,
                # 혹시 모를 타이밍차를 대비해 여기서도 한 번 더 확인
                continue

            text = transcribe(audio)
            if text and len(text.strip()) >= 2:
                print(f"[vmode_mic_bridge] {text}", flush=True)
                send_message(token, chat_id, text.strip())
    finally:
        pa.terminate()
        STOP_FILE.unlink(missing_ok=True)
        print("[vmode_mic_bridge] stopped", flush=True)


if __name__ == "__main__":
    main()
