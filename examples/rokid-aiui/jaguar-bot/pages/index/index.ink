<script type="application/json" def>
{
  "navigationBarTitleText": "재규어",
  "description": "개인 AI 에이전트 재규어(Jaguar)에게 질문하거나 작업을 시킬 때 사용한다. 예: '재규어봇한테 오늘 메일 요약해 달라고 해', '재규어한테 물어봐'.",
  "schema": {
    "data": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "재규어에게 전달할 사용자의 질문 또는 명령 원문. 없으면 비워 둔다."
        }
      }
    }
  }
}
</script>

<script setup>
import wx from 'wx';

// ===================== 설정 =====================
const CONFIG = {
  BASE_URL: 'https://xxxx.synology.me',   // 본인의 HTTPS 도메인(역방향 프록시)
  API_KEY: 'YOUR_API_SERVER_KEY',  // Hermes .env 의 API_SERVER_KEY (절대 커밋 금지)
  MODEL: '',               // 비워 두면 /v1/models 의 첫 번째 모델 사용
  ASR_LANG: 'ko-KR',       // 안 되면 자동으로 런타임 기본 언어('')로 재시도
  REQUEST_TIMEOUT_MS: 600000,
  HISTORY_LIMIT: 10,       // 대화 맥락으로 보낼 최근 메시지 수
  AUTO_LISTEN: true,       // 앱 실행 시 바로 듣기 시도
  TTS: true,               // 응답을 소리로 읽기
  TTS_VOICE: null,         // null = 기본 음성. 예: 'female-tianmei' 등
  TTS_VOLUME: 10,          // 0~10, 기본값 1은 너무 작음 → 최대로 설정
  TTS_MAX_CHARS: 300,      // 너무 긴 응답은 앞부분만 읽기
};

const SYSTEM_PROMPT = [
  '너는 사용자의 개인 에이전트 재규어다. 지금 요청은 Rokid AR 안경에서 음성으로 들어왔다.',
  '응답은 폭 480px 단색 안경 화면에 표시된다. 반드시 지켜라:',
  '- 한국어로, 핵심만 3~4문장 이내.',
  '- 마크다운, 표, 코드블록, 이모지, 링크 금지. 평문만.',
  '- 음성 인식 오류로 문장이 어색하면 가장 그럴듯한 뜻으로 해석해서 처리.',
  '- 시간이 오래 걸리는 작업은 처리한 뒤 결과 요약만 보고.',
].join('\n');
// ================================================

const STATUS_TEXT = {
  connecting: '재규어 연결 중…',
  ready: '대기 · 탭 또는 "Hi Rokid"로 말하기',
  listening: '듣는 중…',
  thinking: '재규어 처리 중…',
  answering: '응답 수신 중…',
  done: '완료 · 탭해서 다시 말하기',
  error: '오류 · 탭해서 다시 시도',
  offline: '연결 실패 · 탭해서 재시도',
};

function authHeaders(extra) {
  return Object.assign(
    { Authorization: 'Bearer ' + CONFIG.API_KEY },
    extra || {}
  );
}

function wxGet(url, header) {
  return new Promise((resolve, reject) => {
    if (typeof wx === 'undefined' || !wx || typeof wx.request !== 'function') {
      reject(new Error('wx.request 없음'));
      return;
    }
    wx.request({
      url: url,
      method: 'GET',
      header: header || {},
      timeout: 8000,
      success: (res) => resolve({ status: res && res.statusCode, body: res && res.data }),
      fail: (err) => reject(new Error((err && (err.errMsg || err.message)) || 'network')),
    });
  });
}

function speakText(text) {
  if (!CONFIG.TTS) return;
  let t = String(text || '').replace(/\s+/g, ' ').trim();
  if (!t) return;
  if (t.length > CONFIG.TTS_MAX_CHARS) t = t.slice(0, CONFIG.TTS_MAX_CHARS) + '. 이하 생략.';

  // AIUI 공식 튜토리얼 패턴: 사용 전 typeof 로 기능 존재 확인
  if (typeof speechSynthesis === 'undefined' || typeof SpeechSynthesisUtterance === 'undefined') {
    console.log('[JaguarBot] TTS 사용 불가: speechSynthesis 또는 SpeechSynthesisUtterance 가 런타임에 없음');
    return;
  }

  try {
    const u = new SpeechSynthesisUtterance(t);
    // voice 는 null(기본 음성)이 아닐 때만 설정
    if (CONFIG.TTS_VOICE) u.voice = CONFIG.TTS_VOICE;
    // volume: 0~10, 기본값 1은 너무 작음 → 최대로 설정
    u.volume = CONFIG.TTS_VOLUME;
    // 'enqueue' = 큐에 추가하여 안정적으로 재생 (기본값, 이전 재생을 끊지 않음)
    speechSynthesis.speak(u, 'enqueue');
    console.log('[JaguarBot] TTS 호출됨:', t.slice(0, 60));
  } catch (e) {
    console.log('[JaguarBot] TTS 오류:', e && e.message ? e.message : String(e));
  }
}

function cleanText(text) {
  return String(text || '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/\*\*|__|`/g, '')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/^\s*[-*]\s+/gm, '· ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export default {
  data: {
    state: 'connecting',
    statusText: STATUS_TEXT.connecting,
    transcript: '',
    answer: '',
    errorText: '',
    elapsed: '',
    diag: [],
    answerLines: [],
  },

  // ---------------- 라이프사이클 ----------------
  onLoad(query) {
    this.history = [];
    this.recognition = null;
    this.controller = null;
    this.busy = false;
    this.model = CONFIG.MODEL;
    this.asrLang = CONFIG.ASR_LANG;
    this.pendingQuery = query && query.query ? String(query.query).trim() : '';

    this.connect().then((ok) => {
      if (!ok) return;
      if (this.pendingQuery) {
        const q = this.pendingQuery;
        this.pendingQuery = '';
        this.ask(q);
      } else if (CONFIG.AUTO_LISTEN) {
        this.startListening(true);
      }
    });
  },

  onUnload() {
    this.abortRecognition();
    this.cancelRequest();
  },

  // ---------------- 입력 이벤트 ----------------
  // 템플 탭(Enter): 듣기 시작/종료
  onKeyDown(event) {
    if (!event || event.code !== 'Enter') return;
    this.handlePrimaryAction();
  },

  onKeyUp(event) {
    if (!event) return;
    if (event.code === 'Enter') {
      event.preventDefault();
      return;
    }
    // 처리 중 뒤로가기: 앱 종료 대신 요청 취소
    if (event.code === 'Backspace' && this.busy) {
      event.preventDefault();
      this.cancelRequest();
      this.setState('ready');
    }
  },

  // 페이지가 열려 있을 때 "Hi Rokid" / AI 버튼 → 시스템 비서 대신 재규어로 듣기
  onVoiceWakeup(event) {
    if (event && event.preventDefault) event.preventDefault();
    if (this.busy) return;
    this.startListening(false);
  },

  handlePrimaryAction() {
    // 템플 탭이 keydown + tap 으로 중복 들어오는 경우 방지
    const now = Date.now();
    if (now - (this.lastActionAt || 0) < 500) return;
    this.lastActionAt = now;
    const s = this.data.state;
    if (s === 'listening') {
      this.stopListening();
    } else if (s === 'offline') {
      this.connect().then((ok) => ok && this.startListening(false));
    } else if (!this.busy) {
      this.startListening(false);
    }
  },

  // ---------------- 상태 ----------------
  setState(state, extra) {
    this.setData(Object.assign({ state, statusText: STATUS_TEXT[state] || state }, extra || {}));
  },

  // ---------------- 연결 확인 ----------------
  async connect() {
    this.setState('connecting', { errorText: '' });
    try {
      const res = await fetch(CONFIG.BASE_URL + '/v1/models', {
        method: 'GET',
        headers: authHeaders(),
        timeout: 10000,
      });
      if (!res.ok) {
        let detail = '';
        try { detail = (await res.text()).replace(/\s+/g, ' ').slice(0, 160); } catch (_) {}
        throw new Error('HTTP ' + res.status + (detail ? ' | ' + detail : ''));
      }
      const json = await res.json();
      if (!this.model) {
        const first = json && json.data && json.data[0];
        this.model = first && first.id ? first.id : 'hermes-agent';
      }
      this.setState('ready');
      return true;
    } catch (err) {
      this.setState('offline', { errorText: '재규어에 연결할 수 없음: ' + (err && err.message ? err.message : err) });
      this.runDiagnostics();
      return false;
    }
  },

  // ---------------- 연결 진단 ----------------
  async runDiagnostics() {
    const B = CONFIG.BASE_URL;
    const tests = [
      { name: 'fetch health', via: 'fetch', url: B + '/health', auth: false },
      { name: 'fetch models', via: 'fetch', url: B + '/v1/models', auth: true },
      { name: 'wx health', via: 'wx', url: B + '/health', auth: false },
      { name: 'wx models', via: 'wx', url: B + '/v1/models', auth: true },
      { name: 'wx syno443', via: 'wx', url: B + '/', auth: false },
      { name: 'wx rokid', via: 'wx', url: 'https://js.rokid.com/', auth: false },
    ];
    const short = (v) => String(v == null ? '' : (typeof v === 'string' ? v : JSON.stringify(v))).replace(/\s+/g, ' ').slice(0, 60);
    const lines = [];
    for (let i = 0; i < tests.length; i++) {
      const t = tests[i];
      let line = t.name + ': ';
      try {
        if (t.via === 'fetch') {
          const res = await fetch(t.url, { method: 'GET', headers: t.auth ? authHeaders() : {}, timeout: 8000 });
          let body = '';
          try { body = await res.text(); } catch (_) {}
          line += res.status + ' ' + short(body);
        } else {
          const r = await wxGet(t.url, t.auth ? authHeaders() : {});
          line += r.status + ' ' + short(r.body);
        }
      } catch (err) {
        line += 'ERR ' + short(err && err.message ? err.message : err);
      }
      lines.push({ id: 'd' + i, text: line });
      this.setData({ diag: lines.slice() });
    }
    console.log('[JaguarBot] diag', JSON.stringify(lines));
  },

  // ---------------- 음성 인식 ----------------
  ensureRecognition() {
    if (this.recognition) return this.recognition;
    if (typeof SpeechRecognition === 'undefined') {
      throw new Error('이 기기에서 SpeechRecognition 을 사용할 수 없음');
    }
    const rec = new SpeechRecognition();
    rec.lang = this.asrLang;
    rec.continuous = false;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    rec.onresult = (event) => {
      let text = '';
      let isFinal = false;
      const results = event && event.results ? event.results : [];
      for (let i = 0; i < results.length; i++) {
        const r = results[i];
        if (r && r[0] && r[0].transcript) text += r[0].transcript;
        if (r && r.isFinal) isFinal = true;
      }
      this.finalText = text;
      this.setData({ transcript: text });
      if (isFinal) this.gotFinal = true;
    };

    rec.onerror = (event) => {
      const code = event && event.error ? event.error : 'error';
      if (code === 'language-not-supported' && this.asrLang) {
        // 한국어 미지원이면 런타임 기본 언어로 재시도
        this.asrLang = '';
        this.recognition = null;
        this.setData({ errorText: 'ko-KR 미지원 → 기본 언어로 재시도' });
        return;
      }
      if (code === 'no-speech' || code === 'aborted') {
        this.recogFailed = 'silent';
        return;
      }
      this.recogFailed = code + (event && event.message ? ': ' + event.message : '');
    };

    rec.onend = () => {
      const text = (this.finalText || '').trim();
      const failed = this.recogFailed;
      this.finalText = '';
      this.gotFinal = false;
      this.recogFailed = null;

      if (this.data.state !== 'listening') return;

      if (text) {
        this.ask(text);
      } else if (!this.recognition && this.asrLang === '') {
        // 언어 폴백 직후 → 다시 듣기 시도 (거부되면 탭 대기)
        this.startListening(true);
      } else if (failed && failed !== 'silent') {
        this.setState('error', { errorText: '음성 인식 오류: ' + failed });
      } else {
        this.setState('ready', { errorText: '' });
      }
    };

    this.recognition = rec;
    return rec;
  },

  startListening(isAuto) {
    if (this.busy) return;
    try {
      const rec = this.ensureRecognition();
      this.finalText = '';
      this.gotFinal = false;
      this.recogFailed = null;
      this.setState('listening', { transcript: '', errorText: '' });
      rec.start();
    } catch (err) {
      // 자동 시작은 사용자 조작이 아니라서 거부될 수 있음 → 탭 대기
      this.recognition = null;
      if (isAuto) {
        this.setState('ready');
      } else {
        this.setState('error', { errorText: '마이크 시작 실패: ' + (err && err.message ? err.message : err) });
      }
    }
  },

  stopListening() {
    try {
      if (this.recognition) this.recognition.stop();
    } catch (_) {}
  },

  abortRecognition() {
    try {
      if (this.recognition) this.recognition.abort();
    } catch (_) {}
    this.recognition = null;
  },

  // ---------------- 재규어 호출 ----------------
  cancelRequest() {
    try {
      if (this.controller) this.controller.abort();
    } catch (_) {}
    this.controller = null;
    this.busy = false;
  },

  async ask(text) {
    if (this.busy) return;
    this.busy = true;
    const startedAt = Date.now();

    this.history.push({ role: 'user', content: text });
    if (this.history.length > CONFIG.HISTORY_LIMIT) {
      this.history = this.history.slice(-CONFIG.HISTORY_LIMIT);
    }

    this.setState('thinking', { transcript: text, answer: '', answerLines: [], errorText: '', elapsed: '' });

    const body = {
      model: this.model || 'hermes-agent',
      stream: true,
      messages: [{ role: 'system', content: SYSTEM_PROMPT }].concat(this.history),
    };

    const opts = {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json', Accept: 'text/event-stream' }),
      body: JSON.stringify(body),
      timeout: CONFIG.REQUEST_TIMEOUT_MS,
    };
    if (typeof AbortController !== 'undefined') {
      this.controller = new AbortController();
      opts.signal = this.controller.signal;
    }

    let answer = '';
    let lastPaint = 0;
    const paint = (force) => {
      const now = Date.now();
      if (!force && now - lastPaint < 150) return;
      lastPaint = now;
      const shown = cleanText(answer);
      this.setData({
        answer: shown,
        answerLines: shown.split('\n').map((t, i) => ({ id: 'a' + i, t: t || ' ' })),
        elapsed: Math.round((now - startedAt) / 1000) + 's',
      });
    };

    // SSE 한 줄 처리
    const handleLine = (line) => {
      const t = line.trim();
      if (!t.startsWith('data:')) return;
      const payload = t.slice(5).trim();
      if (!payload || payload === '[DONE]') return;
      try {
        const json = JSON.parse(payload);
        const choice = json.choices && json.choices[0];
        const delta = choice && (choice.delta || choice.message);
        if (delta && typeof delta.content === 'string' && delta.content) {
          if (this.data.state !== 'answering') this.setState('answering');
          answer += delta.content;
          paint(false);
        }
      } catch (_) {}
    };

    try {
      const res = await fetch(CONFIG.BASE_URL + '/v1/chat/completions', opts);
      if (!res.ok) {
        let detail = '';
        try { detail = (await res.text()).slice(0, 200); } catch (_) {}
        throw new Error('HTTP ' + res.status + (detail ? ' ' + detail : ''));
      }

      const ctype = (res.headers && res.headers.get && res.headers.get('content-type')) || '';

      if (res.body && res.body.getReader && ctype.indexOf('application/json') === -1) {
        // 스트리밍
        const reader = res.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        while (true) {
          const r = await reader.read();
          if (r.done) break;
          buffer += decoder.decode(r.value, { stream: true });
          let idx = buffer.indexOf('\n');
          while (idx !== -1) {
            handleLine(buffer.slice(0, idx));
            buffer = buffer.slice(idx + 1);
            idx = buffer.indexOf('\n');
          }
        }
        buffer += decoder.decode();
        if (buffer) handleLine(buffer);
      } else {
        // 비스트리밍 응답 폴백
        const raw = await res.text();
        if (raw.trim().startsWith('{')) {
          const json = JSON.parse(raw);
          const msg = json.choices && json.choices[0] && json.choices[0].message;
          answer = msg && msg.content ? msg.content : '';
        } else {
          raw.split('\n').forEach(handleLine);
        }
      }

      if (!answer.trim()) answer = '(빈 응답)';
      this.history.push({ role: 'assistant', content: answer });
      paint(true);
      this.setState('done');
      speakText(cleanText(answer));
    } catch (err) {
      const aborted = err && (err.name === 'AbortError' || /abort/i.test(String(err.message || err)));
      // 실패한 질문은 맥락에서 제거
      if (this.history.length && this.history[this.history.length - 1].role === 'user') {
        this.history.pop();
      }
      if (aborted) {
        this.setState('ready', { errorText: '요청 취소됨' });
      } else {
        this.setState('error', { errorText: String(err && err.message ? err.message : err) });
      }
    } finally {
      this.controller = null;
      this.busy = false;
    }
  },
};
</script>

<page>
  <view class="root" bindtap="handlePrimaryAction">
    <view class="status-bar">
      <text class="status">{{statusText}}</text>
      <text class="elapsed" ink:if="{{elapsed}}">{{elapsed}}</text>
    </view>

    <view class="question" ink:if="{{transcript}}">
      <text class="question-text">› {{transcript}}</text>
    </view>

    <view class="answer" ink:if="{{answer}}">
      <text class="answer-text" ink:for="{{answerLines}}" ink:key="id">{{item.t}}</text>
    </view>

    <view class="placeholder" ink:if="{{!answer && !transcript && state === 'ready'}}">
      <text class="placeholder-text">재규어 연결됨</text>
      <text class="hint-text">템플을 탭하고 말하세요</text>
    </view>

    <view class="error" ink:if="{{errorText}}">
      <text class="error-text">{{errorText}}</text>
    </view>

    <view class="diag" ink:if="{{diag.length}}">
      <text class="diag-text" ink:for="{{diag}}" ink:key="id">{{item.text}}</text>
    </view>
  </view>
</page>

<style>
.root {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px 20px;
  min-height: 100%;
  box-sizing: border-box;
  background-color: #000000;
}

.status-bar {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(64, 255, 94, 0.4);
}

.status {
  font-size: 13px;
  font-weight: 600;
  color: rgba(64, 255, 94, 0.6);
}

.elapsed {
  font-size: 13px;
  color: rgba(64, 255, 94, 0.6);
}

.question-text {
  font-size: 15px;
  color: rgba(64, 255, 94, 0.6);
}

.answer {
  display: flex;
  flex-direction: column;
}

.answer-text {
  font-size: 18px;
  line-height: 1.45;
  color: #40ff5e;
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding-top: 24px;
}

.placeholder-text {
  font-size: 20px;
  font-weight: 700;
  color: #40ff5e;
}

.hint-text {
  font-size: 13px;
  color: rgba(64, 255, 94, 0.6);
}

.error {
  padding: 8px 10px;
  border: 1px solid rgba(64, 255, 94, 0.4);
  border-radius: 8px;
  background-color: rgba(64, 255, 94, 0.08);
}

.error-text {
  font-size: 13px;
  color: rgba(64, 255, 94, 0.6);
}
.diag {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.diag-text {
  font-size: 12px;
  color: rgba(64, 255, 94, 0.6);
}
</style>