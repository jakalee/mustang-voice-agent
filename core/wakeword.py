"""
웨이크워드 감지 모듈 (Picovoice 대체 - 완전 무료)
faster-whisper tiny 모델로 짧은 오디오 청크를 계속 분석해
"머스탱" 발화를 감지합니다.
"""
import io
import struct
import tempfile
import time
import wave
from typing import Optional

import pyaudio

# ─── 설정 ─────────────────────────────────────────────────────
SAMPLE_RATE = 16000
CHUNK       = 1024
CHANNELS    = 1

# 웨이크워드 감지용 청크 길이 (초) — 짧을수록 반응 빠름, 오탐 증가
LISTEN_SECONDS = 2.0
LISTEN_FRAMES  = int(SAMPLE_RATE * LISTEN_SECONDS / CHUNK)

# 인식할 웨이크워드 변형 목록 (Whisper 오인식 대비)
WAKEWORDS = [
    "머스탱", "mustang", "머스 탱", "머스땡", "머스팅",
    "musttang", "must tang", "Mustang",
    # tiny 모델 오인식 패턴
    "스탱", "스탬", "머스탬", "머 스탱", "뭐스탱",
    "musstan", "mustan", "머쓰탱", "머스땡",
]

_tiny_model = None


def _load_tiny():
    global _tiny_model
    if _tiny_model is None:
        from faster_whisper import WhisperModel
        import os
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
        print("⏳ 웨이크워드 감지용 Whisper tiny 로딩 중...")
        _tiny_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("✅ 웨이크워드 감지 준비 완료")
    return _tiny_model


def _record_chunk(pa: pyaudio.PyAudio) -> bytes:
    """고정 길이 오디오 청크 녹음"""
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )
    frames = []
    try:
        for _ in range(LISTEN_FRAMES):
            data = stream.read(CHUNK, exception_on_overflow=False)
            if not data:
                raise IOError("오디오 스트림에서 빈 데이터 수신 — 장치 재초기화 필요")
            frames.append(data)
    finally:
        stream.stop_stream()
        stream.close()

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(frames))
    return buf.getvalue()


def _has_wakeword(text: str) -> bool:
    t = text.strip().lower()
    return any(w.lower() in t for w in WAKEWORDS)


def _is_mostly_silent(audio_bytes: bytes, threshold: int = 600) -> bool:
    """무음 청크는 Whisper에 보내지 않아 CPU 절약"""
    buf = io.BytesIO(audio_bytes)
    with wave.open(buf, "rb") as wf:
        raw = wf.readframes(wf.getnframes())
    samples = struct.unpack(f"{len(raw)//2}h", raw)
    rms = (sum(s**2 for s in samples) / max(len(samples), 1)) ** 0.5
    return rms < threshold


def listen_for_wakeword(pa: pyaudio.PyAudio, stop_flag=None) -> bool:
    """
    웨이크워드("머스탱")가 감지될 때까지 반복 청취.
    stop_flag: threading.Event — set되면 루프 종료 후 False 반환
    감지 성공 시 True 반환.
    오디오 장치 오류 시 pa를 재초기화하고 재시도.
    """
    import os
    model = _load_tiny()
    _consecutive_errors = 0

    while True:
        if stop_flag and stop_flag.is_set():
            return False

        try:
            audio = _record_chunk(pa)
            _consecutive_errors = 0
        except Exception as e:
            _consecutive_errors += 1
            # 연속 오류 3회 이상이면 함수 종료 → 호출자(mustang.py)가 pa 재초기화
            if _consecutive_errors >= 3:
                print(f"\n  [wakeword] 오디오 장치 오류 반복 — 재초기화 요청 ({e})")
                return False  # mustang.py 루프에서 _init_audio() 후 재진입
                _consecutive_errors = 0
            else:
                time.sleep(0.5)
            continue

        # 무음 → 건너뜀
        if _is_mostly_silent(audio):
            continue

        tmp = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio)
                tmp = f.name

            segments, _ = model.transcribe(
                tmp,
                language="ko",
                beam_size=1,        # 빠른 추론
                best_of=1,
                temperature=0.0,
                vad_filter=True,
                initial_prompt="머스탱",   # 힌트: 이 단어를 잘 인식하도록 유도
            )
            text = "".join(s.text for s in segments)

            if text:
                print(f"  [wakeword 후보] {text.strip()}", end="\r")

            if _has_wakeword(text):
                print()
                return True

        except Exception as e:
            print(f"\n  [wakeword 오류] {e}")
        finally:
            # 예외 발생 여부와 무관하게 임시 파일 반드시 삭제
            if tmp:
                try:
                    os.unlink(tmp)
                except Exception:
                    pass
