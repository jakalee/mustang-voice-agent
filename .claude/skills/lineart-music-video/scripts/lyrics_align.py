#!/usr/bin/env python3
"""노래 파일에서 보컬을 분리하고, 음성인식으로 가사 줄마다 시작/끝 시간을 잰다.

출력 (outdir):
  vocals.wav        분리된 보컬
  asr.json          Whisper 구간 + 단어 타임스탬프
  lyrics_draft.js   HTML에 붙여넣을 LYRICS 배열 초안  [시작, '가사', 끝]
  structure.txt     템포, 곡 구간 경계, 1초 단위 에너지

사용법:
  python3 lyrics_align.py song.mp3 outdir [--model large-v3] [--prompt "가사 일부"]

필요: pip install demucs faster-whisper librosa
네트워크: huggingface.co 와 그 CDN(us.aws.cdn.hf.co 등), dl.fbaipublicfiles.com (모델 다운로드)
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

os.environ.setdefault('HF_HUB_DISABLE_XET', '1')   # xet 전송 서버가 막힌 환경에서도 받도록

ap = argparse.ArgumentParser()
ap.add_argument('song'); ap.add_argument('outdir')
ap.add_argument('--model', default='large-v3'); ap.add_argument('--lang', default='ko')
ap.add_argument('--prompt', default=None, help='가사 일부를 주면 인식이 좋아진다')
a = ap.parse_args()
out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)

import librosa, numpy as np

# 1) 보컬 분리
voc = out / 'vocals.wav'
if not voc.exists():
    subprocess.run([sys.executable, '-m', 'demucs', '--two-stems=vocals', '-n', 'htdemucs', '-o', str(out / 'sep'), a.song], check=True)
    stem = Path(a.song).stem
    (out / 'sep' / 'htdemucs' / stem / 'vocals.wav').rename(voc)

# 2) 음성인식 (PyAV 버전 충돌을 피하려고 numpy 배열로 넘긴다)
from faster_whisper import WhisperModel
m = WhisperModel(a.model, device='cpu', compute_type='int8', cpu_threads=os.cpu_count() or 4)
audio16, _ = librosa.load(str(voc), sr=16000)
segs, _ = m.transcribe(audio16, language=a.lang, word_timestamps=True, beam_size=5,
                       condition_on_previous_text=False, initial_prompt=a.prompt)
segs = [{'s': s.start, 'e': s.end, 'text': s.text.strip(), 'words': [(w.start, w.end, w.word.strip()) for w in s.words]} for s in segs]
json.dump(segs, open(out / 'asr.json', 'w'), ensure_ascii=False, indent=1)

# 3) 시작 시간 보정: Whisper는 앞 줄 끝에 다음 줄 시작을 붙이는 버릇이 있다.
#    직전 0.15초가 조용하다가 소리가 커지는 지점을 찾아 그 시각으로 당긴다.
y, sr = librosa.load(str(voc), sr=16000)
hop = 160; rms = librosa.feature.rms(y=y, hop_length=hop, frame_length=1024)[0]; tt = np.arange(len(rms)) * hop / sr
thr = np.percentile(rms, 60) * 0.35
def refine(s, prev_end):
    if abs(s - prev_end) > 0.05: return s          # 붙어 있지 않으면 그대로
    i0, i1 = np.searchsorted(tt, s - 0.3), np.searchsorted(tt, s + 3.0)
    for i in range(i0 + 15, i1):
        if rms[i] > thr and rms[i - 15:i].max() < thr: return float(tt[i])
    return s

lines, prev = [], -1
for sg in segs:
    st = refine(sg['s'], prev); prev = sg['e']
    lines.append([round(max(0.0, st - 0.15), 2), sg['text'], round(sg['e'] - 0.05, 2)])
with open(out / 'lyrics_draft.js', 'w') as f:
    f.write('// 음성인식 초안 — 뭉개진 소절은 반드시 사람이 확인해서 고칠 것. 한 구간에 두 줄이 붙어 있으면 asr.json 단어 시간으로 나눈다.\n')
    f.write('const LYRICS = [\n' + ''.join(f"  [{s}, {json.dumps(x, ensure_ascii=False)}, {e}],\n" for s, x, e in lines) + '];\n')

# 4) 곡 구조
yf, srf = librosa.load(a.song, sr=22050)
tempo, _ = librosa.beat.beat_track(y=yf, sr=srf)
H_, _ = librosa.effects.hpss(yf)
C_ = librosa.feature.chroma_cqt(y=H_, sr=srf, hop_length=512)
M_ = librosa.feature.mfcc(y=yf, sr=srf, hop_length=512, n_mfcc=13)
F_ = np.vstack([librosa.util.normalize(C_, axis=0), M_ / (np.abs(M_).max(1, keepdims=True) + 1e-9)])
F_ = librosa.util.sync(F_, np.arange(0, F_.shape[1], 43))
bnd = librosa.segment.agglomerative(F_, 10) * 43 * 512 / srf
r = librosa.feature.rms(y=yf, hop_length=2205)[0]
with open(out / 'structure.txt', 'w') as f:
    f.write(f'tempo {float(np.atleast_1d(tempo)[0]):.1f} bpm (두 배로 잡혔을 수 있음)\n')
    f.write('section boundaries (s): ' + ', '.join(f'{b:.1f}' for b in bnd) + '\n\n')
    for i in range(0, len(r), 10): f.write(f'{i/10:5.0f} ' + '#' * int(r[i:i+10].mean() * 120) + '\n')

print(open(out / 'lyrics_draft.js').read())
print(open(out / 'structure.txt').read().split('\n\n')[0])
