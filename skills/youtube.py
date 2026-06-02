"""
YouTube 재생 스킬
Playwright로 YouTube 검색 후 첫 번째 영상을 자동 클릭하여 재생
"""
import subprocess
from typing import Optional

SKILL_DEFINITION = {
    "name": "play_youtube",
    "description": "YouTube에서 음악이나 동영상을 검색하여 첫 번째 영상을 자동으로 클릭 재생합니다",
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


def _play_with_playwright(query: str) -> Optional[str]:
    """Playwright로 YouTube 검색 후 첫 번째 영상 클릭"""
    try:
        from playwright.sync_api import sync_playwright
        import urllib.parse

        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"

        with sync_playwright() as p:
            # 기존 Chrome 프로필 사용 (로그인 상태 유지)
            try:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir="/tmp/mustang-chrome",
                    headless=False,
                    channel="chrome",
                    args=["--start-maximized"],
                )
                page = browser.pages[0] if browser.pages else browser.new_page()
            except Exception:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

            page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1500)

            # 첫 번째 영상 썸네일 또는 제목 클릭
            first_video = page.locator("ytd-video-renderer a#thumbnail").first
            title = page.locator("ytd-video-renderer #video-title").first.inner_text(timeout=5000)
            first_video.click()

            page.wait_for_timeout(2000)
            # 브라우저는 열어둔 채로 유지 (close 안 함)
            return title.strip()

    except Exception as e:
        return None


def _play_with_ytdlp(query: str) -> Optional[str]:
    """yt-dlp로 video ID 추출 후 브라우저로 열기 (폴백)"""
    try:
        result = subprocess.run(
            ["yt-dlp", f"ytsearch1:{query}", "--get-id", "--no-playlist"],
            capture_output=True, text=True, timeout=15,
        )
        vid_id = result.stdout.strip().splitlines()[0] if result.stdout.strip() else None
        if vid_id:
            url = f"https://www.youtube.com/watch?v={vid_id}"
            try:
                subprocess.run(["open", "-a", "Google Chrome", url], check=True)
            except Exception:
                subprocess.run(["open", url])
            return url
    except Exception:
        pass
    return None


def execute(params: dict) -> str:
    query = params.get("query", "").strip()
    if not query:
        return "검색어를 입력해주세요."

    # 1순위: Playwright로 검색 → 첫 영상 자동 클릭
    title = _play_with_playwright(query)
    if title:
        return f"YouTube에서 '{title}' 재생을 시작했습니다."

    # 2순위: yt-dlp로 URL 추출 후 브라우저로 열기
    url = _play_with_ytdlp(query)
    if url:
        return f"YouTube에서 '{query}' 재생을 시작했습니다."

    # 3순위: 검색 페이지만 열기
    import urllib.parse
    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    try:
        subprocess.run(["open", "-a", "Google Chrome", search_url], check=True)
    except Exception:
        subprocess.run(["open", search_url])
    return f"YouTube 검색 페이지를 열었습니다. '{query}'"
