"""
작업 예약 스킬
크론 스케줄링으로 반복 작업 설정
"""
SKILL_DEFINITION = {
    "name": "schedule_task",
    "description": "작업을 특정 시간이나 반복 주기로 예약합니다. 예: '매일 오전 9시에 이메일 확인', '30분마다 알림'",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "remove", "list"],
                "description": "add(추가), remove(삭제), list(목록)",
                "default": "list",
            },
            "name": {"type": "string", "description": "작업 이름"},
            "command": {"type": "string", "description": "실행할 명령 또는 스킬"},
            "cron": {
                "type": "string",
                "description": "크론 표현식 (분 시 일 월 요일), 예: '0 9 * * *' (매일 9시)",
            },
            "interval_minutes": {
                "type": "integer",
                "description": "반복 간격(분)",
            },
            "task_id": {"type": "string", "description": "삭제할 작업 ID"},
        },
        "required": ["action"],
    },
}

_scheduler = None


def _get_scheduler():
    global _scheduler
    return _scheduler


def set_scheduler(scheduler):
    global _scheduler
    _scheduler = scheduler


def execute(params: dict) -> str:
    action = params.get("action", "list")
    scheduler = _get_scheduler()

    if not scheduler:
        return "스케줄러가 초기화되지 않았습니다."

    if action == "list":
        return scheduler.list_tasks()
    elif action == "add":
        name = params.get("name", "")
        command = params.get("command", "")
        cron = params.get("cron")
        interval = params.get("interval_minutes")
        if not name or not command:
            return "작업 이름과 명령을 입력해주세요."
        return scheduler.add_task(name, command, cron=cron, interval_minutes=interval)
    elif action == "remove":
        task_id = params.get("task_id", "")
        if not task_id:
            return "삭제할 작업 ID를 입력해주세요."
        return scheduler.remove_task(task_id)
    else:
        return f"알 수 없는 동작: {action}"
