#!/bin/bash
# 🐎 Mustang AI 설치 스크립트

set -e
# 스크립트 위치로 이동
cd "$(dirname "$0")"
echo "🐎 Mustang AI 설치 시작... ($(pwd))"

# Python 버전 확인
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python $PYTHON_VERSION 감지됨"

# 가상환경 생성
if [ ! -d "venv" ]; then
    echo "  가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip -q

# 의존성 설치
echo "  패키지 설치 중 (시간이 걸릴 수 있습니다)..."
pip install -r requirements.txt -q

# Playwright 브라우저 설치
echo "  Playwright 브라우저 설치 중..."
playwright install chromium 2>/dev/null || echo "  ⚠️ Playwright 브라우저 설치 실패 (선택사항)"

# config 디렉토리 생성
mkdir -p config data/history data/screenshots

# .gitignore 생성
cat > config/.gitignore << 'EOF'
*.enc
*.json
.salt
EOF

echo ""
echo "✅ 설치 완료!"
echo ""
echo "다음 단계:"
echo "  1. 가상환경 활성화:"
echo "     source venv/bin/activate"
echo ""
echo "  2. 바로 실행 (Claude Code 인증은 이미 완료):"
echo "     python mustang.py --text   # 텍스트 테스트"
echo "     python mustang.py          # 음성 모드"
echo ""
echo "  3. 텔레그램/Google 연동이 필요하면 (선택):"
echo "     python mustang.py --setup"
