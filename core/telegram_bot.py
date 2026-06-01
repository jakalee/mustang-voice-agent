"""
텔레그램 봇 인터페이스
텔레그램으로 머스탱에게 명령을 보내고 결과를 받음
"""
import asyncio
import threading
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

    def _setup(self):
        from telegram import Update
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

        app = ApplicationBuilder().token(self.token).build()

        async def start(update: Update, context):
            await update.message.reply_text(
                "머스탱 AI 봇입니다. 명령을 입력하세요.\n"
                "/reset - 대화 초기화\n"
                "/skills - 스킬 목록\n"
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

        async def handle_message(update: Update, context):
            if self.chat_id and str(update.effective_chat.id) != str(self.chat_id):
                await update.message.reply_text("권한이 없습니다.")
                return

            user_text = update.message.text
            await update.message.reply_text("처리 중...")

            if self.command_handler:
                result = self.command_handler(user_text)
                await update.message.reply_text(result or "처리 완료")

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("reset", reset_cmd))
        app.add_handler(CommandHandler("skills", skills_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        return app

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
