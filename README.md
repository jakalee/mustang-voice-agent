# 🐎 Mustang AI — 음성명령 AI 에이전트

macOS / Windows에서 동작하는 로컬 AI 음성 명령 에이전트입니다.  
**"머스탱"** 이라고 부르면 깨어나고, 음성 명령을 처리합니다.

> 웨이크워드 감지는 **faster-whisper** 기반으로 구현되어 있어 별도 API 키나 유료 서비스 없이 완전 무료로 동작합니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 🎤 웨이크워드 감지 | "머스탱" 호출 시 자동 활성화 (faster-whisper, 완전 무료) |
| 🗣️ 음성 인식 (STT) | Whisper 기반 한국어 음성 → 텍스트 |
| 🔊 음성 합성 (TTS) | macOS 기본 TTS / Windows SAPI |
| 🤖 AI 처리 | Claude Code CLI 기반 자연어 명령 처리 |
| 🖥️ 바탕화면 위젯 | p5.js 파형 원이 AI 상태에 따라 실시간 반응 (GeekTool) |
| 📅 일정 관리 | Google 캘린더 조회/등록 |
| 📧 이메일 | Gmail 확인 및 발송 |
| 🌐 브라우저 | 웹 자동화 (Playwright) |
| 📁 Google Drive | 파일 검색/관리 |
| 📱 텔레그램 | 봇을 통한 원격 명령 |
| ⏰ 예약 실행 | 특정 시간에 명령 자동 실행 |
| 🖱️ 화면 제어 | 스크린샷, 앱 실행 |

---

## 설치 방법

> **플랫폼을 선택하세요**

- [Mac ARM (M1/M2/M3/M4)](#-mac-arm-m1m2m3m4)
- [Mac Intel](#-mac-intel)
- [Windows](#-windows)

---

## 🍎 Mac ARM (M1/M2/M3/M4)

### 1단계 — ARM Homebrew 설치

```bash
arch -arm64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

### 2단계 — ARM Python 설치 (Miniforge)

```bash
brew install --cask miniforge
conda create -n mustang python=3.11 -y
conda activate mustang
```

> **주의:** 기존에 Anaconda가 Intel로 설치되어 있으면 반드시 Miniforge를 별도로 설치해야 합니다.

### 3단계 — PortAudio 설치

```bash
/opt/homebrew/bin/brew install portaudio
```

### 4단계 — 프로젝트 클론 및 패키지 설치

```bash
git clone https://github.com/jakalee/mustang-voice-agent.git
cd mustang-voice-agent

LDFLAGS="-L/opt/homebrew/lib" CPPFLAGS="-I/opt/homebrew/include" \
  pip install pyaudio --no-binary pyaudio --no-cache-dir

pip install -r requirements.txt
```

### 5단계 — 설정 파일 작성

```bash
cp config/.env.example config/.env
```

`config/.env` 파일을 열어서 필요한 값만 입력합니다 (Gmail, 텔레그램은 선택):

```env
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# 텔레그램 봇 (선택)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=123456789
```

### 6단계 — 실행

```bash
conda activate mustang

# 음성 모드 — "머스탱"이라고 부르면 깨어납니다
python mustang.py

# 텍스트 모드
python mustang.py --text

# 텔레그램 봇 모드
python mustang.py --telegram
```

---

## 💻 Mac Intel

### 1단계 — Homebrew 및 Python 설치

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.11 portaudio
```

### 2단계 — 프로젝트 클론 및 가상환경

```bash
git clone https://github.com/jakalee/mustang-voice-agent.git
cd mustang-voice-agent

python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 3단계 — 패키지 설치

```bash
LDFLAGS="-L/usr/local/lib" CPPFLAGS="-I/usr/local/include" \
  pip install pyaudio --no-binary pyaudio --no-cache-dir

pip install -r requirements.txt
```

### 4단계 — 설정 및 실행

```bash
cp config/.env.example config/.env
# config/.env 에 Gmail 등 필요한 값 입력 (선택)

source venv/bin/activate
python mustang.py
```

---

## 🪟 Windows

### 1단계 — Python 설치

[python.org](https://www.python.org/downloads/) 에서 **Python 3.11** 다운로드.  
설치 시 **"Add Python to PATH"** 체크 필수.

### 2단계 — 프로젝트 클론

```powershell
git clone https://github.com/jakalee/mustang-voice-agent.git
cd mustang-voice-agent

python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install pyaudio
pip install -r requirements.txt
```

> `pyobjc-framework-Quartz`는 macOS 전용이라 Windows에서 오류가 나도 무시하세요.

### 3단계 — 설정 및 실행

```powershell
copy config\.env.example config\.env
# config\.env 에 필요한 값 입력

venv\Scripts\activate
python mustang.py
```

---

## 🖥️ 바탕화면 위젯 (macOS + GeekTool)

AI가 말하는 동안 p5.js 파형 원이 실시간으로 반응하는 위젯을 바탕화면에 배치할 수 있습니다.

![위젯 상태](https://raw.githubusercontent.com/jakalee/mustang-voice-agent/main/docs/widget-preview.png)

### 상태별 시각 효과

| 상태 | 색상 | 동작 |
|------|------|------|
| 대기 중 | 🔵 파란색 | 느리고 잔잔한 파형 |
| 듣는 중 | 🟢 초록색 | 중간 속도, 팽창 |
| 생각 중 | 🟣 보라색 | 빠르고 복잡한 파형 |
| 말하는 중 | 🟡 황금색 | 진폭에 따라 박동 |

### 설치 방법

**1. 위젯 파일 준비**

```bash
# 위젯 폴더 생성 및 p5.js 다운로드
mkdir -p ~/Desktop/mustang-widget
curl -o ~/Desktop/mustang-widget/p5.min.js \
  https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js
```

위젯 HTML은 이 저장소의 `widget/index.html`에 포함되어 있습니다.  
`mustang.py` 실행 시 `http://localhost:8766/widget/index.html` 로 자동 서빙됩니다.  
또는 `file:///경로/mustang-voice-agent/widget/index.html` 로 직접 열 수 있습니다.

**2. websockets 설치**

```bash
pip install websockets
```

**3. GeekTool 설정**

1. [GeekTool](https://www.tynsoe.org/geektool/) 설치
2. GeekTool 실행 → **Web Geeklet** 드래그
3. 아래 값 입력:

| 항목 | 값 |
|------|----|
| URL | `file:///Users/사용자명/mustang-voice-agent/widget/index.html` |
| Refresh | `0` (새로고침 없음) |
| Width / Height | `400 / 400` |

4. 바탕화면 원하는 위치로 이동

**4. mustang.py 실행**

```bash
python mustang.py
```

실행 시 `widget_server.py`가 자동으로 시작되며 위젯과 WebSocket으로 연결됩니다.

### 동작 원리

```
"머스탱" 발화
    ↓
mustang.py (faster-whisper 감지)
    ↓
WidgetBridge → WebSocket (ws://localhost:8765)
    ↓
index.html (p5.js) → 파형 원 실시간 반응
    ↓
GeekTool → 바탕화면에 투명 위젯으로 표시
```

---

## 웨이크워드 감지 방식

별도 API 키 없이 **faster-whisper tiny 모델**로 2초 단위 오디오를 분석해 "머스탱" 발화를 감지합니다.

- ✅ 완전 무료, 오프라인 동작
- ✅ 최초 실행 시 모델 자동 다운로드 (~75MB)
- ✅ 오인식 패턴 자동 대응 ("스탱", "머스탬" 등)
- ⚡ Intel/AMD CPU에서도 빠르게 동작 (10코어 이상 권장)

---

## Gmail 앱 비밀번호 발급

1. [Google 계정](https://myaccount.google.com) → **보안** → **2단계 인증** 활성화
2. **앱 비밀번호** → 앱: "메일" → **생성**
3. 16자리 비밀번호를 `GMAIL_APP_PASSWORD`에 입력 (공백 포함 그대로)

---

## 프로젝트 구조

```
mustang-voice-agent/
├── mustang.py            # 메인 실행 파일
├── widget_server.py      # 위젯 WebSocket/HTTP 서버
├── requirements.txt
├── config/
│   ├── .env              # 설정 파일 (직접 생성, git 제외)
│   └── .env.example
├── core/
│   ├── claude_runner.py  # Claude AI 처리
│   ├── stt.py            # 음성 인식 (Whisper)
│   ├── tts.py            # 음성 합성
│   ├── wakeword.py       # 웨이크워드 감지 (faster-whisper)
│   ├── skill_manager.py  # 스킬 관리
│   └── scheduler.py      # 예약 실행
└── skills/
    ├── check_calendar.py
    ├── check_email.py
    ├── google_drive.py
    ├── browser_automation.py
    └── ...
```

---

## 자주 묻는 질문

**Q. `illegal hardware instruction` 오류가 납니다 (Mac)**  
A. Intel Python이 ARM Mac에서 실행되고 있습니다. Miniforge로 ARM Python을 새로 설치하세요.

**Q. 웨이크워드가 잘 감지되지 않습니다**  
A. "머스탱"을 또렷하고 조금 크게 발음해보세요. 주변 소음이 많으면 오탐이 생길 수 있습니다.  
정확도를 높이려면 `core/wakeword.py`의 모델을 `"tiny"` → `"small"`로 변경하세요 (속도는 느려짐).

**Q. Claude가 응답하지 않습니다**  
A. Claude Code CLI가 설치되어 있는지 확인하세요: `which claude`  
없으면: `npm install -g @anthropic-ai/claude-code`

**Q. 위젯이 바탕화면에 표시되지 않습니다**  
A. GeekTool URL이 올바른지 확인하세요. `http://localhost:8766` 대신 `file://` 경로를 사용하세요.  
mustang.py가 실행 중이어야 위젯 서버가 동작합니다.

---

## 라이선스

MIT License
