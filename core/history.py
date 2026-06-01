"""
대화 히스토리 관리
세션별 대화 내용 저장 및 리셋
"""
import json
import time
from pathlib import Path
from typing import Optional, List, Dict

HISTORY_DIR = Path(__file__).parent.parent / "data" / "history"
MAX_HISTORY_MESSAGES = 50


class ConversationHistory:
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.messages: List[Dict] = []
        self.created_at = time.time()
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    def add_user(self, text: str):
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant(self, text: str):
        self.messages.append({"role": "assistant", "content": text})
        self._trim()

    def add_tool_result(self, tool_use_id: str, content: str):
        self.messages.append({
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_use_id, "content": content}]
        })
        self._trim()

    def _trim(self):
        if len(self.messages) > MAX_HISTORY_MESSAGES:
            self.messages = self.messages[-MAX_HISTORY_MESSAGES:]

    def reset(self):
        self.save()
        self.messages = []
        self.session_id = f"session_{int(time.time())}"
        self.created_at = time.time()
        print("🔄 대화 히스토리가 초기화되었습니다.")

    def save(self):
        path = HISTORY_DIR / f"{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "saved_at": time.time(),
            "messages": self.messages,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def load(self, session_id: str) -> bool:
        path = HISTORY_DIR / f"{session_id}.json"
        if not path.exists():
            return False
        data = json.loads(path.read_text())
        self.session_id = data["session_id"]
        self.created_at = data["created_at"]
        self.messages = data["messages"]
        return True

    def list_sessions(self) -> List[Dict]:
        sessions = []
        for f in sorted(HISTORY_DIR.glob("*.json"), reverse=True)[:10]:
            try:
                data = json.loads(f.read_text())
                sessions.append({
                    "id": data["session_id"],
                    "created_at": data["created_at"],
                    "message_count": len(data["messages"]),
                })
            except Exception:
                pass
        return sessions

    def get_messages_for_api(self) -> List[Dict]:
        return self.messages.copy()

    def summary(self) -> str:
        count = len(self.messages)
        user_count = sum(1 for m in self.messages if m["role"] == "user")
        return f"세션 {self.session_id}: 총 {count}개 메시지 ({user_count}회 대화)"
