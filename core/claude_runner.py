"""
Claude Code CLI 기반 AI 엔진
- `claude -p` 서브프로세스로 실행
- --resume 으로 세션 연속성 유지
- --output-format json 으로 session_id 추적
- 스킬은 Python 래퍼 → 쉘 스크립트로 Claude Code에 노출
"""
import json
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional, Callable

CLAUDE_CMD = "claude"
CLAUDE_MODEL = "claude-opus-4-7"
CLAUDE_TIMEOUT = 120
WORK_DIR = str(Path(__file__).parent.parent)

# 세션 ID 저장 (chat_id → session_id)
# 음성 모드: chat_id=0, 텔레그램: chat_id=telegram_user_id
_sessions: Dict[int, str] = {}

SYSTEM_CONTEXT = """당신은 머스탱(Mustang)입니다. macOS 로컬 AI 어시스턴트입니다.

## 핵심 행동 원칙
- 사용자 요청을 받으면 추가 질문 없이 즉시 가장 합리적인 스킬을 실행합니다
- "이메일 체크해줘" → 바로 check_email 실행. "유튜브 틀어줘" → 바로 play_youtube 실행
- 절대 "어떤 것을 원하시나요?" "무엇을 도와드릴까요?" 같은 역질문을 하지 않습니다
- 스킬 실행 결과를 받은 후 한두 문장으로 자연스럽게 요약합니다
- 답변은 TTS로 읽히므로 이모지/마크다운/특수문자 사용 금지
- 항상 한국어로 답변합니다
- 숫자는 한글로 표현합니다 (5개 → 다섯 개)

## 스킬 실행 방법
python {work_dir}/run_skill.py <스킬명> '<JSON>'

## 사용 가능한 스킬
{skill_list}

## 실행 예시
- "이메일 체크" → python {work_dir}/run_skill.py check_email '{{"action":"read","count":5}}'
- "유튜브에서 마이클잭슨" → python {work_dir}/run_skill.py play_youtube '{{"query":"마이클잭슨"}}'
- "오늘 일정" → python {work_dir}/run_skill.py check_calendar '{{"action":"list","days":1}}'
- "문자 보내줘" → python {work_dir}/run_skill.py send_sms '{{"recipient":"이름","message":"내용"}}'
- "스크린샷" → python {work_dir}/run_skill.py control_screen '{{"action":"screenshot"}}'
"""


def _build_prompt(user_message: str, skill_list: str) -> str:
    context = SYSTEM_CONTEXT.format(
        skill_list=skill_list,
        work_dir=WORK_DIR,
    )
    return f"{context}\n\n사용자 요청: {user_message}\n\n(위 요청을 즉시 처리하세요. 추가 질문 없이 바로 스킬을 실행하세요.)"


class ClaudeRunner:
    def __init__(self, skill_list: str = "", skill_manager: Optional[object] = None):
        self.skill_list = skill_list
        self.skill_manager = skill_manager
        self._ensure_run_skill_script()

    def _ensure_run_skill_script(self):
        """Claude Code가 스킬을 쉘에서 실행할 수 있도록 래퍼 스크립트 생성"""
        script_path = Path(WORK_DIR) / "run_skill.py"
        script_content = '''#!/usr/bin/env python3
"""Claude Code CLI에서 스킬을 실행하는 래퍼"""
import sys, json, os
from pathlib import Path

# 스킬 로딩 메시지를 stderr로 보내서 Claude 응답과 섞이지 않게 함
os.environ["MUSTANG_QUIET"] = "1"

# .env 자동 로드 (Gmail 앱 비밀번호 등)
_env = Path(__file__).parent / "config" / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            if _v.strip():
                os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, str(Path(__file__).parent))
from core.skill_manager import SkillManager

if len(sys.argv) < 2:
    print("사용법: python run_skill.py <스킬명> [JSON파라미터]", file=sys.stderr)
    sys.exit(1)

skill_name = sys.argv[1]
params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

sm = SkillManager()
result = sm.execute(skill_name, params)
print(result)
'''
        script_path.write_text(script_content)

    def update_skill_list(self, skill_list: str):
        self.skill_list = skill_list

    def chat(self, user_message: str, chat_id: int = 0) -> str:
        """Claude Code CLI로 대화 처리 (세션 연속성 유지)"""
        prompt = _build_prompt(user_message, self.skill_list)
        return _ask_claude(chat_id, prompt)

    def reset_session(self, chat_id: int = 0):
        """세션 초기화"""
        _sessions.pop(chat_id, None)

    def run_shell(self, command: str) -> str:
        """쉘 명령어 직접 실행"""
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            out = result.stdout.strip()
            if result.returncode != 0:
                out += f"\n[오류] {result.stderr.strip()}"
            return out or "(출력 없음)"
        except subprocess.TimeoutExpired:
            return "명령 시간 초과"
        except Exception as e:
            return f"명령 오류: {e}"


# ── Claude Code CLI 호출 핵심 함수 ───────────────────────────────────────────

def _ask_claude(chat_id: int, prompt: str) -> str:
    session_id = _sessions.get(chat_id)

    args = [
        CLAUDE_CMD,
        "-p", prompt,
        "--dangerously-skip-permissions",
        "--output-format", "json",
        "--model", CLAUDE_MODEL,
    ]
    if session_id:
        args += ["--resume", session_id]

    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            encoding="utf-8",
            errors="ignore",
            cwd=WORK_DIR,
        )
    except subprocess.TimeoutExpired:
        return f"타임아웃: {CLAUDE_TIMEOUT}초 초과."
    except FileNotFoundError:
        return f"`{CLAUDE_CMD}` 를 찾을 수 없습니다. npm install -g @anthropic-ai/claude-code"
    except Exception as e:
        return f"실행 오류: {type(e).__name__}: {e}"

    raw_out = (proc.stdout or "").strip()
    raw_err = (proc.stderr or "").strip()

    if proc.returncode != 0 and not raw_out:
        return f"Claude 오류 (exit={proc.returncode}):\n{raw_err[:1500]}"

    try:
        data = json.loads(raw_out)
        new_sid = data.get("session_id") or session_id
        if new_sid:
            _sessions[chat_id] = new_sid
        result = (data.get("result") or "").strip()
        if not result and raw_err:
            return raw_err[:1500]
        return result or "(빈 응답)"
    except json.JSONDecodeError:
        return raw_out or raw_err or "(빈 응답)"


def reset_session(chat_id: int):
    _sessions.pop(chat_id, None)


def get_session_id(chat_id: int) -> Optional[str]:
    return _sessions.get(chat_id)
