# 🐎 음성명령 AI (Mustang AI)

macOS / Windows에서 동작하는 로컬 AI 음성 명령 에이전트입니다.  
**"머스탱"** 이라고 부르면 깨어나고, 음성 명령을 처리합니다.

## 주요 기능

| 기능 | 설명 |
|------|------|
| 🎤 웨이크워드 감지 | "머스탱" 호출 시 자동 활성화 |
| 🗣️ 음성 인식 (STT) | Whisper 기반 한국어 음성 → 텍스트 |
| 🔊 음성 합성 (TTS) | macOS 기본 TTS / Windows SAPI |
| 🤖 AI 처리 | Claude Code CLI 기반 자연어 명령 처리 |
| 📅 일정 관리 | Google 캘린더 조회/등록 |
| 📧 이메일 | Gmail 확인 및 발송 |
| 🌐 브라우저 | 웹 자동화 (Playwright) |
| 📁 Google Drive | 파일 검색/관리 |
| 📱 텔레그램 | 봇을 통한 원격 명령 |
| ⏰ 예약 실행 | 특정 시간에 명령 자동 실행 |
| 🖥️ 화면 제어 | 스크린샷, 앱 실행 |

---

## 설치 방법

> **플랫폼을 선택하세요**

- [Mac ARM (M1/M2/M3/M4)](#-mac-arm-m1m2m3m4)
- [Mac Intel](#-mac-intel)
- [Windows](#-windows)

---

## 🍎 Mac ARM (M1/M2/M3/M4)

### 1단계 — ARM Homebrew 설치

터미널을 열고 실행합니다.

```bash
arch -arm64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

설치 후 터미널에서 PATH 추가 (`.zshrc` 또는 `.bash_profile`):

```bash
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### 2단계 — ARM Python 설치 (Miniforge)

```bash
brew install --cask miniforge
conda create -n mustang python=3.11 -y
conda activate mustang
```

> **주의:** 기존에 Anaconda가 Intel로 설치되어 있으면 반드시 Miniforge를 별도로 설치해야 합니다.

### 3단계 — PortAudio 설치 (pyaudio 의존성)

```bash
/opt/homebrew/bin/brew install portaudio
```

### 4단계 — 프로젝트 클론 및 패키지 설치

```bash
git clone https://github.com/jakalee/mustang-voice-agent.git
cd mustang-voice-agent

# pyaudio는 ARM portaudio 링크로 별도 설치
LDFLAGS="-L/opt/homebrew/lib" CPPFLAGS="-I/opt/homebrew/include" \
  pip install pyaudio --no-binary pyaudio --no-cache-dir

# 나머지 패키지
pip install -r requirements.txt
```

### 5단계 — 웨이크워드 모델 준비

1. [Picovoice Console](https://console.picovoice.ai) 에서 무료 계정 생성
2. **Access Key** 발급
3. Porcupine에서 한국어 커스텀 웨이크워드 생성 (예: "머스탱") → `.ppn` 파일 다운로드
4. 한국어 모델 파일 `porcupine_params_ko.pv` 다운로드

### 6단계 — 설정 파일 작성

```bash
cp config/.env.example config/.env
```

`config/.env` 파일을 열어서 값 입력:

```
PICOVOICE_ACCESS_KEY=여기에_발급받은_키
KEYWORD_PATH=/절대경로/머스탱_ko_mac.ppn
KO_MODEL_PATH=/절대경로/porcupine_params_ko.pv

GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# 텔레그램 봇 (선택 — python mustang.py --telegram 사용 시)
# 1. 텔레그램에서 @BotFather 에게 /newbot 명령으로 봇 생성 후 토큰 발급
# 2. 본인 채팅 ID는 https://t.me/userinfobot 에서 확인
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=123456789
```

### 7단계 — 실행

```bash
conda activate mustang

# 음성 모드 (웨이크워드 대기)
python mustang.py

# 텍스트 모드 (키보드 입력)
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

### 4단계 — 웨이크워드 모델 준비

Mac ARM의 [5단계](#5단계--웨이크워드-모델-준비)와 동일합니다.  
단, `.ppn` 파일 생성 시 플랫폼을 **mac (x86_64)** 으로 선택하세요.

### 5단계 — 설정 및 실행

```bash
cp config/.env.example config/.env
```

`config/.env` 파일을 열어서 값 입력:

```
PICOVOICE_ACCESS_KEY=여기에_발급받은_키
KEYWORD_PATH=/절대경로/머스탱_ko_mac.ppn
KO_MODEL_PATH=/절대경로/porcupine_params_ko.pv

GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# 텔레그램 봇 (선택 — python mustang.py --telegram 사용 시)
# 1. 텔레그램에서 @BotFather 에게 /newbot 명령으로 봇 생성 후 토큰 발급
# 2. 본인 채팅 ID는 https://t.me/userinfobot 에서 확인
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=123456789
```

```bash
source venv/bin/activate
python mustang.py
```

---

## 🪟 Windows

### 1단계 — Python 설치

[python.org](https://www.python.org/downloads/) 에서 **Python 3.11** 다운로드 후 설치.  
설치 시 **"Add Python to PATH"** 체크 필수.

### 2단계 — 프로젝트 클론

PowerShell 또는 명령 프롬프트에서:

```powershell
git clone https://github.com/jakalee/mustang-voice-agent.git
cd mustang-voice-agent

python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
```

### 3단계 — PortAudio 및 PyAudio 설치

Windows에서는 pip로 바로 설치됩니다:

```powershell
pip install pyaudio
```

만약 오류가 나면 [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) 에서 `.whl` 파일을 받아 설치:

```powershell
pip install PyAudio‑0.2.14‑cp311‑cp311‑win_amd64.whl
```

### 4단계 — 나머지 패키지 설치

```powershell
pip install -r requirements.txt
```

> `pyobjc-framework-Quartz`는 macOS 전용이라 Windows에서 오류가 나도 무시하세요.  
> `requirements.txt`에 `sys_platform == "darwin"` 조건이 있어 자동 스킵됩니다.

### 5단계 — 웨이크워드 모델 준비

Mac ARM의 [5단계](#5단계--웨이크워드-모델-준비)와 동일합니다.  
단, `.ppn` 파일 생성 시 플랫폼을 **windows** 로 선택하세요.

### 6단계 — 설정 파일 작성

```powershell
copy config\.env.example config\.env
```

메모장 또는 VS Code로 `config\.env` 열어서 값 입력:

```
PICOVOICE_ACCESS_KEY=여기에_발급받은_키
KEYWORD_PATH=C:\절대경로\머스탱_ko_windows.ppn
KO_MODEL_PATH=C:\절대경로\porcupine_params_ko.pv

GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# 텔레그램 봇 (선택 — python mustang.py --telegram 사용 시)
# 1. 텔레그램에서 @BotFather 에게 /newbot 명령으로 봇 생성 후 토큰 발급
# 2. 본인 채팅 ID는 https://t.me/userinfobot 에서 확인
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=123456789
```

### 7단계 — 실행

```powershell
venv\Scripts\activate

# 음성 모드
python mustang.py

# 텍스트 모드
python mustang.py --text
```

> **Windows TTS:** macOS의 `say` 명령어 대신 Windows SAPI를 사용합니다.  
> `core/tts.py`에서 자동으로 플랫폼을 감지합니다.

---

## Gmail 앱 비밀번호 발급 방법

1. [Google 계정](https://myaccount.google.com) → **보안** → **2단계 인증** 활성화
2. **앱 비밀번호** → 앱: "메일", 기기: "Mac/Windows" → **생성**
3. 16자리 비밀번호를 `GMAIL_APP_PASSWORD`에 입력 (공백 포함 그대로)

---

## 프로젝트 구조

```
음성명령ai/
├── mustang.py          # 메인 실행 파일
├── requirements.txt    # 패키지 목록
├── config/
│   ├── .env            # 설정 파일 (직접 생성, git 제외)
│   └── .env.example    # 설정 파일 예시
├── core/
│   ├── claude_runner.py  # Claude AI 처리
│   ├── stt.py            # 음성 인식
│   ├── tts.py            # 음성 합성
│   ├── skill_manager.py  # 스킬 관리
│   └── scheduler.py      # 예약 실행
└── skills/
    ├── google_calendar.py
    ├── google_gmail.py
    ├── google_drive.py
    ├── browser.py
    ├── youtube.py
    └── ...
```

---

## 자주 묻는 질문

**Q. `illegal hardware instruction` 오류가 납니다 (Mac)**  
A. Intel Python이 ARM Mac에서 실행되고 있습니다. Miniforge로 ARM Python을 새로 설치하세요. ([Mac ARM 설치 가이드](#-mac-arm-m1m2m3m4))

**Q. `symbol not found: _PaMacCore_SetupChannelMap` 오류**  
A. PortAudio가 없거나 Intel 버전입니다. `brew install portaudio` 후 pyaudio를 소스에서 재설치하세요.

**Q. 웨이크워드가 감지되지 않습니다**  
A. `.ppn` 파일이 현재 플랫폼(mac arm / mac x86 / windows)용으로 생성됐는지 확인하세요.

**Q. Claude가 응답하지 않습니다**  
A. Claude Code CLI가 설치되어 있고 `claude` 명령어가 터미널에서 동작하는지 확인하세요.

---

## 라이선스

MIT License
