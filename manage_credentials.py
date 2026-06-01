#!/usr/bin/env python3
"""
자격증명 관리 CLI
암호화된 자격증명 파일을 관리합니다

사용법:
  python manage_credentials.py set ANTHROPIC_API_KEY sk-ant-...
  python manage_credentials.py get ANTHROPIC_API_KEY
  python manage_credentials.py list
  python manage_credentials.py delete ANTHROPIC_API_KEY
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.credentials import load_credentials, save_credentials, set_credential, get_credential


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "set" and len(sys.argv) >= 4:
        key, value = sys.argv[2], sys.argv[3]
        set_credential(key, value)
        print(f"✅ '{key}' 저장 완료")

    elif cmd == "get" and len(sys.argv) >= 3:
        key = sys.argv[2]
        val = get_credential(key)
        if val:
            print(f"{key} = {val[:8]}{'*' * max(0, len(val) - 8)}")
        else:
            print(f"'{key}'를 찾을 수 없습니다.")

    elif cmd == "list":
        creds = load_credentials()
        if not creds:
            print("저장된 자격증명이 없습니다.")
        else:
            print("저장된 자격증명:")
            for k, v in creds.items():
                masked = v[:8] + "*" * max(0, len(str(v)) - 8)
                print(f"  {k} = {masked}")

    elif cmd == "delete" and len(sys.argv) >= 3:
        key = sys.argv[2]
        creds = load_credentials()
        if key in creds:
            del creds[key]
            save_credentials(creds)
            print(f"✅ '{key}' 삭제 완료")
        else:
            print(f"'{key}'를 찾을 수 없습니다.")

    elif cmd == "setup":
        from core.credentials import setup_credentials
        setup_credentials()

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
