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
| 🖥️ 바탕화면 위젯 | p5.js 파형 원이 AI 상태에 따라 실시간 반응 (Übersicht) |
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

`config/.env` 파일을 열어서 필요한 값 입력 (Gmail, 텔레그램은 선택):

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

### 3단계 — 설정 및 실행

```powershell
copy config\.env.example config\.env

venv\Scripts\activate
python mustang.py
```

---

## 🖥️ 바탕화면 위젯 (macOS + Übersicht)

AI가 말하는 동안 p5.js 파형 원이 실시간으로 반응하는 위젯을 바탕화면에 배치합니다.

### 상태별 시각 효과

| 상태 | 색상 | 동작 |
|------|------|------|
| 대기 중 | 🔵 파란색 | 느리고 잔잔한 파형 |
| 듣는 중 | 🟢 초록색 | 중간 속도, 팽창 |
| 생각 중 | 🟣 보라색 | 빠르고 복잡한 파형 + 사용자 발화 표시 |
| 말하는 중 | 🟡 황금색 | 진폭에 따라 박동 + AI 응답 표시 |

---

### 1단계 — Übersicht 설치

👉 **[Übersicht 다운로드](https://tracesof.net/uebersicht/)** (무료, macOS 전용)

설치 후 메뉴바에 Übersicht 아이콘이 생깁니다.

### 2단계 — 위젯 파일 복사

Übersicht 위젯 폴더에 두 파일을 복사합니다.

```bash
# Übersicht 위젯 폴더 열기
open ~/Library/Application\ Support/Übersicht/widgets/

# 위젯 파일 복사
cp mustang-voice-agent/ubersicht/mustang-ai.jsx \
   ~/Library/Application\ Support/Übersicht/widgets/

cp mustang-voice-agent/ubersicht/mustang-starter.jsx \
   ~/Library/Application\ Support/Übersicht/widgets/
```

또는 터미널 한 줄로:

```bash
cp mustang-voice-agent/ubersicht/*.jsx \
   ~/Library/Application\ Support/Übersicht/widgets/
```

### 3단계 — 위젯 위치/크기 조정

`mustang-ai.jsx` 파일 상단에서 조정:

```js
const SIZE = 400        // 위젯 크기 (px)
// 위치는 className의 left/top 값으로 조정
// left: 20px;  top: 20px;  ← 왼쪽 상단
// right: 20px; top: 20px;  ← 오른쪽 상단
```

### 4단계 — 새로고침

**Übersicht 메뉴바 → Refresh All Widgets**

### 동작 원리

```
"머스탱" 발화
    ↓
mustang.py (faster-whisper 웨이크워드 감지)
    ↓
WidgetBridge → WebSocket (ws://localhost:8765)
    ↓
mustang-ai.jsx (Canvas 애니메이션) → 파형 원 실시간 반응
    ↓
Übersicht → 바탕화면에 투명 위젯으로 표시
```

---

### 로그인 시 자동 시작 설정

mustang.py가 로그인 시 자동으로 시작되도록 launchd에 등록합니다.

```bash
# plist 파일 생성
cat > ~/Library/LaunchAgents/com.mustang.agent.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.mustang.agent</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/anaconda3/bin/python3</string>
    <string>-u</string>
    <string>/Users/사용자명/mustang-voice-agent/mustang.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>/Users/사용자명/mustang-voice-agent</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ThrottleInterval</key>
  <integer>5</integer>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/anaconda3/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>PYTHONUNBUFFERED</key>
    <string>1</string>
    <key>KMP_DUPLICATE_LIB_OK</key>
    <string>TRUE</string>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/mustang-agent.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/mustang-agent-err.log</string>
</dict>
</plist>
EOF

# 등록
launchctl load ~/Library/LaunchAgents/com.mustang.agent.plist
```

> `/Users/사용자명/` 부분을 실제 사용자 이름으로 변경하세요. (`echo $HOME` 으로 확인)

**mustang 시작/중지 명령어:**

```bash
# 중지
launchctl unload ~/Library/LaunchAgents/com.mustang.agent.plist

# 시작
launchctl load ~/Library/LaunchAgents/com.mustang.agent.plist

# 로그 확인
tail -f /tmp/mustang-agent.log
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
├── mustang.py            # 메인 실행 파일 (위젯 서버 내장)
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
├── skills/
│   ├── check_calendar.py
│   ├── check_email.py
│   ├── google_drive.py
│   ├── browser_automation.py
│   ├── youtube.py        # YouTube 재생 (Chrome 쿠키 활용)
│   └── ...
├── widget/
│   ├── index.html        # 위젯 HTML (레거시/브라우저 직접 열기용)
│   └── p5.min.js
└── ubersicht/
    ├── mustang-ai.jsx    # Übersicht 메인 위젯 (파형 원 애니메이션)
    └── mustang-starter.jsx  # Übersicht 자동 시작 위젯
```

---

## 자주 묻는 질문

**Q. `illegal hardware instruction` 오류가 납니다 (Mac)**  
A. Intel Python이 ARM Mac에서 실행되고 있습니다. Miniforge로 ARM Python을 새로 설치하세요.

**Q. 웨이크워드가 잘 감지되지 않습니다**  
A. "머스탱"을 또렷하고 조금 크게 발음해보세요. 정확도를 높이려면 `core/wakeword.py`의 모델을 `"tiny"` → `"small"`로 변경하세요 (속도는 느려짐).

**Q. Claude가 응답하지 않습니다**  
A. Claude Code CLI가 설치되어 있는지 확인하세요: `which claude`  
없으면: `npm install -g @anthropic-ai/claude-code`

**Q. 위젯이 바탕화면에 표시되지 않습니다**  
A. Übersicht 메뉴바 → Refresh All Widgets 를 클릭하세요.  
mustang.py가 실행 중이어야 WebSocket 서버(8765)가 동작합니다.

**Q. mustang.py를 끄고 싶습니다**  
A. launchd로 등록한 경우: `launchctl unload ~/Library/LaunchAgents/com.mustang.agent.plist`

---

## 라이선스

MIT License
