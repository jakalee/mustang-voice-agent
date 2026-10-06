# Agent Manifest

## Identity
- **Name**: 재규어봇 (Jaguar Bot)
- **Version**: 1.0.0
- **Description**: 개인용 Hermes 에이전트 "재규어"에 음성 명령을 전달하고, 응답을 안경 디스플레이에 표시하는 개인 개발용 에이전트.
- **Author**: (your name)

## Capabilities
- **Permissions**:
  - microphone (음성 명령 인식)
- **Network**:
  - https://xxxx.synology.me (Hermes API, OpenAI 호환 /v1/chat/completions)

## Instructions
- 사용자가 "재규어봇", "재규어", "Jaguar" 에게 질문하거나 작업을 요청하면 이 에이전트를 연다.
- 사용자의 발화 원문을 그대로 query 로 전달한다.

## Boundaries
- 개인 개발용. 스토어 배포 대상 아님 (API 토큰이 패키지에 포함되므로 절대 공개/배포 금지).
