# 텔레그램으로 Claude Code 세션에 연결하기 (Channels)

Mac에서 돌아가는 Claude Code 세션을 텔레그램 봇에 연결해서, 폰으로 메시지를
보내면 그 세션이 응답하도록 설정하는 방법입니다. Anthropic 공식
`claude-plugins-official` 마켓플레이스의 `telegram` 플러그인을 사용합니다.

> 실험적(research preview) 기능입니다. 텔레그램으로 오는 메시지가 그대로
> 세션에 프롬프트로 들어가기 때문에 프롬프트 인젝션 위험이 있습니다. 반드시
> 아래 "잠그기" 단계까지 진행하세요.

## 사전 준비

- Claude Code CLI 최신 버전 (`npm install -g @anthropic-ai/claude-code`)
- [Bun](https://bun.sh) 런타임 — 플러그인의 MCP 서버가 Bun으로 동작합니다.
  ```bash
  brew install oven-sh/bun/bun
  ```

## 설정 순서

**1. BotFather로 봇 생성**

텔레그램에서 [@BotFather](https://t.me/BotFather)에게 `/newbot` 전송 →
이름/유저네임 입력 → 토큰 발급받기.

**2. 플러그인 설치**

```bash
claude plugin install telegram@claude-plugins-official
```

**3. 토큰 등록**

Claude Code 세션 안에서:

```
/telegram:configure <발급받은 토큰>
```

`~/.claude/channels/telegram/.env`에 `TELEGRAM_BOT_TOKEN`으로 저장됩니다.
직접 파일을 만들어 넣어도 됩니다. **이 파일은 절대 git에 커밋하지 마세요.**

**4. channels 플래그로 재시작**

```bash
claude --channels plugin:telegram@claude-plugins-official
```

`--channels`는 실제 TTY(터미널)가 있어야 동작합니다. 백그라운드/파이프로는
실행되지 않습니다.

**5. 페어링**

세션이 뜬 상태에서 텔레그램으로 봇에게 아무 메시지나 DM → 봇이 6자리
페어링 코드로 답장 → Claude Code 세션에서:

```
/telegram:access pair <코드>
```

**6. 잠그기**

페어링이 끝나면 낯선 사람이 더 이상 페어링 코드를 못 받도록 정책을 바꿉니다:

```
/telegram:access policy allowlist
```

## 참고

- 세션을 계속 열어둬야 브릿지가 유지됩니다. 터미널 창을 닫으면 연결이
  끊깁니다.
- 여러 봇을 동시에 운영하려면 `TELEGRAM_STATE_DIR` 환경변수로 봇마다 다른
  상태 디렉터리를 지정하세요.
- MCP 서버(`bun server.ts`)가 뜨지 않으면 응답이 없습니다. 프로세스 목록에서
  `bun server.ts`가 살아있는지 확인하세요. 안 떠 있으면 세션을 껐다 다시
  켜보세요.

## 로그인 시 자동 시작 (tmux + launchd)

위의 4번 단계(`claude --channels ...`)를 매번 터미널을 열어 수동으로 치는 대신,
tmux 세션 안에서 백그라운드로 띄우고 로그인 시 자동 실행되게 만들 수
있습니다. 실제 사용 중인 스크립트/plist를 이 저장소에 그대로 넣어뒀습니다:

- [`scripts/telegram-channel/start-telegram-session.sh`](../scripts/telegram-channel/start-telegram-session.sh)
- [`scripts/telegram-channel/com.mustang.claude-telegram.plist`](../scripts/telegram-channel/com.mustang.claude-telegram.plist)

설치:

```bash
mkdir -p ~/.claude/scripts
cp scripts/telegram-channel/start-telegram-session.sh ~/.claude/scripts/
cp scripts/telegram-channel/com.mustang.claude-telegram.plist ~/Library/LaunchAgents/
```

등록/해제:

```bash
launchctl load ~/Library/LaunchAgents/com.mustang.claude-telegram.plist    # 등록 (다음 로그인부터 자동 실행)
launchctl unload ~/Library/LaunchAgents/com.mustang.claude-telegram.plist  # 해제
```

세션 들여다보기 / 직접 명령 넣기:

```bash
tmux attach -t claude-telegram   # 세션 안으로 들어가기 (Ctrl+B, D로 빠져나오기)
```

주의:
- `RunAtLoad`는 **로그인할 때** 실행되는 것이지 Mac이 완전히 종료됐다가 켜질
  때만이 아니라 로그아웃 후 재로그인해도 다시 뜹니다.
- 세션이 이미 있으면(`tmux has-session`) 새로 안 띄우므로 중복 실행 걱정은
  없지만, **다른 방식(수동 Terminal.app 등)으로 같은 봇을 또 띄우면 텔레그램
  polling이 충돌**할 수 있으니 봇 하나당 세션은 하나만 유지하세요.

## 실전에서 겪은 문제들

- **Claude Code CLI 자체 OAuth가 만료/취소될 수 있음.** `--channels` 세션
  안에서 슬래시 명령이 `API Error: 401 OAuth access token has been revoked`
  로 실패하면, 별도 터미널에서 `claude auth login` 실행 → 브라우저에서
  재로그인 → 다시 시도.
- **MCP 서버가 처음엔 안 뜨는 경우가 있었음.** 세션은 떠 있는데
  `ps aux | grep bun`으로 봐도 `bun server.ts`가 안 보이면, 텔레그램에 메시지를
  보내도 응답이 없거나 "Gateway shutting down" 메시지만 옵니다. 이럴 땐
  세션 프로세스를 `kill`하고 `claude --channels ...`를 다시 실행하면
  `bun server.ts`가 정상적으로 붙습니다.
- **페어링 승인 프롬프트.** `/telegram:access pair <코드>`를 실행하면
  access.json을 덮어써도 되는지 확인 프롬프트가 뜹니다 (`1. Yes` 선택).
  자동화 스크립트로 이 창을 조작할 땐 `osascript`의
  `System Events`(키 입력)는 손쉬운 사용(Accessibility) 권한이 없으면
  막히므로, `Terminal`의 `do script "1" in <tab>`처럼 셸에 직접 문자를
  흘려넣는 방식이 더 안정적이었습니다.
