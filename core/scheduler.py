"""
크론 스케줄러
APScheduler 기반 작업 예약
"""
import json
import time
from pathlib import Path
from typing import Callable, Optional, Dict

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

SCHEDULE_FILE = Path(__file__).parent.parent / "config" / "schedules.json"


class TaskScheduler:
    def __init__(self, task_runner: Optional[Callable] = None):
        self.scheduler = BackgroundScheduler()
        self.task_runner = task_runner
        self._tasks: Dict[str, dict] = {}
        self._load_schedules()
        self.scheduler.start()

    def _load_schedules(self):
        SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if SCHEDULE_FILE.exists():
            try:
                self._tasks = json.loads(SCHEDULE_FILE.read_text())
                for task_id, task in self._tasks.items():
                    self._register_job(task_id, task)
            except Exception as e:
                print(f"⚠️ 스케줄 로드 실패: {e}")

    def _save_schedules(self):
        SCHEDULE_FILE.write_text(json.dumps(self._tasks, ensure_ascii=False, indent=2))

    def _register_job(self, task_id: str, task: dict):
        def job():
            print(f"\n⏰ 예약 작업 실행: {task['name']}")
            if self.task_runner:
                self.task_runner(task["command"])

        cron_expr = task.get("cron", "")
        if cron_expr:
            parts = cron_expr.split()
            if len(parts) == 5:
                minute, hour, day, month, day_of_week = parts
                trigger = CronTrigger(
                    minute=minute, hour=hour, day=day,
                    month=month, day_of_week=day_of_week
                )
            else:
                return
        else:
            interval = task.get("interval_minutes", 60)
            trigger = IntervalTrigger(minutes=interval)

        try:
            self.scheduler.add_job(job, trigger, id=task_id, replace_existing=True)
        except Exception as e:
            print(f"⚠️ 작업 등록 실패 {task_id}: {e}")

    def add_task(self, name: str, command: str,
                 cron: Optional[str] = None,
                 interval_minutes: Optional[int] = None) -> str:
        task_id = f"task_{int(time.time())}"
        task = {
            "id": task_id,
            "name": name,
            "command": command,
            "created_at": time.time(),
        }
        if cron:
            task["cron"] = cron
        elif interval_minutes:
            task["interval_minutes"] = interval_minutes
        else:
            return "크론 표현식 또는 반복 간격을 지정하세요."

        self._tasks[task_id] = task
        self._register_job(task_id, task)
        self._save_schedules()
        return f"작업 '{name}'이 예약되었습니다. (ID: {task_id})"

    def remove_task(self, task_id: str) -> str:
        if task_id not in self._tasks:
            return f"작업 '{task_id}'를 찾을 수 없습니다."
        self.scheduler.remove_job(task_id)
        del self._tasks[task_id]
        self._save_schedules()
        return f"작업 '{task_id}'가 삭제되었습니다."

    def list_tasks(self) -> str:
        if not self._tasks:
            return "예약된 작업이 없습니다."
        lines = ["예약된 작업 목록:"]
        for task in self._tasks.values():
            schedule = task.get("cron") or f"{task.get('interval_minutes', '?')}분마다"
            lines.append(f"  [{task['id']}] {task['name']} - {schedule}")
        return "\n".join(lines)

    def shutdown(self):
        self.scheduler.shutdown(wait=False)
