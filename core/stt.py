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

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK = 1024
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 1.5
MAX_RECORD_DURATION = 15.0

# webrtcvad는 10/20/30ms 프레임만 지원, 16kHz 기준 20ms = 320 샘플
VAD_FRAME_MS = 20
VAD_FRAME_SIZE = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)  # 320 샘플 = 640 bytes


def _is_silent(data: bytes, threshold: int = SILENCE_THRESHOLD) -> bool:
    samples = struct.unpack(f"{len(data)//2}h", data)
    rms = (sum(s**2 for s in samples) / len(samples)) ** 0.5
    return rms < threshold


def _record_with_vad(
    pa: pyaudio.PyAudio,
    sample_rate: int = SAMPLE_RATE,
    silence_duration: float = SILENCE_DURATION,
    max_duration: float = MAX_RECORD_DURATION,
) -> Optional[bytes]:
    """webrtcvad 기반 음성 녹음 — ML로 발화 끝 정확히 감지"""
    vad = webrtcvad.Vad(2)  # aggressiveness 0~3, 2=균형

    stream = pa.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=sample_rate,
        input=True,
        frames_per_buffer=VAD_FRAME_SIZE,
    )

    frames = []
    silence_frames = 0
    speaking_started = False
    start_time = time.time()
    silence_frames_needed = int(silence_duration * 1000 / VAD_FRAME_MS)

    try:
        while True:
            data = stream.read(VAD_FRAME_SIZE, exception_on_overflow=False)
            frames.append(data)

            if time.time() - start_time > max_duration:
                break

            try:
                is_speech = vad.is_speech(data, sample_rate)
            except Exception:
                is_speech = not _is_silent(data)

            if is_speech:
                speaking_started = True
                silence_frames = 0
            elif speaking_started:
                silence_frames += 1
                if silence_frames >= silence_frames_needed:
                    break
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


def _record_with_energy(
    pa: pyaudio.PyAudio,
    sample_rate: int = SAMPLE_RATE,
    silence_duration: float = SILENCE_DURATION,
    max_duration: float = MAX_RECORD_DURATION,
) -> Optional[bytes]:
    """에너지 기반 음성 녹음 (webrtcvad 폴백)"""
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

            if time.time() - start_time > max_duration:
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


def record_audio(
    pa: pyaudio.PyAudio,
    sample_rate: int = SAMPLE_RATE,
    silence_duration: float = SILENCE_DURATION,
    max_duration: float = MAX_RECORD_DURATION,
) -> Optional[bytes]:
    """마이크에서 음성 녹음 (webrtcvad 우선, 폴백은 에너지 기반)"""
    if VAD_AVAILABLE:
        return _record_with_vad(pa, sample_rate, silence_duration, max_duration)
    return _record_with_energy(pa, sample_rate, silence_duration, max_duration)


_whisper_model = None
_whisper_model_size = None


def _load_whisper(model_size: str = "base") -> Optional[object]:
    global _whisper_model, _whisper_model_size
    if (_whisper_model is None or _whisper_model_size != model_size) and WHISPER_AVAILABLE:
        print(f"⏳ Whisper '{model_size}' 모델 로딩 중...")
        _whisper_model = _WhisperModel(model_size, device="cpu", compute_type="int8")
        _whisper_model_size = model_size
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
