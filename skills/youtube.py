"""
YouTube 재생 스킬
yt-dlp로 첫 번째 검색 결과 URL을 가져와 브라우저로 바로 재생
"""
import subprocess
import urllib.parse

SKILL_DEFINITION = {
    "name": "play_youtube",
    "description": "YouTube에서 음악이나 동영상을 검색하여 브라우저로 바로 재생합니다",
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


def _get_video_url(query: str) -> str | None:
    """yt-dlp로 첫 번째 검색 결과 URL 반환"""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                f"ytsearch1:{query}",
                "--get-url",
                "--no-playlist",
                "--format", "bestvideo+bestaudio/best",
                "--youtube-skip-dash-manifest",
            ],
            capture_output=True, text=True, timeout=15,
        )
        # yt-dlp --get-url 는 여러 줄 출력 가능 — 첫 줄이 영상 페이지 URL이 아님
        # watch URL을 따로 구함
        result2 = subprocess.run(
            [
                "yt-dlp",
                f"ytsearch1:{query}",
                "--get-id",
                "--no-playlist",
            ],
            capture_output=True, text=True, timeout=15,
        )
        vid_id = result2.stdout.strip().splitlines()[0] if result2.stdout.strip() else None
        if vid_id:
            return f"https://www.youtube.com/watch?v={vid_id}"
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return None


def execute(params: dict) -> str:
    query = params.get("query", "").strip()
    if not query:
        return "검색어를 입력해주세요."

    video_url = _get_video_url(query)

    if video_url:
        # 브라우저로 직접 watch URL 열기 (로그인 쿠키 사용)
        try:
            subprocess.run(["open", "-a", "Google Chrome", video_url], check=True)
            return f"Chrome에서 YouTube '{query}' 재생을 시작했습니다."
        except Exception:
            subprocess.run(["open", video_url])
            return f"YouTube에서 '{query}' 재생을 시작했습니다."
    else:
        # yt-dlp 없으면 검색 페이지라도 열기
        encoded = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded}"
        try:
            subprocess.run(["open", "-a", "Google Chrome", search_url], check=True)
        except Exception:
            subprocess.run(["open", search_url])
        return f"yt-dlp가 없어 검색 페이지를 열었습니다. 'pip install yt-dlp' 로 설치하면 바로 재생됩니다."
