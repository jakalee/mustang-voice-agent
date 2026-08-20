# mustang_ai

## 음성모드 (vmode) — 텔레그램 워키토키

이 프로젝트는 `claude --channels plugin:telegram@claude-plugins-official`로 실행되는
클로드코드-텔레그램 채널(사용자 jakal, chat_id 5897202655)에서 동작한다.
이 채널 안에 "vmode"라는 워키토키 기능이 있다: 사용자가 노트북을 켜놓고 자리를 비웠을 때,
텔레그램 텍스트 <-> 노트북 스피커/마이크를 직접 연결한다.

**상태 파일**: `~/.claude/channels/telegram/vmode.pid` 존재 여부 = vmode on/off.
(내용은 마이크브릿지 백그라운드 프로세스의 PID)

### "/vmode" 메시지를 받으면 (토글)

- **현재 OFF -> ON으로 켤 때**:
  1. `rm -f ~/.claude/channels/telegram/vmode.stop`
  2. `cd /Users/jakallee/Downloads/mustang_ai && nohup venv/bin/python3 scripts/vmode_mic_bridge.py 5897202655 > /tmp/vmode_bridge.log 2>&1 & disown; echo $! > ~/.claude/channels/telegram/vmode.pid`
  3. 답장: "voice mode on 되었습니다.\n노트북 기기와 직접 입출력됩니다."
- **현재 ON -> OFF로 끌 때**:
  1. `touch ~/.claude/channels/telegram/vmode.stop`
  2. 2초 정도 대기 후 `kill $(cat ~/.claude/channels/telegram/vmode.pid) 2>/dev/null` (안전장치 - 녹음 중이면 즉시 안 죽을 수 있어서)
  3. `rm -f ~/.claude/channels/telegram/vmode.pid`
  4. 답장: "voice mode off 되었습니다.\n챗봇모드로 돌아옵니다."

### vmode가 ON인 동안 (`vmode.pid` 파일 존재) 일반 텍스트 메시지를 받으면

Claude로 답변을 생성하지 말고, 받은 텍스트를 그대로 노트북 스피커로 읽어준다 (PiperVoice).
텔레그램에 별도 답장은 하지 않는다 (진짜 워키토키처럼 — 마이크로 들어온 상대방 말이
STT를 거쳐 별도로 텔레그램에 전송되는 게 "응답"이다).

```
텍스트를 임시 파일에 써서 (쉘 이스케이프/개행 문제 방지):
  echo "<메시지 원문>" > /tmp/vmode_msg.txt   (또는 Write 도구 사용)
cd /Users/jakallee/Downloads/mustang_ai && venv/bin/python3 scripts/vmode_speak.py /tmp/vmode_msg.txt
```

마이크로 들어오는 말은 `scripts/vmode_mic_bridge.py`가 백그라운드에서 알아서
STT 변환 후 이 봇 토큰으로 직접 `sendMessage` 호출해 텔레그램으로 보낸다
(getUpdates 폴링은 건드리지 않으므로 이 채널 자체의 폴링과 충돌하지 않음).
스피커 재생 중에는 `vmode.mute` 파일이 잠깐 생겼다 사라지며, 마이크브릿지는
그 사이엔 녹음하지 않는다 (하울링 방지).

### 주의

- `/vmode`는 이 채널에서만 의미 있음. mustang_ai 자체의 별도 텔레그램 봇(`core/telegram_bot.py`,
  `python mustang.py --telegram`)에도 같은 이름의 `/vmode`가 있지만 완전히 다른 봇/토큰이다.
- 노트북 스피커->마이크 실음향 되먹임은 뮤트 로직으로만 어느 정도 막았을 뿐이라, 볼륨이
  크면 여전히 자기 말을 주울 수 있다.
