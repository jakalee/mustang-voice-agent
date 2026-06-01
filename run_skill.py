#!/usr/bin/env python3
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
