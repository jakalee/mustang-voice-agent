#!/usr/bin/env python3
"""capture.mjs stills 로 뽑은 PNG들을 8장씩 가로로 이어 붙인 확인용 시트로 만든다.

사용법: python3 contact_sheet.py <stillsDir>   ->  <stillsDir>/sheet0.png, sheet1.png ...
"""
import glob, subprocess, sys

d = sys.argv[1]
fs = sorted(glob.glob(d + '/t*.png'))
font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
for k in range(0, len(fs), 8):
    grp = fs[k:k + 8]; ins = []
    for f in grp: ins += ['-i', f]
    n = len(grp)
    filt = ''.join(f'[{i}:v]scale=300:-2,pad=300:540:0:0:black,drawtext=fontfile={font}:text={grp[i].split("/")[-1][1:-4]}:x=6:y=6:fontsize=20:fontcolor=red[v{i}];' for i in range(n))
    lay = '|'.join(f'{i * 300}_0' for i in range(n))
    filt += ''.join(f'[v{i}]' for i in range(n)) + f'xstack=inputs={n}:layout={lay}:fill=black'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', filt, f'{d}/sheet{k // 8}.png'], check=True)
