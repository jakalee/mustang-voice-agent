"""
YouTube 재생 스킬
yt-dlp로 첫 번째 검색 결과 video ID 추출 →
기존 Chrome(로그인 쿠키/YouTube Premium)으로 열어 광고 없이 재생
"""
import subprocess
import urllib.parse
from typing import Optional


SKILL_DEFINITION = {
    "name": "play_youtube",
    "description": "YouTube에서 음악이나 동영상을 검색하여 첫 번째 영상을 Chrome으로 재생합니다",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "검색할 음악 또는 동영상 제목/키워드",
            },
        },
        "required": ["query"],
    },
}


def _get_video_id(query: str) -> Optional[str]:
    """yt-dlp로 첫 번째 검색 결과 video ID 반환"""
    try:
        result = subprocess.run(
            ["yt-dlp", f"ytsearch1:{query}", "--get-id", "--no-playlist", "-q"],
            capture_output=True, text=True, timeout=15,
        )
        vid_id = result.stdout.strip().splitlines()[0] if result.stdout.strip() else None
        return vid_id
    except Exception:
        return None


def _open_in_chrome(url: str):
    """기존 Chrome(로그인 세션/쿠키 유지)으로 URL 열기"""
    try:
        # AppleScript로 기존 Chrome 창에서 열기 (새 탭)
        script = f'''
        tell application "Google Chrome"
            activate
            if (count of windows) > 0 then
                tell front window
                    set newTab to make new tab
                    set URL of newTab to "{url}"
                end tell
            else
                open location "{url}"
            end if
        end tell
        '''
        subprocess.run(["osascript", "-e", script],
                       capture_output=True, timeout=8)
    except Exception:
        # 폴백: open 명령
        try:
            subprocess.run(["open", "-a", "Google Chrome", url], check=True)
        except Exception:
            subprocess.run(["open", url])


def execute(params: dict) -> str:
    query = params.get("query", "").strip()
    if not query:
        return "검색어를 입력해주세요."

    # 1순위: yt-dlp로 video ID 추출 → 기존 Chrome으로 열기
    vid_id = _get_video_id(query)
    if vid_id:
        url = f"https://www.youtube.com/watch?v={vid_id}"
        _open_in_chrome(url)
        return f"YouTube에서 '{query}' 재생을 시작했습니다."

    # 폴백: 검색 페이지를 기존 Chrome으로 열기
    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    _open_in_chrome(search_url)
    return f"yt-dlp로 영상을 찾지 못해 검색 페이지를 열었습니다. (pip install yt-dlp 로 설치 가능)"
