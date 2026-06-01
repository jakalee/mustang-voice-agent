"""
문자 메시지 스킬
AppleScript로 macOS 메시지 앱을 통해 SMS/iMessage 전송
"""
import subprocess

SKILL_DEFINITION = {
    "name": "send_sms",
    "description": "애플 메시지 앱으로 문자 메시지를 보냅니다",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "recipient": {
                "type": "string",
                "description": "수신자 이름 또는 전화번호",
            },
            "message": {
                "type": "string",
                "description": "보낼 메시지 내용",
            },
        },
        "required": ["recipient", "message"],
    },
}


def execute(params: dict) -> str:
    recipient = params.get("recipient", "").strip()
    message = params.get("message", "").strip()

    if not recipient or not message:
        return "수신자와 메시지를 입력해주세요."

    # 메시지 내용 이스케이프
    safe_message = message.replace('"', '\\"').replace("'", "\\'")
    safe_recipient = recipient.replace('"', '\\"')

    applescript = f"""
    tell application "Messages"
        activate
        set targetService to 1st service whose service type = iMessage
        set targetBuddy to buddy "{safe_recipient}" of targetService
        send "{safe_message}" to targetBuddy
    end tell
    """

    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return f"{recipient}에게 메시지를 전송했습니다."
        else:
            # 폴백: 전화번호로 시도
            applescript_fallback = f"""
            tell application "Messages"
                activate
                send "{safe_message}" to participant "{safe_recipient}" of front chat
            end tell
            """
            result2 = subprocess.run(
                ["osascript", "-e", applescript_fallback],
                capture_output=True, text=True, timeout=15,
            )
            if result2.returncode == 0:
                return f"메시지를 전송했습니다."
            return f"메시지 전송 실패: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "메시지 전송 시간이 초과되었습니다."
    except Exception as e:
        return f"메시지 전송 오류: {e}"


def check_new_messages() -> str:
    """최근 수신 메시지 확인"""
    applescript = """
    tell application "Messages"
        set recentChats to (chats whose has unread messages is true)
        set msgCount to count of recentChats
        if msgCount = 0 then
            return "읽지 않은 메시지가 없습니다."
        end if
        set resultText to msgCount & "개의 읽지 않은 대화가 있습니다."
        return resultText as string
    end tell
    """
    try:
        result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True, timeout=10)
        return result.stdout.strip() or "메시지 확인 완료"
    except Exception as e:
        return f"메시지 확인 오류: {e}"
