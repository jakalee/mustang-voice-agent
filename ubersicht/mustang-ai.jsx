// Mustang AI Widget for Übersicht
// p5.js 없이 Canvas API로 직접 구현 — WebSocket으로 AI 상태 수신

import { React, run } from 'uebersicht'
const { useEffect, useRef } = React

const CMD_START   = 'launchctl start com.mustang.agent'
const CMD_STOP    = 'launchctl stop com.mustang.agent'
const CMD_RESTART = 'launchctl kickstart -k gui/$(id -u)/com.mustang.agent'

export const refreshFrequency = false

const SIZE = 400

export const className = `
  left: 20px;
  top: 20px;
  width: ${SIZE}px;
  height: ${SIZE}px;
  pointer-events: none;
  background: transparent;

  canvas {
    position: absolute;
    top: 0; left: 0;
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
  #mu-controls {
    position: absolute;
    top: 10px;
    right: 10px;
    display: flex;
    gap: 6px;
    pointer-events: auto;
    opacity: 0.25;
    transition: opacity 0.2s ease;
  }
  #mu-controls:hover {
    opacity: 1;
  }
  #mu-controls button {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    border: none;
    background: rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.85);
    font-size: 11px;
    line-height: 1;
    cursor: pointer;
    font-family: -apple-system, sans-serif;
  }
  #mu-controls button:hover {
    background: rgba(255,255,255,0.25);
  }
  #mu-controls button:active {
    background: rgba(255,255,255,0.4);
  }
`

// ── Perlin noise (간단한 구현) ──────────────────────────────────
function makeNoise() {
  const p = Array.from({length: 512}, (_, i) => i < 256 ? i : 0)
  for (let i = 255; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [p[i], p[j]] = [p[j], p[i]]
  }
  for (let i = 0; i < 256; i++) p[i + 256] = p[i]
  const fade = t => t * t * t * (t * (t * 6 - 15) + 10)
  const lerp  = (a, b, t) => a + t * (b - a)
  const grad  = (h, x, y, z) => {
    const v = h & 15
    const u = v < 8 ? x : y
    const w = v < 4 ? y : (v === 12 || v === 14 ? x : z)
    return ((v & 1) ? -u : u) + ((v & 2) ? -w : w)
  }
  return (x, y, z = 0) => {
    const X = Math.floor(x) & 255, Y = Math.floor(y) & 255, Z = Math.floor(z) & 255
    x -= Math.floor(x); y -= Math.floor(y); z -= Math.floor(z)
    const u = fade(x), v = fade(y), w = fade(z)
    const A  = p[X] + Y,  AA = p[A] + Z,  AB = p[A+1] + Z
    const B  = p[X+1] + Y, BA = p[B] + Z, BB = p[B+1] + Z
    return (lerp(
      lerp(lerp(grad(p[AA], x, y, z),    grad(p[BA], x-1, y, z), u),
           lerp(grad(p[AB], x, y-1, z),  grad(p[BB], x-1, y-1, z), u), v),
      lerp(lerp(grad(p[AA+1], x, y, z-1),  grad(p[BA+1], x-1, y, z-1), u),
           lerp(grad(p[AB+1], x, y-1, z-1),grad(p[BB+1], x-1, y-1, z-1), u), v), w)
      + 1) / 2
  }
}

const PARAMS = {
  idle:      { speed: 0.002,  rBase: 0.20, rMod: 0.00, alpha: 80,  color: [160, 200, 255] },
  listening: { speed: 0.0045, rBase: 0.22, rMod: 0.02, alpha: 140, color: [100, 220, 180] },
  thinking:  { speed: 0.010,  rBase: 0.23, rMod: 0.03, alpha: 160, color: [200, 160, 255] },
  speaking:  { speed: 0.006,  rBase: 0.21, rMod: 0.00, alpha: 200, color: [255, 200, 100] },
}

function MustangWidget() {
  const canvasRef = useRef(null)
  const stateRef  = useRef({ state: 'idle', amplitude: 0, targetAmp: 0, subtext: '' })

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const CX = SIZE / 2, CY = SIZE / 2
    const CIRCLES = 60

    // 원 초기화
    const circles = Array.from({ length: CIRCLES }, () => ({
      pointNum:   Math.floor(Math.random() * 24 + 24),
      degree:     Math.random() * Math.PI * 2,
      noiseScale: 0.0025,
      seed:       Math.random() * 200,
      seedStep:   Math.random() * 0.0012 + 0.0008,
    }))

    let animId
    let t0 = performance.now()

    function draw() {
      const { state, amplitude: amp } = stateRef.current
      const pm = PARAMS[state] || PARAMS.idle
      const t  = (performance.now() - t0) / 1000

      // 진폭 스무딩
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

        const pts = []
        for (let j = 0; j <= c.pointNum; j++) {
          const angle = (j / c.pointNum) * Math.PI * 2 + c.degree
          // sin 조합으로 유기적 파형 생성 (Perlin 대체)
          const wobble = 1
            + 0.06 * Math.sin(c.seed * 2.1 + angle * 3)
            + 0.04 * Math.sin(c.seed * 3.7 + angle * 5)
            + 0.02 * Math.sin(c.seed * 5.3 + angle * 7)
          const curR = baseR * wobble
          const x = CX + curR * Math.cos(angle)
          const y = CY + curR * Math.sin(angle)
          if (j === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }
        ctx.closePath()
        ctx.stroke()

        c.seed += pm.speed
      })

      animId = requestAnimationFrame(draw)
    }
    draw()

    // WebSocket 연결
    const STATUS_TEXT = { idle: '대기 중', listening: '듣는 중', thinking: '생각 중', speaking: '말하는 중' }
    let ws, wsTimer

    function connectWS() {
      try {
        ws = new WebSocket('ws://127.0.0.1:8765')
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
              const subtextEl = document.getElementById('mu-subtext')
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
      if (ws) ws.close()
    }
  }, [])

  return (
    <div>
      <canvas ref={canvasRef} width={SIZE} height={SIZE} />
      <div id="mu-status">대기 중</div>
      <div id="mu-subtext"></div>
      <div id="mu-controls">
        <button title="시작" onClick={() => run(CMD_START)}>▶</button>
        <button title="재시작" onClick={() => run(CMD_RESTART)}>⟳</button>
        <button title="종료" onClick={() => run(CMD_STOP)}>⏹</button>
      </div>
    </div>
  )
}

export const render = () => <MustangWidget />
