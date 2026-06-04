// Mustang AI Widget for Übersicht
// 클릭 → 텍스트 입력 → Enter → WebSocket으로 명령 전송

import { React } from 'uebersicht'
const { useEffect, useRef, useState } = React

export const refreshFrequency = false

const SIZE = 300

export const className = `
  left: 30px;
  top: 5px;
  width: ${SIZE}px;
  height: ${SIZE}px;
  background: transparent;

  canvas {
    position: absolute;
    top: 0; left: 0;
    cursor: pointer;
  }
  #mu-status {
    position: absolute;
    bottom: 38px;
    width: 100%;
    text-align: center;
    font-family: -apple-system, sans-serif;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.5);
    pointer-events: none;
  }
  #mu-subtext {
    position: absolute;
    bottom: 14px;
    width: 92%;
    left: 4%;
    text-align: center;
    font-family: -apple-system, sans-serif;
    font-size: 12px;
    color: rgba(255,255,255,0.75);
    pointer-events: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  #mu-input-wrap {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    display: flex;
    align-items: center;
    padding: 0 12px;
    box-sizing: border-box;
  }
  #mu-input {
    width: 100%;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    padding: 7px 16px;
    color: #fff;
    font-family: -apple-system, sans-serif;
    font-size: 13px;
    outline: none;
    backdrop-filter: blur(8px);
  }
  #mu-input::placeholder {
    color: rgba(255,255,255,0.35);
  }
`

const PARAMS = {
  idle:      { speed: 0.002,  rBase: 0.20, rMod: 0.00, alpha: 160, color: [160, 200, 255] },
  listening: { speed: 0.0045, rBase: 0.22, rMod: 0.02, alpha: 210, color: [100, 220, 180] },
  thinking:  { speed: 0.010,  rBase: 0.23, rMod: 0.03, alpha: 230, color: [200, 160, 255] },
  speaking:  { speed: 0.006,  rBase: 0.21, rMod: 0.00, alpha: 255, color: [255, 200, 100] },
}

const STATUS_TEXT = { idle: '대기 중', listening: '듣는 중', thinking: '생각 중', speaking: '말하는 중' }

function MustangWidget() {
  const canvasRef = useRef(null)
  const stateRef  = useRef({ state: 'idle', amplitude: 0, targetAmp: 0 })
  const wsRef     = useRef(null)
  const [inputVisible, setInputVisible] = useState(false)
  const [inputVal, setInputVal]         = useState('')
  const inputRef  = useRef(null)

  // 입력창 열릴 때 포커스
  useEffect(() => {
    if (inputVisible && inputRef.current) {
      setTimeout(() => inputRef.current && inputRef.current.focus(), 50)
    }
  }, [inputVisible])

  // 명령 전송
  function sendCommand(text) {
    const ws = wsRef.current
    if (!text.trim() || !ws || ws.readyState !== 1) return
    ws.send(JSON.stringify({ command: text.trim() }))
    setInputVal('')
    setInputVisible(false)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      e.preventDefault()
      sendCommand(inputVal)
    } else if (e.key === 'Escape') {
      setInputVisible(false)
      setInputVal('')
    }
  }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const CX = SIZE / 2, CY = SIZE / 2
    const CIRCLES = 60

    const circles = Array.from({ length: CIRCLES }, () => ({
      pointNum: Math.floor(Math.random() * 24 + 24),
      degree:   Math.random() * Math.PI * 2,
      seed:     Math.random() * 200,
    }))

    let animId
    const t0 = performance.now()

    function draw() {
      const { state, amplitude: amp } = stateRef.current
      const pm = PARAMS[state] || PARAMS.idle
      const t  = (performance.now() - t0) / 1000

      stateRef.current.amplitude += (stateRef.current.targetAmp - stateRef.current.amplitude) * 0.12

      const ampMod = state === 'speaking' ? amp * 0.18 : pm.rMod
      const pulse  = state !== 'speaking' ? Math.sin(t) * pm.rMod : 0
      const baseR  = SIZE * (pm.rBase + pulse + ampMod)

      ctx.clearRect(0, 0, SIZE, SIZE)

      const [r, g, b] = pm.color
      circles.forEach((c, idx) => {
        const a = Math.max(0, (pm.alpha - idx * 0.5) / 255)
        ctx.strokeStyle = `rgba(${r},${g},${b},${a.toFixed(3)})`
        ctx.lineWidth   = 0.7
        ctx.beginPath()
        for (let j = 0; j <= c.pointNum; j++) {
          const angle = (j / c.pointNum) * Math.PI * 2 + c.degree
          const wobble = 1
            + 0.06 * Math.sin(c.seed * 2.1 + angle * 3)
            + 0.04 * Math.sin(c.seed * 3.7 + angle * 5)
            + 0.02 * Math.sin(c.seed * 5.3 + angle * 7)
          const curR = baseR * wobble
          const x = CX + curR * Math.cos(angle)
          const y = CY + curR * Math.sin(angle)
          j === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        }
        ctx.closePath()
        ctx.stroke()
        c.seed += pm.speed
      })

      animId = requestAnimationFrame(draw)
    }
    draw()

    // WebSocket
    let wsTimer
    function connectWS() {
      try {
        const ws = new WebSocket('ws://127.0.0.1:8765')
        wsRef.current = ws
        ws.onmessage = (e) => {
          try {
            const msg = JSON.parse(e.data)
            const statusEl  = document.getElementById('mu-status')
            const subtextEl = document.getElementById('mu-subtext')
            if (msg.state) {
              stateRef.current.state = msg.state
              if (statusEl) statusEl.textContent = STATUS_TEXT[msg.state] || msg.state
              if (msg.state === 'idle' || msg.state === 'listening') {
                if (subtextEl) subtextEl.textContent = ''
              }
              if (msg.text && subtextEl) subtextEl.textContent = msg.text
            }
            if (!msg.state && msg.text) {
              if (subtextEl) subtextEl.textContent = msg.text
            }
            if (msg.amplitude !== undefined) {
              stateRef.current.targetAmp = Math.min(1.0, msg.amplitude)
            }
          } catch (_) {}
        }
        ws.onclose = () => { wsTimer = setTimeout(connectWS, 3000) }
        ws.onerror = () => ws.close()
      } catch (_) {
        wsTimer = setTimeout(connectWS, 3000)
      }
    }
    connectWS()

    return () => {
      cancelAnimationFrame(animId)
      clearTimeout(wsTimer)
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  return (
    <div>
      <canvas
        ref={canvasRef}
        width={SIZE}
        height={SIZE}
        onClick={() => { setInputVisible(v => !v); setInputVal('') }}
      />
      <div id="mu-status">대기 중</div>
      <div id="mu-subtext"></div>
      {inputVisible && (
        <div id="mu-input-wrap">
          <input
            id="mu-input"
            ref={inputRef}
            type="text"
            placeholder="명령을 입력하세요..."
            value={inputVal}
            onChange={e => setInputVal(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>
      )}
    </div>
  )
}

export const render = () => <MustangWidget />
