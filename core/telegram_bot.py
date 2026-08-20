"""
텔레그램 봇 인터페이스
텔레그램으로 머스탱에게 명령을 보내고 결과를 받음
"""
import asyncio
import threading
import time
from typing import Callable, Optional


class TelegramBot:
    def __init__(self,
                 token: str,
                 chat_id: Optional[str] = None,
                 command_handler: Optional[Callable] = None):
        self.token = token
        self.chat_id = chat_id
        self.command_handler = command_handler
        self._app = None
        self._loop = None
        self._thread = None

        # 음성모드 (vmode) — 텔레그램 텍스트 ↔ 노트북 스피커/마이크 워키토키
        self.voice_mode = False
        self._voice_thread = None
        self._voice_stop = threading.Event()
        self._tts_active = threading.Event()

    def _setup(self):
        from telegram import Update
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

        app = ApplicationBuilder().token(self.token).build()

        async def start(update: Update, context):
            await update.message.reply_text(
                "머스탱 AI 봇입니다. 명령을 입력하세요.\n"
                "/reset - 대화 초기화\n"
                "/skills - 스킬 목록\n"
                "/vmode - 음성모드(워키토키) on/off\n"
                "/help - 도움말"
            )

        async def reset_cmd(update: Update, context):
            if self.command_handler:
                result = self.command_handler("리셋")
                await update.message.reply_text(result or "대화가 초기화되었습니다.")

        async def skills_cmd(update: Update, context):
            if self.command_handler:
                result = self.command_handler("스킬 목록")
                await update.message.reply_text(result or "스킬 정보를 가져올 수 없습니다.")

        async def vmode_cmd(update: Update, context):
            if self.chat_id and str(update.effective_chat.id) != str(self.chat_id):
                await update.message.reply_text("권한이 없습니다.")
                return

            self.voice_mode = not self.voice_mode
            if self.voice_mode:
                await update.message.reply_text(
                    "voice mode on 되었습니다.\n노트북 기기와 직접 입출력됩니다."
                )
                self._start_voice_bridge(update.effective_chat.id)
            else:
                await update.message.reply_text(
                    "voice mode off 되었습니다.\n챗봇모드로 돌아옵니다."
                )
                self._stop_voice_bridge()

        async def handle_message(update: Update, context):
            if self.chat_id and str(update.effective_chat.id) != str(self.chat_id):
                await update.message.reply_text("권한이 없습니다.")
                return

            user_text = update.message.text

            if self.voice_mode:
                # 워키토키 모드: Claude로 보내지 않고 텍스트를 그대로 스피커로 송출
                self._speak_piper(user_text)
                return

            await update.message.reply_text("처리 중...")

            if self.command_handler:
                result = self.command_handler(user_text)
                await update.message.reply_text(result or "처리 완료")

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("reset", reset_cmd))
        app.add_handler(CommandHandler("skills", skills_cmd))
        app.add_handler(CommandHandler("vmode", vmode_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        return app

    # ── 음성모드 (vmode) ────────────────────────────────────────────────────
    def _speak_piper(self, text: str):
        """텔레그램에서 온 텍스트를 PiperVoice로 스피커에 송출 (마이크 루프와 겹치지 않게 뮤트)"""
        def _run():
            self._tts_active.set()
            try:
                from core.tts import speak_piper
                speak_piper(text, blocking=True)
            finally:
                time.sleep(0.5)  # 스피커 잔향이 마이크에 잡히지 않도록 여유
                self._tts_active.clear()

        threading.Thread(target=_run, daemon=True).start()

    def _start_voice_bridge(self, chat_id):
        """마이크로 들어오는 음성을 STT로 변환해 텔레그램으로 전송하는 루프 시작"""
        self._voice_stop.clear()

        def _loop():
            import pyaudio
            from core.stt import record_audio, transcribe

            pa = pyaudio.PyAudio()
            try:
                while not self._voice_stop.is_set():
                    if self._tts_active.is_set():
                        self._tts_active.wait(timeout=5)
                        continue

                    audio = record_audio(pa)

                    if self._voice_stop.is_set():
                        break
                    if self._tts_active.is_set() or not audio:
                        # 스피커가 재생 중이었으면 자기 목소리를 주웠을 수 있으니 버림
                        continue

                    text = transcribe(audio)
                    if text and len(text.strip()) >= 2:
                        self.send_message(text, chat_id=chat_id)
            finally:
                pa.terminate()

        self._voice_thread = threading.Thread(target=_loop, daemon=True)
        self._voice_thread.start()

    def _stop_voice_bridge(self):
        self._voice_stop.set()

    def start(self):
        if not self.token:
            print("⚠️ 텔레그램 봇 토큰이 없습니다.")
            return

        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            self._app = self._setup()
            loop.run_until_complete(self._app.run_polling())

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        print("✅ 텔레그램 봇 시작됨")

    def send_message(self, text: str, chat_id: Optional[str] = None):
        target = chat_id or self.chat_id
        if not target or not self._loop or not self._app:
            return
        try:
            future = asyncio.run_coroutine_threadsafe(
                self._app.bot.send_message(chat_id=target, text=text),
                self._loop
            )
            future.result(timeout=10)
        except Exception as e:
            print(f"⚠️ 텔레그램 전송 실패: {e}")

    def stop(self):
        if self._app and self._loop:
            asyncio.run_coroutine_threadsafe(self._app.stop(), self._loop)
