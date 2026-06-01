"""
스킬 관리자
스킬 등록, 실행, 추가/삭제
"""
import importlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

SKILLS_DIR = Path(__file__).parent.parent / "skills"
SKILL_REGISTRY_FILE = Path(__file__).parent.parent / "config" / "skill_registry.json"


class SkillManager:
    def __init__(self):
        self._skills: Dict[str, dict] = {}
        self._executors: Dict[str, Callable] = {}
        self._load_registry()
        self._auto_load_builtin_skills()

    def _load_registry(self):
        SKILL_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if SKILL_REGISTRY_FILE.exists():
            try:
                data = json.loads(SKILL_REGISTRY_FILE.read_text())
                self._skills = data.get("skills", {})
            except Exception:
                self._skills = {}

    def _save_registry(self):
        data = {"skills": {k: {kk: vv for kk, vv in v.items()} for k, v in self._skills.items()}}
        SKILL_REGISTRY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _auto_load_builtin_skills(self):
        for skill_file in SKILLS_DIR.glob("*.py"):
            if skill_file.name.startswith("_") or skill_file.name == "base.py":
                continue
            try:
                self._load_skill_module(skill_file)
            except Exception as e:
                print(f"⚠️ 스킬 로드 실패 {skill_file.name}: {e}")

    def _load_skill_module(self, path: Path):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "SKILL_DEFINITION") and hasattr(module, "execute"):
            skill_def = module.SKILL_DEFINITION
            name = skill_def["name"]
            self._skills[name] = skill_def
            self._executors[name] = module.execute
            if not os.environ.get("MUSTANG_QUIET"):
                print(f"  ✅ 스킬 로드: {name}")

    def register(self, definition: dict, executor: Callable):
        name = definition["name"]
        self._skills[name] = definition
        self._executors[name] = executor
        self._save_registry()

    def execute(self, skill_name: str, params: dict) -> Any:
        if skill_name not in self._executors:
            return f"스킬 '{skill_name}'을 찾을 수 없습니다."
        try:
            return self._executors[skill_name](params)
        except Exception as e:
            return f"스킬 '{skill_name}' 실행 오류: {e}"

    def get_tool_definitions(self) -> List[dict]:
        tools = []
        for name, skill in self._skills.items():
            if skill.get("enabled", True):
                tools.append({
                    "name": skill["name"],
                    "description": skill["description"],
                    "input_schema": skill.get("input_schema", {"type": "object", "properties": {}}),
                })
        return tools

    def list_skills(self) -> str:
        enabled = [s for s in self._skills.values() if s.get("enabled", True)]
        disabled = [s for s in self._skills.values() if not s.get("enabled", True)]
        lines = ["사용 가능한 스킬:"]
        for s in enabled:
            lines.append(f"  - {s['name']}: {s['description']}")
        if disabled:
            lines.append("\n비활성 스킬:")
            for s in disabled:
                lines.append(f"  - {s['name']} (비활성)")
        return "\n".join(lines)

    def add_skill_from_file(self, path: str) -> str:
        p = Path(path)
        if not p.exists():
            return f"파일을 찾을 수 없습니다: {path}"
        try:
            import shutil
            dest = SKILLS_DIR / p.name
            shutil.copy2(p, dest)
            self._load_skill_module(dest)
            return f"스킬 '{p.stem}'이 추가되었습니다."
        except Exception as e:
            return f"스킬 추가 실패: {e}"

    def remove_skill(self, skill_name: str) -> str:
        if skill_name not in self._skills:
            return f"스킬 '{skill_name}'을 찾을 수 없습니다."
        skill_file = SKILLS_DIR / f"{skill_name}.py"
        if skill_file.exists():
            skill_file.unlink()
        del self._skills[skill_name]
        self._executors.pop(skill_name, None)
        self._save_registry()
        return f"스킬 '{skill_name}'이 삭제되었습니다."

    def enable_skill(self, skill_name: str, enabled: bool = True):
        if skill_name in self._skills:
            self._skills[skill_name]["enabled"] = enabled
            self._save_registry()
