"""
시스템 상태 스킬
배터리, CPU, 메모리 상태를 음성으로 보고
"""
import psutil

SKILL_DEFINITION = {
    "name": "system_status",
    "description": (
        "맥의 시스템 상태를 알려줍니다. "
        "'배터리 얼마야', '충전 얼마나 됐어' → type=battery, "
        "'CPU 얼마야', '프로세서 상태' → type=cpu, "
        "'메모리 얼마야', '램 상태' → type=memory, "
        "'시스템 상태 전체' → type=all"
    ),
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["battery", "cpu", "memory", "all"],
                "description": "조회할 항목",
            },
        },
        "required": ["type"],
    },
}


def execute(params: dict) -> str:
    kind = params.get("type", "all")
    parts = []

    if kind in ("battery", "all"):
        battery = psutil.sensors_battery()
        if battery:
            pct = int(battery.percent)
            charging = "충전 중" if battery.power_plugged else "배터리 사용 중"
            parts.append(f"배터리 {pct}%, {charging}")
        else:
            parts.append("배터리 정보를 가져올 수 없어요")

    if kind in ("cpu", "all"):
        cpu = psutil.cpu_percent(interval=0.5)
        parts.append(f"CPU 사용률 {cpu}%")

    if kind in ("memory", "all"):
        mem = psutil.virtual_memory()
        used_gb = mem.used / 1024**3
        total_gb = mem.total / 1024**3
        parts.append(f"메모리 {used_gb:.1f}GB / {total_gb:.1f}GB 사용 중 ({mem.percent}%)")

    return ", ".join(parts) if parts else "정보를 가져올 수 없어요."
