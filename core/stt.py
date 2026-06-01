"""
STT (Speech-to-Text) 모듈
웨이크워드 감지 후 음성을 텍스트로 변환
"""
import io
import struct
import tempfile
import threading
import time
import wave
from typing import Optional

import pyaudio

import os
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

try:
    from faster_whisper import WhisperModel as _WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK = 1024
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 2.0
MAX_RECORD_DURATION = 15.0


def _is_silent(data: bytes, threshold: int = SILENCE_THRESHOLD) -> bool:
    samples = struct.unpack(f"{len(data)//2}h", data)
    rms = (sum(s**2 for s in samples) / len(samples)) ** 0.5
    return rms < threshold


def record_audio(
    pa: pyaudio.PyAudio,
    sample_rate: int = SAMPLE_RATE,
    silence_duration: float = SILENCE_DURATION,
    max_duration: float = MAX_RECORD_DURATION,
) -> Optional[bytes]:
    """마이크에서 음성 녹음 (무음 감지로 자동 종료)"""
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=sample_rate,
        input=True,
        frames_per_buffer=CHUNK,
    )

    frames = []
    silent_chunks = 0
    speaking_started = False
    start_time = time.time()
    silence_chunks_needed = int(silence_duration * sample_rate / CHUNK)

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            elapsed = time.time() - start_time

            if elapsed > max_duration:
                break

            if _is_silent(data):
                if speaking_started:
                    silent_chunks += 1
                    if silent_chunks >= silence_chunks_needed:
                        break
            else:
                speaking_started = True
                silent_chunks = 0
    finally:
        stream.stop_stream()
        stream.close()

    if not speaking_started:
        return None

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))
    return buf.getvalue()


_whisper_model = None


def _load_whisper(model_size: str = "small") -> Optional[object]:
    global _whisper_model
    if _whisper_model is None and WHISPER_AVAILABLE:
        print(f"⏳ Whisper '{model_size}' 모델 로딩 중...")
        _whisper_model = _WhisperModel(model_size, device="cpu", compute_type="int8")
        print("✅ Whisper 모델 준비 완료")
    return _whisper_model


def transcribe_whisper(audio_bytes: bytes, language: str = "ko") -> str:
    model = _load_whisper()
    if model is None:
        return ""

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        segments, _ = model.transcribe(
            tmp_path,
            language=language,
            beam_size=5,
            vad_filter=True,
        )
        return "".join(seg.text for seg in segments).strip()
    finally:
        import os
        os.unlink(tmp_path)


def transcribe_google(audio_bytes: bytes, language: str = "ko-KR") -> str:
    if not SR_AVAILABLE:
        return ""

    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)

    try:
        return recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"⚠️ Google STT 오류: {e}")
        return ""


def transcribe(audio_bytes: bytes, use_whisper: bool = True) -> str:
    # Google STT 우선 (한국어 정확도 높음) → Whisper 폴백
    if SR_AVAILABLE:
        result = transcribe_google(audio_bytes)
        if result:
            return result
    if WHISPER_AVAILABLE:
        return transcribe_whisper(audio_bytes)
    return ""
