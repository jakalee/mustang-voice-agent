"""
웨이크워드 감지 모듈 — VAD + Whisper 기반 (완전 무료/오픈소스)
"머스탱"이라는 단어를 Whisper tiny 모델로 감지
⌥Space 전역 단축키로도 활성화 가능
"""
import struct
import threading
import time

import pyaudio

SAMPLE_RATE = 16000
CHUNK = 512
ENERGY_THRESHOLD = 400      # 이 이상이면 말소리로 판단
MAX_RECORD_SECS = 3.0       # 웨이크워드 감지용 최대 녹음 길이
WAKEWORDS = [
    "머스탱", "무스탕", "머스탕", "mustang",
    "머스", "뭐스탱", "뭐스탕", "뭐 스탱", "뭐 스탕",
    "스탱", "스탬", "스탄", "스탐",
    "뭐스", "무스", "멋있", "멋진",   # tiny 모델 오인식 패턴
    "뭐 스", "머 스",
]  # 인식 후보 (tiny 모델 오인식 포함)

# 전역 단축키 트리거 이벤트
hotkey_event = threading.Event()

_whisper_model = None


def _load_whisper():
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            print("⏳ 웨이크워드용 Whisper tiny 로딩 중...")
            _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            print("✅ 웨이크워드 감지 준비 완료 (Whisper tiny)")
        except Exception as e:
            print(f"⚠️  Whisper 로드 실패: {e}")
    return _whisper_model


def _energy(data: bytes) -> float:
    samples = struct.unpack(f"{len(data)//2}h", data)
    return (sum(s * s for s in samples) / len(samples)) ** 0.5


try:
    import webrtcvad as _webrtcvad
    _VAD = _webrtcvad.Vad(2)
    _VAD_AVAILABLE = True
except ImportError:
    _VAD = None
    _VAD_AVAILABLE = False

VAD_FRAME_MS = 20
VAD_FRAME_SIZE = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)  # 320 샘플


def _record_until_silence(stream) -> bytes:
    """소리가 끝날 때까지 최대 MAX_RECORD_SECS 녹음 (webrtcvad 우선)"""
    frames = []
    silence_count = 0
    silence_limit = int(0.8 * 1000 / VAD_FRAME_MS)  # 0.8초치 프레임 수
    deadline = time.time() + MAX_RECORD_SECS

    if _VAD_AVAILABLE:
        read_size = VAD_FRAME_SIZE
    else:
        read_size = CHUNK

    while time.time() < deadline:
        data = stream.read(read_size, exception_on_overflow=False)
        frames.append(data)

        if _VAD_AVAILABLE:
            try:
                is_speech = _VAD.is_speech(data, SAMPLE_RATE)
            except Exception:
                is_speech = _energy(data) >= ENERGY_THRESHOLD
        else:
            is_speech = _energy(data) >= ENERGY_THRESHOLD

        if not is_speech:
            silence_count += 1
            if silence_count >= silence_limit:
                break
        else:
            silence_count = 0

    return b"".join(frames)


def _is_wakeword(text: str) -> bool:
    """Whisper 인식 결과가 웨이크워드인지 판단"""
    t = text.strip().lower().replace(" ", "")
    # 정확한 매칭
    for w in WAKEWORDS:
        if w.replace(" ", "") in t:
            return True
    # 짧은 발화(3글자 이하)이고 스 or 탱 포함 시
    if len(t) <= 5 and ("스탱" in t or "스탕" in t or "스탬" in t or "스탄" in t):
        return True
    return False


def _transcribe_wakeword(audio_bytes: bytes) -> str:
    import io, wave, tempfile, os
    model = _load_whisper()
    if model is None:
        return ""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    try:
        with wave.open(tmp, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_bytes)
        segments, _ = model.transcribe(
            tmp,
            language="ko",
            beam_size=1,
            vad_filter=False,
            initial_prompt="머스탱",  # 웨이크워드 후보 힌트
        )
        return "".join(s.text for s in segments).strip()
    except Exception:
        return ""
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def _start_hotkey_listener():
    """⌥Space 전역 단축키 리스너 — 백그라운드 스레드"""
    try:
        from pynput import keyboard

        def on_activate():
            print("\n⌨️  [단축키] ⌥Space 감지 → 머스탱 활성화")
            hotkey_event.set()

        hotkey = keyboard.GlobalHotKeys({"<alt>+<space>": on_activate})
        hotkey.start()
        print("✅ 전역 단축키 ⌥Space 등록 완료")
    except Exception as e:
        print(f"⚠️  전역 단축키 등록 실패: {e}")


def listen_for_wakeword(pa: pyaudio.PyAudio, stop_flag=None) -> bool:
    """
    "머스탱" 발화 또는 ⌥Space 감지 시 True 반환.
    stop_flag: threading.Event — set되면 False 반환.
    """
    _load_whisper()
    hotkey_event.clear()

    read_size = VAD_FRAME_SIZE if _VAD_AVAILABLE else CHUNK
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=read_size,
    )
    try:
        while True:
            if stop_flag and stop_flag.is_set():
                return False

            if hotkey_event.is_set():
                hotkey_event.clear()
                return True

            data = stream.read(read_size, exception_on_overflow=False)

            # 소리 감지 — webrtcvad 우선, 폴백은 에너지
            if _VAD_AVAILABLE:
                try:
                    detected = _VAD.is_speech(data, SAMPLE_RATE)
                except Exception:
                    detected = _energy(data) >= ENERGY_THRESHOLD
            else:
                detected = _energy(data) >= ENERGY_THRESHOLD

            if detected:
                audio = data + _record_until_silence(stream)
                text = _transcribe_wakeword(audio)
                if text:
                    print(f"  [웨이크워드 후보] {text}")
                if _is_wakeword(text):
                    return True

    finally:
        stream.stop_stream()
        stream.close()
