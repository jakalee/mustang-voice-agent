"""
암호화된 자격증명 관리자
모든 API 키, 토큰, 비밀번호를 Fernet 대칭 암호화로 하나의 파일에 저장
"""
import os
import json
import base64
import getpass
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

CRED_FILE = Path(__file__).parent.parent / "config" / "credentials.enc"
SALT_FILE = Path(__file__).parent.parent / "config" / ".salt"


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def _get_fernet(password: Optional[str] = None) -> Fernet:
    SALT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if SALT_FILE.exists():
        salt = SALT_FILE.read_bytes()
    else:
        salt = os.urandom(16)
        SALT_FILE.write_bytes(salt)

    if password is None:
        env_pw = os.environ.get("MUSTANG_PASSWORD")
        if env_pw:
            password = env_pw
        else:
            password = getpass.getpass("🔐 Mustang 마스터 비밀번호: ")

    return Fernet(_derive_key(password, salt))


def load_credentials(password: Optional[str] = None) -> dict:
    if not CRED_FILE.exists():
        return {}
    try:
        f = _get_fernet(password)
        data = f.decrypt(CRED_FILE.read_bytes())
        return json.loads(data)
    except Exception:
        return {}


def save_credentials(creds: dict, password: Optional[str] = None):
    CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
    f = _get_fernet(password)
    CRED_FILE.write_bytes(f.encrypt(json.dumps(creds).encode()))


def get_credential(key: str, password: Optional[str] = None) -> Optional[str]:
    creds = load_credentials(password)
    return creds.get(key)


def set_credential(key: str, value: str, password: Optional[str] = None):
    creds = load_credentials(password)
    creds[key] = value
    save_credentials(creds, password)


def setup_credentials():
    """최초 실행시 자격증명 설정 대화형 인터페이스"""
    print("\n🐎 Mustang AI 자격증명 설정")
    print("=" * 40)
    pw = getpass.getpass("마스터 비밀번호 설정 (기억하세요!): ")
    pw2 = getpass.getpass("비밀번호 확인: ")
    if pw != pw2:
        print("❌ 비밀번호가 일치하지 않습니다.")
        return

    creds = {}
    print("\nAPI 키를 입력하세요 (건너뛰려면 Enter):")

    keys_to_setup = [
        ("TELEGRAM_BOT_TOKEN", "텔레그램 봇 토큰 (선택)"),
        ("TELEGRAM_CHAT_ID", "텔레그램 채팅 ID (선택)"),
        ("GOOGLE_CREDENTIALS_PATH", "Google OAuth 자격증명 파일 경로 (선택)"),
    ]

    for key, label in keys_to_setup:
        val = input(f"  {label}: ").strip()
        if val:
            creds[key] = val

    save_credentials(creds, pw)
    print("\n✅ 자격증명이 암호화되어 저장되었습니다.")
    print(f"   파일: {CRED_FILE}")
    return pw
