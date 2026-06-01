"""
TTS (Text-to-Speech) 모듈
macOS say 명령어 + 한국어 음성 지원
"""
import os
import subprocess
import threading
import time

PREFERRED_VOICES = [
    "Yuna (Premium)",
    "Yuna",
    "Eddy (한국어(한국))",
    "Sandy (한국어(한국))",
]

POST_SPEAK_DELAY = 0.4

_TTS_TMP = "/tmp/mustang_tts.aiff"


def _get_available_voice() -> str:
    try:
        result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
        voices_text = result.stdout + result.stderr
        for preferred in PREFERRED_VOICES:
            if preferred in voices_text:
                return preferred
        for line in voices_text.splitlines():
            if "ko_KR" in line or "ko_" in line:
                return line.split()[0]
    except Exception:
        pass
    return "Alex"


_voice = None


def get_voice() -> str:
    global _voice
    if _voice is None:
        _voice = _get_available_voice()
    return _voice


def speak(text: str, blocking: bool = True, rate: int = 180):
    """say -o AIFF 파일로 변환 후 afplay로 완전 재생 (끝 음절 잘림 없음)"""
    if not text:
        return
    voice = get_voice()

    def _run():
        # 1단계: 텍스트를 AIFF 파일로 저장 (stdin 파이프)
        encode_proc = subprocess.Popen(
            ["say", "-v", voice, "-r", str(rate), "-o", _TTS_TMP],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        encode_proc.communicate(input=text.encode("utf-8"))
        encode_proc.wait()

        # 2단계: afplay로 완전 재생 (오디오 버퍼 보장)
        subprocess.run(
            ["afplay", _TTS_TMP],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def speak_async(text: str, rate: int = 180):
    speak(text, blocking=False, rate=rate)


def stop_speaking():
    """현재 재생 중인 TTS 즉시 중지"""
    subprocess.run(["killall", "afplay", "say"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def list_korean_voices():
    result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
    voices = []
    for line in (result.stdout + result.stderr).splitlines():
        if "ko_" in line or "Korean" in line:
            voices.append(line.strip())
    return voices
