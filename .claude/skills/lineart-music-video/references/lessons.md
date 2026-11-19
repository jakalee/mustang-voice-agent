# 실전에서 막혔던 것들

## 네트워크 (클라우드 세션)
- Whisper/Demucs 모델 다운로드에 필요한 호스트: `huggingface.co`, `us.aws.cdn.hf.co`, `cas-server.xethub.hf.co`, `cas-bridge.xethub.hf.co`, `cdn-lfs.hf.co`, `dl.fbaipublicfiles.com`. 허깅페이스는 실제 파일을 CDN으로 리다이렉트하므로 `huggingface.co`만 열면 403이 난다.
- `HF_HUB_DISABLE_XET=1`이면 xet 서버 없이 받는다 (`lyrics_align.py`가 기본으로 켠다).
- 캡처 시 Google Fonts는 `capture.mjs`가 curl로 받아 넘겨준다. 브라우저 쪽 TLS 검증을 끄지 않기 위해서다.

## 라이브러리 충돌
- `faster-whisper`에 파일 경로를 주면 PyAV 버전에 따라 `open() got an unexpected keyword argument 'metadata_errors'`가 난다 → librosa로 16kHz numpy 배열을 읽어 넘긴다.
- Playwright를 ESM에서 `import`하면 전역 설치본을 못 찾는다 → `createRequire`로 절대 경로를 require.

## 가사 타이밍
- 영상에 들어 있던 자막(mov_text)은 롤링 3줄 자막이라, 새 줄이 뜨는 시각이 실제 노래와 4~12초씩 어긋났다. 그걸로 맞춘 첫 버전은 1:46부터 틀렸다 (후렴 한 줄이 누락돼 뒤가 전부 밀림).
- Whisper는 다음 줄 시작을 앞 줄 끝에 붙인다 → 직전이 조용하다가 커지는 지점으로 보정.
- 한 구간에 두 줄이 붙어 나오면 단어 타임스탬프로 나눈다.
- 길게 끄는 음(예: "난~")은 단어 길이가 엉터리다. 보컬 RMS를 0.25초 단위로 찍어 무음 구간 사이를 본다.

## 그림
- 닫힌 다각형을 부드러운 곡선(`trace`)으로 그리면 문·컵·책이 타원이 된다 → `sharp: true`.
- 나뭇가지 위 눈을 가지 굵기에 비례해 그리면 흰 막대처럼 보인다 → 굵기 상한 7px.
- 서리 결정은 길면 화면을 긁은 자국처럼 보인다 → 짧게(60~150px), 개수를 늘리고, 불투명도 0.6 이하.
- 김서림은 선으로 표현이 안 된다 → 창밖을 오프스크린에 그리고 blur 사본 + 반투명 막을 얹은 뒤, 글씨 마스크로 `destination-out`.
- 세로(9:16)로 바꿀 때는 자르지 말고 카메라 줌·장면 구도를 다시 잡는다 (골목은 줌 1.6, 창은 세로로 긴 비율, 글씨는 두 줄).

## 성능
- 1080×1920, 30fps, 166초 ≈ 5000프레임: 캔버스 `toDataURL('image/jpeg')` → ffmpeg `image2pipe` 로 3~6분.
- 결과 mp4가 100MB를 넘으면 `-crf 23 -tune animation`으로 다시 인코딩 (대략 절반).
