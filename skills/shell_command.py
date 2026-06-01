"""
쉘 명령어 실행 스킬
터미널 명령어 실행 및 결과 반환
"""
import subprocess

SKILL_DEFINITION = {
    "name": "run_shell",
    "description": "터미널 쉘 명령어를 실행하고 결과를 반환합니다. 파일 관리, 시스템 정보, 앱 실행 등에 사용합니다.",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "실행할 쉘 명령어",
            },
            "timeout": {
                "type": "integer",
                "description": "타임아웃(초)",
                "default": 30,
            },
        },
        "required": ["command"],
    },
}


def execute(params: dict) -> str:
    command = params.get("command", "").strip()
    timeout = params.get("timeout", 30)

    if not command:
        return "명령어를 입력해주세요."

    # 위험한 명령어 차단 (기본 안전장치)
    dangerous = ["rm -rf /", "mkfs", "dd if=/dev/zero", ":(){:|:&};:"]
    for d in dangerous:
        if d in command:
            return f"위험한 명령어가 포함되어 있어 실행을 거부했습니다."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode == 0:
            return output or "명령이 성공적으로 실행되었습니다."
        else:
            return f"오류 (코드 {result.returncode}): {stderr or output}"

    except subprocess.TimeoutExpired:
        return f"명령 실행 시간이 {timeout}초를 초과했습니다."
    except Exception as e:
        return f"명령 실행 오류: {e}"
