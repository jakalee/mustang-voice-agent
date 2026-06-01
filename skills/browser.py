"""
웹브라우저 자동화 스킬
Playwright 기반 브라우저 제어
"""
import subprocess

SKILL_DEFINITION = {
    "name": "browser_automation",
    "description": "웹브라우저를 자동으로 제어합니다. URL 열기, 클릭, 텍스트 입력, 스크린샷, 페이지 내용 읽기 등을 수행합니다.",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["open", "click", "fill", "screenshot", "read_page", "scroll", "back", "close"],
                "description": "수행할 브라우저 동작",
            },
            "url": {"type": "string", "description": "열 URL"},
            "selector": {"type": "string", "description": "CSS 셀렉터 또는 텍스트"},
            "text": {"type": "string", "description": "입력할 텍스트"},
            "headless": {"type": "boolean", "description": "헤드리스 모드 여부", "default": False},
        },
        "required": ["action"],
    },
}

_browser_instance = None
_page_instance = None


def _get_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError:
        return None


def execute(params: dict) -> str:
    action = params.get("action", "")

    # 간단한 URL 열기는 macOS open 명령으로
    if action == "open":
        url = params.get("url", "")
        if not url:
            return "URL을 지정해주세요."
        try:
            subprocess.run(["open", url], check=True, timeout=10)
            return f"브라우저에서 '{url}'을 열었습니다."
        except Exception as e:
            return f"URL 열기 실패: {e}"

    # 고급 자동화는 Playwright 사용
    sync_playwright = _get_playwright()
    if not sync_playwright:
        return "Playwright가 설치되지 않았습니다. 'pip install playwright && playwright install chromium'을 실행하세요."

    return _playwright_action(sync_playwright, params)


def _playwright_action(sync_playwright, params: dict) -> str:
    action = params.get("action", "")
    headless = params.get("headless", False)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()

            if action == "read_page":
                url = params.get("url", "")
                if url:
                    page.goto(url, timeout=30000)
                content = page.inner_text("body")[:2000]
                browser.close()
                return f"페이지 내용:\n{content}"

            elif action == "screenshot":
                url = params.get("url", "")
                if url:
                    page.goto(url, timeout=30000)
                from pathlib import Path
                import time
                path = Path(__file__).parent.parent / "data" / "screenshots" / f"browser_{int(time.time())}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(path))
                browser.close()
                return f"스크린샷 저장됨: {path}"

            elif action == "click":
                selector = params.get("selector", "")
                if selector:
                    page.click(selector)
                    browser.close()
                    return f"'{selector}' 클릭 완료"

            elif action == "fill":
                selector = params.get("selector", "")
                text = params.get("text", "")
                if selector and text:
                    page.fill(selector, text)
                    browser.close()
                    return f"텍스트 입력 완료"

            browser.close()
            return "작업 완료"

    except Exception as e:
        return f"브라우저 자동화 오류: {e}"
