"""
화면 제어 스킬
PyAutoGUI + AppleScript로 macOS 화면 제어
스크린샷, 마우스 클릭, 키보드 입력, 앱 실행, 화면 Vision 분석, 접근성 UI 읽기
"""
import subprocess
import time
import base64
import os
from pathlib import Path

SCREENSHOT_DIR = Path(__file__).parent.parent / "data" / "screenshots"

SKILL_DEFINITION = {
    "name": "control_screen",
    "description": "컴퓨터 화면을 제어합니다. 스크린샷 촬영, 마우스 클릭, 키보드 입력, 앱 실행 등을 수행합니다.",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["screenshot", "click", "double_click", "type", "key", "scroll", "open_app", "run_shortcut", "get_frontmost_app", "analyze_screen", "get_ui_elements"],
                "description": "수행할 동작. analyze_screen: 화면을 보고 AI가 설명/분석. get_ui_elements: 현재 앱 UI 구조 반환.",
            },
            "question": {"type": "string", "description": "analyze_screen 시 화면에 대해 물어볼 질문"},
            "x": {"type": "number", "description": "클릭할 X 좌표"},
            "y": {"type": "number", "description": "클릭할 Y 좌표"},
            "text": {"type": "string", "description": "입력할 텍스트 또는 앱 이름"},
            "key": {"type": "string", "description": "누를 키 (예: cmd+c, return, escape)"},
            "direction": {"type": "string", "enum": ["up", "down", "left", "right"]},
            "amount": {"type": "number", "description": "스크롤 양"},
        },
        "required": ["action"],
    },
}


def execute(params: dict) -> str:
    action = params.get("action", "")

    if action == "screenshot":
        return _screenshot()
    elif action == "click":
        return _click(params.get("x", 0), params.get("y", 0))
    elif action == "double_click":
        return _double_click(params.get("x", 0), params.get("y", 0))
    elif action == "type":
        return _type_text(params.get("text", ""))
    elif action == "key":
        return _press_key(params.get("key", ""))
    elif action == "scroll":
        return _scroll(params.get("direction", "down"), params.get("amount", 3))
    elif action == "open_app":
        return _open_app(params.get("text", ""))
    elif action == "run_shortcut":
        return _run_shortcut(params.get("text", ""))
    elif action == "get_frontmost_app":
        return _get_frontmost_app()
    elif action == "analyze_screen":
        return _analyze_screen(params.get("question", "지금 화면에 무엇이 보이나요? 한국어로 간결하게 설명해주세요."))
    elif action == "get_ui_elements":
        return _get_ui_elements()
    else:
        return f"알 수 없는 동작: {action}"


def _screenshot() -> str:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    path = SCREENSHOT_DIR / f"screenshot_{ts}.png"
    try:
        subprocess.run(["screencapture", "-x", str(path)], check=True, timeout=10)
        return f"스크린샷 저장됨: {path}"
    except Exception as e:
        return f"스크린샷 실패: {e}"


def _click(x: float, y: float) -> str:
    try:
        import pyautogui
        pyautogui.click(int(x), int(y))
        return f"({int(x)}, {int(y)}) 클릭 완료"
    except ImportError:
        # AppleScript 폴백
        script = f'tell application "System Events" to click at {{{int(x)}, {int(y)}}}'
        subprocess.run(["osascript", "-e", script], capture_output=True)
        return f"({int(x)}, {int(y)}) 클릭 완료"
    except Exception as e:
        return f"클릭 실패: {e}"


def _double_click(x: float, y: float) -> str:
    try:
        import pyautogui
        pyautogui.doubleClick(int(x), int(y))
        return f"({int(x)}, {int(y)}) 더블클릭 완료"
    except Exception as e:
        return f"더블클릭 실패: {e}"


def _type_text(text: str) -> str:
    if not text:
        return "입력할 텍스트가 없습니다."
    try:
        import pyautogui
        pyautogui.write(text, interval=0.05)
        return f"텍스트 입력 완료: {text[:30]}"
    except ImportError:
        script = f'tell application "System Events" to keystroke "{text}"'
        subprocess.run(["osascript", "-e", script], capture_output=True)
        return f"텍스트 입력 완료"
    except Exception as e:
        return f"텍스트 입력 실패: {e}"


def _press_key(key: str) -> str:
    if not key:
        return "키를 지정해주세요."
    try:
        # AppleScript로 키 입력 (한국어 포함 안전)
        key_map = {
            "return": "return", "enter": "return", "escape": "escape",
            "tab": "tab", "space": "space", "delete": "delete",
            "up": "up arrow", "down": "down arrow",
            "left": "left arrow", "right": "right arrow",
        }

        if "+" in key:
            # 수식키 조합 (예: cmd+c)
            parts = key.split("+")
            modifier_map = {"cmd": "command", "ctrl": "control", "alt": "option", "shift": "shift"}
            modifiers = [modifier_map.get(p, p) for p in parts[:-1]]
            actual_key = parts[-1]
            mod_str = " using {" + ", ".join(f"{m} down" for m in modifiers) + "}"
            script = f'tell application "System Events" to keystroke "{actual_key}"{mod_str}'
        else:
            mapped = key_map.get(key.lower(), key)
            script = f'tell application "System Events" to key code (key code of {mapped})'
            # 더 안전한 방법
            script = f'tell application "System Events" to keystroke "{key}"'

        subprocess.run(["osascript", "-e", script], capture_output=True)
        return f"키 입력 완료: {key}"
    except Exception as e:
        return f"키 입력 실패: {e}"


def _scroll(direction: str, amount: float) -> str:
    try:
        import pyautogui
        dy = -int(amount) if direction == "down" else int(amount)
        dx = -int(amount) if direction == "right" else (int(amount) if direction == "left" else 0)
        pyautogui.scroll(dy)
        return f"{direction} 방향으로 스크롤 완료"
    except Exception as e:
        return f"스크롤 실패: {e}"


def _open_app(app_name: str) -> str:
    if not app_name:
        return "앱 이름을 지정해주세요."
    try:
        subprocess.run(["open", "-a", app_name], check=True, timeout=10)
        return f"'{app_name}' 앱을 열었습니다."
    except Exception as e:
        return f"앱 열기 실패: {e}"


def _run_shortcut(shortcut_name: str) -> str:
    """macOS 단축어(Shortcuts) 실행"""
    try:
        subprocess.run(["shortcuts", "run", shortcut_name], check=True, timeout=30)
        return f"단축어 '{shortcut_name}' 실행 완료"
    except Exception as e:
        return f"단축어 실행 실패: {e}"


def _get_frontmost_app() -> str:
    script = """
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        return frontApp
    end tell
    """
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return f"현재 활성 앱: {result.stdout.strip()}"


def _analyze_screen(question: str) -> str:
    """스크린샷을 찍어 Claude Vision으로 분석"""
    import tempfile
    try:
        import anthropic
    except ImportError:
        return "anthropic 패키지가 필요합니다: pip install anthropic"

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name

    try:
        subprocess.run(["screencapture", "-x", tmp_path], check=True, timeout=10)
        with open(tmp_path, "rb") as f:
            img_data = base64.standard_b64encode(f.read()).decode("utf-8")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    try:
        msg = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_data}},
                    {"type": "text", "text": f"{question}\n\n답변은 TTS로 읽히므로 이모지/마크다운 없이 한국어로 간결하게 두세 문장으로만 말해주세요."},
                ],
            }],
        )
        return msg.content[0].text
    except Exception as e:
        return f"화면 분석 실패: {e}"


def _get_ui_elements() -> str:
    """접근성 API로 현재 앱의 창 제목과 메뉴 항목을 반환"""
    script = """
    tell application "System Events"
        set frontProc to first application process whose frontmost is true
        set appName to name of frontProc
        set result to "앱: " & appName
        try
            set winTitle to name of window 1 of frontProc
            set result to result & ", 창: " & winTitle
        end try
        try
            set menuNames to name of every menu bar item of menu bar 1 of frontProc
            set result to result & ", 메뉴: " & (menuNames as string)
        end try
        return result
    end tell
    """
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=5)
        info = r.stdout.strip()
        if not info:
            return "UI 정보를 가져올 수 없습니다. (접근성 권한이 필요할 수 있습니다)"
        return info
    except Exception as e:
        return f"UI 요소 읽기 실패: {e}"
