"""
YouTube 재생 스킬
Safari/Chrome으로 YouTube 검색 및 재생
"""
import subprocess
import urllib.parse

SKILL_DEFINITION = {
    "name": "play_youtube",
    "description": "YouTube에서 음악이나 동영상을 검색하여 Safari 브라우저로 재생합니다",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "검색할 음악 또는 동영상 제목/키워드",
            },
            "autoplay": {
                "type": "boolean",
                "description": "첫 번째 결과 자동 재생 여부",
                "default": True,
            },
        },
        "required": ["query"],
    },
}


def execute(params: dict) -> str:
    query = params.get("query", "")
    if not query:
        return "검색어를 입력해주세요."

    encoded_query = urllib.parse.quote(query)
    # YouTube 검색 URL
    search_url = f"https://www.youtube.com/results?search_query={encoded_query}"

    # AppleScript로 Safari에서 열기
    applescript = f"""
    tell application "Safari"
        activate
        if (count of windows) = 0 then
            make new document
        end if
        set URL of current tab of front window to "{search_url}"
    end tell

    delay 3

    tell application "System Events"
        tell process "Safari"
            -- 첫 번째 동영상 클릭 (키보드 단축키)
            keystroke tab
            delay 0.5
        end tell
    end tell
    """

    try:
        subprocess.run(["open", "-a", "Google Chrome", search_url], check=True)
        return f"Chrome에서 YouTube '{query}' 검색을 열었습니다."
    except Exception:
        try:
            subprocess.run(["open", search_url], check=True)
            return f"YouTube에서 '{query}'를 검색했습니다."
        except Exception as e2:
            return f"YouTube 열기 실패: {e2}"
