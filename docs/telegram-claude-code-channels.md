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
