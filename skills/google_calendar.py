"""
캘린더 스킬 - macOS 캘린더 앱 AppleScript
Google 계정이 macOS에 연동되면 Google 캘린더도 자동 반영
"""
import subprocess
from datetime import datetime, timedelta

SKILL_DEFINITION = {
    "name": "check_calendar",
    "description": "캘린더 일정을 확인하거나 새 일정을 추가합니다. macOS 캘린더 앱 사용 (Google 캘린더 자동 연동)",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "add"],
                "default": "list",
            },
            "days":    {"type": "integer", "default": 7, "description": "조회할 일수"},
            "title":   {"type": "string",  "description": "일정 제목 (add 시)"},
            "date":    {"type": "string",  "description": "날짜 YYYY-MM-DD (add 시)"},
            "time":    {"type": "string",  "description": "시간 HH:MM (add 시)"},
            "duration_minutes": {"type": "integer", "default": 60},
        },
        "required": ["action"],
    },
}


def execute(params: dict) -> str:
    action = params.get("action", "list")
    if action == "list":
        return _list_events(params.get("days", 7))
    elif action == "add":
        return _add_event(params)
    return f"알 수 없는 동작: {action}"


def _list_events(days: int) -> str:
    now = datetime.now()
    end = now + timedelta(days=days)

    # AppleScript: 오늘부터 N일간 일정 조회
    script = f"""
    set startDate to (current date)
    set endDate to startDate + ({days} * days)
    set resultList to {{}}

    tell application "Calendar"
        repeat with cal in every calendar
            set evts to (every event of cal whose start date >= startDate and start date <= endDate)
            repeat with evt in evts
                set evtTitle to summary of evt
                set evtStart to start date of evt
                set evtStr to (evtTitle & "|" & (evtStart as string))
                set end of resultList to evtStr
            end repeat
        end repeat
    end tell

    set AppleScript's text item delimiters to "\\n"
    return resultList as text
    """

    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
    output = result.stdout.strip()

    if not output:
        return f"앞으로 {days}일간 예정된 일정이 없습니다."

    lines = [l for l in output.splitlines() if "|" in l]
    if not lines:
        return f"앞으로 {days}일간 예정된 일정이 없습니다."

    summaries = []
    for line in lines[:7]:
        parts = line.split("|", 1)
        title = parts[0].strip()
        date_str = parts[1].strip() if len(parts) > 1 else ""
        # 날짜 파싱 시도
        try:
            # macOS 날짜 형식: "Monday, May 19, 2025 at 9:00:00 AM"
            for fmt in ["%A, %B %d, %Y at %I:%M:%S %p", "%Y-%m-%d %H:%M:%S"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    date_str = dt.strftime("%-m월 %-d일 %H시 %M분")
                    break
                except ValueError:
                    pass
        except Exception:
            pass
        summaries.append(f"{date_str}에 {title}")

    return f"앞으로 {days}일간 {len(lines)}개 일정이 있습니다. " + ". ".join(summaries[:5])


def _add_event(params: dict) -> str:
    title    = params.get("title", "")
    date_str = params.get("date", "")
    time_str = params.get("time", "09:00")
    duration = params.get("duration_minutes", 60)

    if not title or not date_str:
        return "일정 제목과 날짜를 입력해주세요."

    try:
        dt_start = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        dt_end   = dt_start + timedelta(minutes=duration)
    except ValueError:
        return "날짜 형식이 올바르지 않습니다. (예: 2025-05-20, 14:00)"

    def _fmt(dt):
        return dt.strftime("%B %d, %Y %I:%M:%S %p")

    script = f"""
    tell application "Calendar"
        tell calendar 1
            make new event with properties {{¬
                summary:"{title}",¬
                start date:(date "{_fmt(dt_start)}"),¬
                end date:(date "{_fmt(dt_end)}")}}
        end tell
    end tell
    return "ok"
    """

    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
    if result.returncode == 0:
        return f"{date_str} {time_str}에 '{title}' 일정을 추가했습니다."
    return f"일정 추가 실패: {result.stderr.strip()}"
