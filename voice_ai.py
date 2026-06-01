import os
import sys
import struct
import pvporcupine
from pyaudio import PyAudio, paInt16

# 1. Picovoice Access Key
ACCESS_KEY = "awDDXrB75GvtoZNrckfmQHElucCoDLyg/Tp89lapnge0LrLJp0Vg1A=="

# 2. 커스텀 .ppn 파일 경로
KEYWORD_PATH = "/Users/jakallee/Downloads/머스탱_ko_mac_v4_0_0/머스탱_ko_mac_v4_0_0.ppn"

# 3. 한국어 모델(.pv) 파일 경로
KO_MODEL_PATH = "/Users/jakallee/Downloads/머스탱_ko_mac_v4_0_0/porcupine_params_ko.pv"

porcupine = None
pa = None
audio_stream = None

try:
    # Porcupine 엔진 초기화
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[KEYWORD_PATH],
        model_path=KO_MODEL_PATH
    )

    # 오디오 입력(마이크) 설정
    pa = PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print("🎤 준비 완료! '머스탱'이라고 불러보세요... (종료: Ctrl+C)")

    while True:
        # 마이크로부터 오디오 데이터 읽기
        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        
        # 데이터 타입 변환 (바이트 -> 16비트 정수 배열)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        # 웨이크 워드 감지 수행
        keyword_index = porcupine.process(pcm)
        
        # 감지 성공 시
        if keyword_index >= 0:
            print("\n🔥 [감지] 머스탱이 깨어났습니다!")
            
            # 🔊 Mac 내장 음성으로 답변하기 (추가된 로직)
            # os.system을 이용해 macOS의 say 명령어를 실행합니다.
            response_text = "부르셨어요? 무엇을 도와드릴까요?"
            os.system(f"say '{response_text}'")
            
            print("🎤 다시 대기 중...")

except KeyboardInterrupt:
    print("\n👋 테스트를 종료합니다.")

finally:
    # 자원 해제
    if audio_stream is not None:
        audio_stream.close()
    if pa is not None:
        pa.terminate()
    if porcupine is not None:
        porcupine.delete()