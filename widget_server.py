"""
Mustang Widget Server
- WebSocket 서버 (port 8765): 위젯에 상태/진폭 전송
- HTTP 서버 (port 8766): index.html 서빙 (GeekTool용)

mustang-voice-agent의 voice_ai.py 또는 mustang.py에서
WidgetBridge를 import하여 상태 변경 시 호출하세요.
"""

import asyncio
import json
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional
import websockets

# ─── 연결된 WebSocket 클라이언트 ─────────────────────────────────
_clients: set = set()
_loop: Optional[asyncio.AbstractEventLoop] = None

WIDGET_DIR = Path(__file__).parent / "widget"


async def _ws_handler(websocket):
    _clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        _clients.discard(websocket)


async def _broadcast(msg: dict):
    if not _clients:
        return
    data = json.dumps(msg)
    await asyncio.gather(*[c.send(data) for c in _clients], return_exceptions=True)


def _send(msg: dict):
    """스레드 안전 전송 (mustang 코드에서 호출)"""
    if _loop and _loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast(msg), _loop)


# ─── 공개 API ─────────────────────────────────────────────────
class WidgetBridge:
    """mustang-voice-agent에서 import해서 사용"""

    @staticmethod
    def set_idle():
        _send({"state": "idle", "amplitude": 0.0})

    @staticmethod
    def set_listening():
        _send({"state": "listening", "amplitude": 0.0})

    @staticmethod
    def set_thinking():
        _send({"state": "thinking", "amplitude": 0.0})

    @staticmethod
    def set_speaking(text: str = ""):
        """TTS 발화 시작 — macOS say 명령어 모니터링"""
        _send({"state": "speaking", "amplitude": 0.3})
        # say 명령 길이 기반 진폭 시뮬레이션
        threading.Thread(target=_simulate_speaking, args=(text,), daemon=True).start()


def _simulate_speaking(text: str):
    """macOS say는 진폭 API가 없으므로 텍스트 길이 기반으로 파형 시뮬레이션"""
    chars = max(len(text), 10)
    duration = chars * 0.07  # 한국어 기준 대략적 발화 시간(초)
    start = time.time()
    import math
    while time.time() - start < duration:
        t = time.time() - start
        amp = 0.4 + 0.5 * abs(math.sin(t * 6)) * (1 - t / duration)
        _send({"amplitude": round(amp, 3)})
        time.sleep(0.05)
    _send({"state": "idle", "amplitude": 0.0})


# ─── HTTP 서버 (index.html 서빙) ──────────────────────────────
class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WIDGET_DIR), **kwargs)

    def log_message(self, *args):
        pass  # 로그 억제


def _kill_port(port: int):
    """해당 포트를 점유 중인 프로세스를 종료"""
    import signal
    import subprocess
    try:
        result = subprocess.check_output(
            ["lsof", "-ti", f":{port}"], text=True
        ).strip()
        for pid in result.splitlines():
            os.kill(int(pid), signal.SIGKILL)
        time.sleep(0.5)
    except Exception:
        pass


def _run_http():
    _kill_port(8766)
    server = HTTPServer(("localhost", 8766), _Handler)
    server.serve_forever()


# ─── 서버 진입점 ──────────────────────────────────────────────
async def _main():
    global _loop
    _loop = asyncio.get_running_loop()
    _kill_port(8765)
    async with websockets.serve(_ws_handler, "localhost", 8765):
        print("[widget] WebSocket ws://localhost:8765 시작")
        print("[widget] HTTP     http://localhost:8766 시작")
        await asyncio.Future()  # 영구 실행


def start_servers():
    """백그라운드 스레드에서 서버 시작 (mustang에서 호출)"""
    threading.Thread(target=_run_http, daemon=True).start()

    def _run_ws():
        global _loop
        loop = asyncio.new_event_loop()
        _loop = loop
        loop.run_until_complete(_main())

    threading.Thread(target=_run_ws, daemon=True).start()


if __name__ == "__main__":
    # 단독 실행 시
    threading.Thread(target=_run_http, daemon=True).start()
    asyncio.run(_main())
