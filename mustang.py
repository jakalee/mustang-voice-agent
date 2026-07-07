#!/usr/bin/env python3
"""
🐎 Mustang AI - macOS 로컬 AI 어시스턴트
웨이크워드 "머스탱" 감지 후 음성 명령 처리

실행: python mustang.py [--setup] [--text] [--telegram]
"""
import argparse
import asyncio
import json
import logging
import math
import os
import signal
import struct
import subprocess
import sys
import time
import threading
import warnings
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional

# ── 로그 설정 ────────────────────────────────────────────────────────────────
_LOG_DIR = Path(__file__).parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(_LOG_DIR / "mustang.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("mustang")

# ── 위젯 서버 (WebSocket + HTTP, mustang.py 내장) ────────────────────────────
_ws_clients: set = set()
_ws_loop: Optional[asyncio.AbstractEventLoop] = None
_WIDGET_DIR = Path(__file__).parent / "widget"


async def _ws_handler(websocket):
    _ws_clients.add(websocket)
    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
                if "command" in msg:
                    # 위젯에서 받은 텍스트 명령을 별도 스레드에서 처리
                    threading.Thread(
                        target=_handle_widget_command,
                        args=(msg["command"],),
                        daemon=True,
                    ).start()
            except Exception:
                pass
    finally:
        _ws_clients.discard(websocket)


async def _ws_broadcast(msg: dict):
    if not _ws_clients:
        return
    data = json.dumps(msg)
    await asyncio.gather(*[c.send(data) for c in _ws_clients], return_exceptions=True)


def _ws_send(msg: dict):
    if _ws_loop and _ws_loop.is_running():
        asyncio.run_coroutine_threadsafe(_ws_broadcast(msg), _ws_loop)


def _kill_port(port: int):
    try:
        result = subprocess.check_output(["lsof", "-ti", f":{port}"], text=True).strip()
        for pid in result.splitlines():
            os.kill(int(pid), signal.SIGKILL)
        time.sleep(0.4)
    except Exception:
        pass


class _WidgetHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(_WIDGET_DIR), **kwargs)
    def log_message(self, *args):
        pass


def _start_http_server():
    _kill_port(8766)
    HTTPServer(("localhost", 8766), _WidgetHTTPHandler).serve_forever()


def _start_ws_server():
    global _ws_loop
    try:
        import websockets as _ws
    except ImportError:
        return
    _kill_port(8765)

    async def _run():
        global _ws_loop
        _ws_loop = asyncio.get_running_loop()
        async with _ws.serve(_ws_handler, "localhost", 8765):
            await asyncio.Future()

    loop = asyncio.new_event_loop()
    _ws_loop = loop
    loop.run_until_complete(_run())


def _start_widget_servers():
    threading.Thread(target=_start_http_server, daemon=True).start()
    threading.Thread(target=_start_ws_server,   daemon=True).start()
    print("🎨 위젯 서버 시작됨 (ws://localhost:8765 | http://localhost:8766)")


# 위젯 명령 처리 (MustangAgent 인스턴스 참조용)
_agent_ref = None

def _handle_widget_command(text: str):
    """위젯에서 받은 텍스트 명령 처리"""
    if not _agent_ref:
        return
    print(f"\n💬 [위젯] {text}")
    WidgetBridge.set_thinking(text)
    try:
        response = _agent_ref._process_command(text)
        if response in ("SLEEP", "TEXT_MODE", "VOICE_MODE"):
            WidgetBridge.set_idle()
            return
        ev = WidgetBridge.set_speaking(response)
        _agent_ref.speak(response)
        ev.set()
    except Exception as e:
        WidgetBridge.set_idle()
        print(f"  ⚠️ 위젯 명령 오류: {e}")


def _simulate_speaking(stop_event: threading.Event):
    """self.speak()가 끝날 때까지 진폭 시뮬레이션 — stop_event로 종료 신호 수신"""
    start = time.time()
    while not stop_event.is_set():
        t = time.time() - start
        amp = 0.35 + 0.55 * abs(math.sin(t * 5.5 + 0.3))
        _ws_send({"amplitude": round(amp, 3)})
        time.sleep(0.05)
    # 자연스러운 페이드아웃
    for i in range(10):
        amp = 0.3 * (1 - i / 10)
        _ws_send({"amplitude": round(amp, 3)})
        time.sleep(0.04)
    _ws_send({"state": "idle", "amplitude": 0.0, "text": ""})


class WidgetBridge:
    @staticmethod
    def set_idle():
        _ws_send({"state": "idle", "amplitude": 0.0, "text": ""})

    @staticmethod
    def set_listening():
        _ws_send({"state": "listening", "amplitude": 0.0, "text": ""})

    @staticmethod
    def set_thinking(user_text: str = ""):
        _ws_send({"state": "thinking", "amplitude": 0.0, "text": user_text})

    @staticmethod
    def set_speaking(text: str = "") -> threading.Event:
        """진폭 시뮬레이션 시작. 반환된 stop_event.set()으로 TTS 종료 신호를 보내세요."""
        _ws_send({"state": "speaking", "amplitude": 0.3, "text": text})
        stop_event = threading.Event()
        threading.Thread(target=_simulate_speaking, args=(stop_event,), daemon=True).start()
        return stop_event


_start_widget_servers()

# 불필요한 경고 억제
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("MKL_THREADING_LAYER", "GNU")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
warnings.filterwarnings("ignore", category=UserWarning)

sys.path.insert(0, str(Path(__file__).parent))

# .env 파일 자동 로드
_env_file = Path(__file__).parent / "config" / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            if _v.strip():
                os.environ.setdefault(_k.strip(), _v.strip())

# ── 설정 상수 ─────────────────────────────────────────────────────────────────

VOICE_CHAT_ID = 0       # 음성 모드용 고정 chat_id
WAKEUP_MESSAGE = "네, 말씀하세요."
READY_MESSAGE = "머스탱 준비됐습니다."


def setup_google_env(creds: dict):
    gcp_path = creds.get("GOOGLE_CREDENTIALS_PATH", "")
    if gcp_path:
        os.environ["GOOGLE_CREDENTIALS_PATH"] = gcp_path


class MustangAgent:
    def __init__(self, use_whisper: bool = True):
        global _agent_ref
        self.use_whisper = use_whisper
        self._init_components()
        _agent_ref = self

    def _init_components(self):
        print("🐎 Mustang AI 초기화 중...")

        # 자격증명 로드 (텔레그램/Google 선택 항목만)
        try:
            from core.credentials import load_credentials
            self.creds = load_credentials()
            setup_google_env(self.creds)
        except Exception:
            self.creds = {}

        # TTS
        from core.tts import speak, speak_async
        self.speak = speak
        self.speak_async = speak_async

        # STT
        from core.stt import record_audio, transcribe
        self.record_audio = record_audio
        self.transcribe = transcribe

        # 스킬 매니저
        from core.skill_manager import SkillManager
        print("  📦 스킬 로딩 중...")
        self.skill_manager = SkillManager()

        # 스케줄러
        try:
            from core.scheduler import TaskScheduler
            self.scheduler = TaskScheduler(task_runner=self._run_scheduled_task)
            try:
                from skills.schedule_task import set_scheduler
                set_scheduler(self.scheduler)
            except Exception:
                pass
        except Exception as e:
            print(f"  ⚠️ 스케줄러 초기화 실패: {e}")
            self.scheduler = None

        # Claude Code CLI 엔진
        from core.claude_runner import ClaudeRunner
        skill_list = self._build_skill_list()
        self.claude = ClaudeRunner(
            skill_list=skill_list,
            skill_manager=self.skill_manager,
        )

        # PyAudio
        try:
            import pyaudio
            self.pa = pyaudio.PyAudio()
        except Exception as e:
            print(f"  ⚠️ PyAudio 초기화 실패: {e}")
            self.pa = None

        print("✅ 초기화 완료\n")

    def _build_skill_list(self) -> str:
        lines = []
        for tool in self.skill_manager.get_tool_definitions():
            params = list(tool["input_schema"].get("properties", {}).keys())
            lines.append(f"- {tool['name']}: {tool['description']} (파라미터: {params})")
        return "\n".join(lines) if lines else "(없음)"

    def _run_scheduled_task(self, command: str):
        result = self._process_command(command)
        print(f"  [예약작업] {result}")
        self.speak_async(result)

    def _process_command(self, user_text: str, chat_id: int = VOICE_CHAT_ID) -> str:
        text = user_text.strip()

        # 특별 명령 처리 (Claude 호출 없이 즉시 처리)
        if any(w in text for w in ["리셋", "초기화", "대화 삭제"]):
            self.claude.reset_session(chat_id)
            return "대화 내용을 초기화했습니다."

        if any(w in text for w in ["스킬 목록", "스킬목록", "사용 가능한 스킬"]):
            return self.skill_manager.list_skills()

        if any(w in text for w in ["퇴근해", "퇴근", "컴퓨터 꺼", "컴퓨터 종료", "시스템 종료"]):
            self.speak("네, 수고하셨습니다. 5초 후 컴퓨터를 종료합니다.")
            import threading
            def _shutdown():
                import time, subprocess
                time.sleep(5)
                subprocess.run(["osascript", "-e", 'tell app "System Events" to shut down'])
            threading.Thread(target=_shutdown, daemon=False).start()
            return "SHUTDOWN"

        if any(w in text for w in ["종료", "잠자", "바이", "꺼줘"]):
            return "SLEEP"

        if any(w in text for w in ["텍스트 모드", "텍스트모드", "키보드 모드"]):
            return "TEXT_MODE"

        if text in ["/음성모드", "/voice", "/음성"]:
            return "VOICE_MODE"

        # Claude Code CLI로 처리
        try:
            logger.info(f"[사용자] {text}")
            response = self.claude.chat(user_message=text, chat_id=chat_id)
            if response == "AUTH_ERROR":
                msg = "Claude 인증이 만료됐어요. 터미널에서 로그인 중이에요. 브라우저에서 승인해주세요."
                logger.error(f"[AUTH_ERROR] 인증 만료 감지")
                return msg
            logger.info(f"[머스탱] {response}")
            return response
        except Exception as e:
            logger.exception(f"[오류] _process_command 예외: {e}")
            return f"처리 중 오류가 발생했습니다: {e}"

    def _terminate_audio(self):
        """PyAudio 완전 종료 (TTS 전 CoreAudio 충돌 방지)"""
        if self.pa:
            try:
                self.pa.terminate()
            except Exception:
                pass
            self.pa = None

    def _init_audio(self):
        """PyAudio 재초기화"""
        if self.pa is None:
            import pyaudio
            self.pa = pyaudio.PyAudio()

    def _listen_and_respond(self) -> str:
        """음성 입력 받아 처리. 특수 반환값: SLEEP / TEXT_MODE / 없음"""
        self._init_audio()
        if not self.pa:
            print("  ⚠️ 마이크를 사용할 수 없습니다.")
            return ""

        print("  🎤 음성 입력 대기 중...")
        WidgetBridge.set_listening()
        audio = self.record_audio(self.pa)

        # 녹음 완료 → PyAudio 종료 후 TTS (CoreAudio 충돌 방지)
        self._terminate_audio()

        if audio is None:
            WidgetBridge.set_idle()
            self.speak("음성을 인식하지 못했습니다.")
            return ""

        print("  ⏳ 음성 분석 중...")
        WidgetBridge.set_thinking()
        text = self.transcribe(audio, use_whisper=self.use_whisper)

        if not text or len(text.strip()) < 2:
            WidgetBridge.set_idle()
            self.speak("말씀을 이해하지 못했습니다.")
            return ""

        print(f"  📝 인식됨: {text}")
        WidgetBridge.set_thinking(text)   # 사용자 발화를 위젯에 표시
        response = self._process_command(text, chat_id=VOICE_CHAT_ID)

        if response == "SLEEP":
            ev = WidgetBridge.set_speaking("알겠습니다. 다시 부르시면 깨어납니다.")
            self.speak("알겠습니다. 다시 부르시면 깨어납니다.")
            ev.set()
            return "SLEEP"

        if response == "TEXT_MODE":
            ev = WidgetBridge.set_speaking("텍스트 모드로 전환합니다.")
            self.speak("텍스트 모드로 전환합니다.")
            ev.set()
            return "TEXT_MODE"

        if response == "SHUTDOWN":
            return "SHUTDOWN"

        print(f"  🤖 응답: {response[:120]}{'...' if len(response) > 120 else ''}")
        ev = WidgetBridge.set_speaking(response)
        self.speak(response)   # 블로킹 — TTS가 완전히 끝날 때까지 대기
        ev.set()               # TTS 끝 → 진폭 페이드아웃 시작
        return ""

    def run_voice_mode(self):
        """웨이크워드 감지 루프 (faster-whisper 기반, 완전 무료)"""
        from core.wakeword import listen_for_wakeword, _start_hotkey_listener

        self._init_audio()
        if not self.pa:
            print("❌ 마이크를 초기화할 수 없습니다.")
            return

        _start_hotkey_listener()
        print("🎤 준비 완료! '머스탱'이라고 불러보세요... 또는 ⌥Space (종료: Ctrl+C)\n")
        self._terminate_audio()
        self.speak(READY_MESSAGE)
        time.sleep(0.3)

        try:
            while True:
                self._init_audio()
                WidgetBridge.set_idle()

                # 웨이크워드 감지 ("머스탱!")
                detected = listen_for_wakeword(self.pa)
                if not detected:
                    continue

                print("\n🔥 [감지] 머스탱이 깨어났습니다!")
                WidgetBridge.set_listening()

                self._terminate_audio()
                time.sleep(0.15)
                self.speak(WAKEUP_MESSAGE)
                time.sleep(0.2)

                result = self._listen_and_respond()

                if result == "TEXT_MODE":
                    self.run_text_mode(from_voice=True)

                WidgetBridge.set_idle()
                self._terminate_audio()
                time.sleep(0.3)
                print("\n🎤 다시 대기 중... ('머스탱'이라고 불러주세요)")

        except KeyboardInterrupt:
            print("\n👋 머스탱을 종료합니다.")

    def run_text_mode(self, from_voice: bool = False):
        """텍스트 입력 모드
        from_voice=True 이면 /음성모드 입력 시 음성 모드로 복귀
        """
        if from_voice:
            print("\n💬 텍스트 모드 전환됨 ('/음성모드' 입력 시 음성 모드로 복귀)\n")
        else:
            print("💬 텍스트 모드 - 명령을 입력하세요 ('종료'로 끝내기)\n")
            self.speak_async(READY_MESSAGE)

        while True:
            try:
                text = input("나: ").strip()
                if not text:
                    continue

                response = self._process_command(text, chat_id=VOICE_CHAT_ID)

                if response == "SLEEP":
                    print("머스탱: 안녕히 계세요!")
                    self.speak("안녕히 계세요.")
                    break

                if response == "VOICE_MODE":
                    print("머스탱: 음성 모드로 전환합니다.")
                    self.speak("음성 모드로 전환합니다.")
                    time.sleep(0.5)
                    return  # 음성 루프로 복귀

                if response == "TEXT_MODE":
                    print("머스탱: 이미 텍스트 모드입니다.")
                    continue

                print(f"머스탱: {response}")
                self.speak_async(response)

            except KeyboardInterrupt:
                print("\n👋 종료합니다.")
                break
            except EOFError:
                break

    def run_telegram_mode(self):
        """텔레그램 봇 모드"""
        token = self.creds.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            print("⚠️ 텔레그램 봇 토큰이 없습니다.")
            return

        chat_id_str = self.creds.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")

        def telegram_handler(user_text: str, tg_user_id: int = 0) -> str:
            return self._process_command(user_text, chat_id=tg_user_id)

        try:
            from core.telegram_bot import TelegramBot
            bot = TelegramBot(
                token=token,
                chat_id=chat_id_str,
                command_handler=self._process_command,
            )
            bot.start()
            print("✅ 텔레그램 봇 실행 중... (종료: Ctrl+C)")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 텔레그램 봇 종료")
        except ImportError:
            print("❌ python-telegram-bot 설치 필요: pip install python-telegram-bot")


def main():
    parser = argparse.ArgumentParser(description="🐎 Mustang AI")
    parser.add_argument("--setup", action="store_true", help="자격증명 최초 설정")
    parser.add_argument("--text", action="store_true", help="텍스트 모드")
    parser.add_argument("--telegram", action="store_true", help="텔레그램 봇 모드")
    parser.add_argument("--no-whisper", action="store_true", help="Google STT 사용")
    args = parser.parse_args()

    if args.setup:
        from core.credentials import setup_credentials
        setup_credentials()
        print("\n설정 완료. 이제 'python mustang.py'로 시작하세요.")
        print("(Claude Code는 별도 API 키 없이 이미 인증된 상태로 사용됩니다)")
        return

    agent = MustangAgent(use_whisper=not args.no_whisper)

    if args.telegram:
        agent.run_telegram_mode()
    elif args.text:
        agent.run_text_mode()
    else:
        agent.run_voice_mode()


if __name__ == "__main__":
    main()
