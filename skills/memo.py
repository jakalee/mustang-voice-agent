"""
메모 스킬
"기억해줘" / "뭐 기억하고 있어?" 음성 명령으로 메모 저장 및 조회
"""
import json
from datetime import datetime
from pathlib import Path

MEMO_FILE = Path(__file__).parent.parent / "data" / "memos.json"

SKILL_DEFINITION = {
    "name": "memo",
    "description": (
        "메모를 저장하거나 저장된 메모를 조회합니다. "
        "'기억해줘', '메모해줘', '저장해줘' 같은 요청은 action=save로, "
        "'뭐 기억해', '메모 뭐 있어', '저장된 거 알려줘' 같은 요청은 action=list로, "
        "'메모 삭제', '다 지워줘' 는 action=clear로 처리합니다."
    ),
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["save", "list", "clear"],
                "description": "수행할 동작: save(저장), list(조회), clear(전체 삭제)",
            },
            "content": {
                "type": "string",
                "description": "저장할 메모 내용 (action=save일 때 필수)",
            },
        },
        "required": ["action"],
    },
}


def _load() -> list:
    if MEMO_FILE.exists():
        try:
            return json.loads(MEMO_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(memos: list):
    MEMO_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMO_FILE.write_text(json.dumps(memos, ensure_ascii=False, indent=2), encoding="utf-8")


def execute(params: dict) -> str:
    action = params.get("action", "list")
    memos = _load()

    if action == "save":
        content = params.get("content", "").strip()
        if not content:
            return "저장할 내용을 말씀해주세요."
        entry = {"text": content, "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
        memos.append(entry)
        _save(memos)
        return f"기억했어요: {content}"

    elif action == "list":
        if not memos:
            return "저장된 메모가 없어요."
        lines = [f"{i+1}. {m['text']} ({m['time']})" for i, m in enumerate(memos)]
        return "기억하고 있는 내용이에요:\n" + "\n".join(lines)

    elif action == "clear":
        _save([])
        return "메모를 모두 지웠어요."

    return "알 수 없는 동작이에요."
