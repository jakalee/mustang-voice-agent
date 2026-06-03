"""
Mustang AI 데모 GIF 생성기
Playwright로 위젯을 자동 상태 전환하며 스크린샷 찍어 GIF로 합성
"""
import time
import asyncio
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
import io

OUT_DIR  = Path(__file__).parent
GIF_PATH = OUT_DIR / "demo.gif"
W, H = 480, 480   # 캡처 크기

# (상태, JS로 주입할 state, subtext, amplitude, 머무는 시간(초))
SEQUENCE = [
    # 대기 상태
    ("idle",      "",                           0.0,  2.0),
    ("idle",      "",                           0.0,  1.5),

    # 웨이크워드 감지 → 듣는 중
    ("listening", "",                           0.0,  2.0),
    ("listening", "",                           0.1,  1.5),

    # 생각 중 (사용자 발화 표시)
    ("thinking",  "유튜브 아이유 Celebrity 틀어줘", 0.0, 1.5),
    ("thinking",  "유튜브 아이유 Celebrity 틀어줘", 0.0, 1.5),
    ("thinking",  "유튜브 아이유 Celebrity 틀어줘", 0.0, 1.5),

    # 말하는 중 (AI 응답 + 진폭 박동)
    ("speaking",  "YouTube에서 아이유 Celebrity 재생을 시작했습니다.", 0.3,  0.8),
    ("speaking",  "YouTube에서 아이유 Celebrity 재생을 시작했습니다.", 0.7,  0.8),
    ("speaking",  "YouTube에서 아이유 Celebrity 재생을 시작했습니다.", 0.9,  0.8),
    ("speaking",  "YouTube에서 아이유 Celebrity 재생을 시작했습니다.", 0.6,  0.8),
    ("speaking",  "YouTube에서 아이유 Celebrity 재생을 시작했습니다.", 0.8,  0.8),
    ("speaking",  "YouTube에서 아이유 Celebrity 재생을 시작했습니다.", 0.4,  0.8),
    ("speaking",  "YouTube에서 아이유 Celebrity 재생을 시작했습니다.", 0.2,  0.8),

    # 대기로 복귀
    ("idle",      "",                           0.0,  2.0),
    ("idle",      "",                           0.0,  1.5),
]

WIDGET_HTML = Path(__file__).parent.parent / "widget" / "index.html"

STATUS_TEXT = {
    "idle":      "대기 중",
    "listening": "듣는 중",
    "thinking":  "생각 중",
    "speaking":  "말하는 중",
}

def inject_state(page, state, subtext, amplitude):
    """JavaScript로 위젯 상태 직접 주입"""
    page.evaluate(f"""
        agentState = '{state}';
        targetAmplitude = {amplitude};
        document.getElementById('status').textContent = '{STATUS_TEXT[state]}';
        const sub = document.getElementById('subtext');
        if (sub) {{
            if ('{state}' === 'idle' || '{state}' === 'listening') {{
                sub.textContent = '';
            }} else {{
                sub.textContent = `{subtext}`;
            }}
        }}
    """)


def make_gif():
    frames = []
    durations = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": W, "height": H})

        # 위젯 로드 (WebSocket 연결 실패는 무시)
        page.goto(f"file://{WIDGET_HTML}", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)   # p5.js 초기화 대기

        FPS = 30
        FRAME_MS = 1000 // FPS

        for (state, subtext, amplitude, duration) in SEQUENCE:
            inject_state(page, state, subtext, amplitude)
            total_frames = max(1, int(duration * FPS))

            for f in range(total_frames):
                # amplitude를 시간에 따라 약간 변동시켜 자연스럽게
                if state == "speaking":
                    import math
                    t = f / FPS
                    amp = amplitude * (0.6 + 0.4 * abs(math.sin(t * 6)))
                    page.evaluate(f"targetAmplitude = {amp:.3f};")

                page.wait_for_timeout(FRAME_MS)
                png = page.screenshot()
                img = Image.open(io.BytesIO(png)).convert("RGBA")
                # 검정 배경 합성 (GIF는 투명 지원이 제한적)
                bg = Image.new("RGBA", img.size, (15, 15, 20, 255))
                bg.paste(img, mask=img.split()[3])
                frames.append(bg.convert("RGB"))
                durations.append(FRAME_MS)

        browser.close()

    print(f"  총 {len(frames)}프레임 캡처 완료")

    # GIF 저장
    frames[0].save(
        GIF_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    size_mb = GIF_PATH.stat().st_size / 1_000_000
    print(f"  저장 완료: {GIF_PATH} ({size_mb:.1f} MB)")

    # 10MB 이상이면 최적화
    if size_mb > 8:
        print("  최적화 중...")
        optimized = []
        for i, fr in enumerate(frames):
            if i % 2 == 0:  # 2프레임마다 하나 (절반 용량)
                optimized.append(fr)
        optimized[0].save(
            GIF_PATH,
            save_all=True,
            append_images=optimized[1:],
            duration=[d*2 for d in durations[::2]],
            loop=0,
            optimize=True,
        )
        size_mb = GIF_PATH.stat().st_size / 1_000_000
        print(f"  최적화 완료: {size_mb:.1f} MB")


if __name__ == "__main__":
    print("🎬 Mustang AI 데모 GIF 생성 중...")
    make_gif()
    print("✅ 완료!")
