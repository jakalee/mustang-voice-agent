# Rokid AIUI 예제: 재규어봇 (Hermes Agent 클라이언트)

Rokid 안경에서 음성으로 말하면 Hermes Agent(OpenAI 호환 `/v1/chat/completions`)에 전달하고, 응답을 안경 화면에 스트리밍으로 표시하는 AIUI 앱 소스입니다.
전체 설정 방법(Hermes 서버, 역방향 프록시, AIUI Studio, 안경 반영)은 [docs/rokid/README.md](../../docs/rokid/README.md)를 보세요.

## 구성

```
jaguar-bot/
├── app.json                # 앱 메타/권한 (INTERNET, RECORD_AUDIO)
├── app.js                  # 앱 엔트리
├── AGENTS.md               # 에이전트 매니페스트
└── pages/index/index.ink   # 메인 화면 (음성 인식, API 호출, 스트리밍 표시, TTS)
```

## 사용 전 반드시 수정

`jaguar-bot/pages/index/index.ink` 상단 `CONFIG`:

| 항목 | 설명 |
|---|---|
| `BASE_URL` | 본인의 HTTPS 주소 (예: `https://xxxx.synology.me`) |
| `API_KEY` | Hermes `.env`의 `API_SERVER_KEY` |

`AGENTS.md`의 Network 도메인과 Author도 본인 값으로 바꾸세요.

## 주요 설정값 (`CONFIG`)

| 키 | 기본값 | 설명 |
|---|---|---|
| `MODEL` | `''` | 비우면 `/v1/models`의 첫 모델 사용 |
| `ASR_LANG` | `ko-KR` | 미지원이면 런타임 기본 언어로 자동 재시도 |
| `AUTO_LISTEN` | `true` | 실행 직후 바로 듣기 시도 |
| `TTS` / `TTS_VOLUME` | `true` / `10` | 응답 음성 출력 (Speaker 권한 필요) |
| `HISTORY_LIMIT` | `10` | 대화 맥락으로 보낼 최근 메시지 수 |

## 조작

- 템플 탭: 듣기 시작/종료
- 처리 중 뒤로가기: 요청 취소
- 연결 실패 시 화면에 진단 결과(`/health`, `/v1/models`)가 표시됩니다.

## ⚠️ 보안

- `API_KEY`는 앱 코드와 `.aix` 패키지에 **평문으로 포함**됩니다. 개인 기기용으로만 쓰고, 키를 채운 소스/`.aix`를 GitHub 등에 올리지 마세요.
- 이 저장소의 소스는 키와 도메인을 플레이스홀더로 바꿔 둔 상태입니다. 로컬에서 값을 채운 뒤 `git add` 하기 전에 `git diff`로 확인하세요.
