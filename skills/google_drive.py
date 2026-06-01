"""
Google Drive 스킬 - 로컬 Google Drive 폴더 기반
Google Drive for Desktop 앱이 설치된 경우 사용
"""
import os
import subprocess
from pathlib import Path

SKILL_DEFINITION = {
    "name": "google_drive",
    "description": "Google Drive에서 파일을 검색하거나 열거나 목록을 조회합니다",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "search", "open"],
                "default": "list",
            },
            "query": {"type": "string", "description": "검색할 파일명"},
            "count": {"type": "integer", "default": 10},
        },
        "required": ["action"],
    },
}

# Google Drive for Desktop 기본 마운트 경로들
DRIVE_PATHS = [
    os.environ.get("GOOGLE_DRIVE_PATH", ""),
    "/Users/jakallee/Library/CloudStorage/GoogleDrive-emiemc@gmail.com/My Drive",
    "/Users/jakallee/Library/CloudStorage/GoogleDrive-emiemc@gmail.com",
    "/Volumes/GoogleDrive/My Drive",
    str(Path.home() / "Google Drive"),
]


def _find_drive_root() -> str:
    for p in DRIVE_PATHS:
        if p and Path(p).exists():
            return p
    return ""


def execute(params: dict) -> str:
    action = params.get("action", "list")
    drive_root = _find_drive_root()

    if not drive_root:
        return (
            "Google Drive 폴더를 찾을 수 없습니다. "
            "Google Drive for Desktop 앱을 설치하거나 "
            "config/.env 에 GOOGLE_DRIVE_PATH를 설정하세요."
        )

    if action == "list":
        return _list_files(drive_root, params.get("count", 10))
    elif action == "search":
        return _search_files(drive_root, params.get("query", ""), params.get("count", 10))
    elif action == "open":
        return _open_drive(drive_root)
    return f"알 수 없는 동작: {action}"


def _list_files(root: str, count: int) -> str:
    try:
        result = subprocess.run(
            ["find", root, "-maxdepth", "2", "-type", "f",
             "!", "-name", ".*"],
            capture_output=True, text=True, timeout=10
        )
        files = [Path(f).name for f in result.stdout.splitlines() if f]
        files = files[:count]
        if not files:
            return "Drive에 파일이 없습니다."
        return f"Drive 파일 {len(files)}개: " + ", ".join(files[:7])
    except Exception as e:
        return f"Drive 목록 조회 오류: {e}"


def _search_files(root: str, query: str, count: int) -> str:
    if not query:
        return "검색어를 입력해주세요."
    try:
        result = subprocess.run(
            ["find", root, "-iname", f"*{query}*", "-type", "f"],
            capture_output=True, text=True, timeout=10
        )
        files = [Path(f) for f in result.stdout.splitlines() if f][:count]
        if not files:
            return f"'{query}' 파일을 찾지 못했습니다."
        names = [f.name for f in files]
        return f"'{query}' 검색 결과 {len(names)}개: " + ", ".join(names[:5])
    except Exception as e:
        return f"Drive 검색 오류: {e}"


def _open_drive(root: str) -> str:
    subprocess.run(["open", root], check=True)
    return "Google Drive 폴더를 열었습니다."
