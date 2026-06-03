// Mustang AI Auto-Starter
// Übersicht 실행 시 mustang.py가 꺼져있으면 자동으로 시작합니다
// 화면에는 보이지 않는 숨김 위젯입니다

export const refreshFrequency = 10000  // 10초마다 살아있는지 확인

export const className = `
  width: 0;
  height: 0;
  overflow: hidden;
  pointer-events: none;
`

export const command = `
  if ! pgrep -f "mustang.py" > /dev/null 2>&1; then
    /opt/anaconda3/bin/python3 -u /Users/jakallee/mustang-voice-agent/mustang.py \
      >> /tmp/mustang-agent.log 2>&1 &
    echo "started"
  else
    echo "running"
  fi
`

export const render = ({ output }) => <div />
