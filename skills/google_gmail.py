"""
Gmail 스킬 - IMAP/SMTP + 앱 비밀번호
Google API OAuth 불필요
"""
import imaplib
import smtplib
import email
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header

SKILL_DEFINITION = {
    "name": "check_email",
    "description": "Gmail 이메일 확인(읽기/검색) 또는 전송",
    "enabled": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "send", "search"],
                "default": "read",
            },
            "count":   {"type": "integer", "default": 5},
            "to":      {"type": "string"},
            "subject": {"type": "string"},
            "body":    {"type": "string"},
            "query":   {"type": "string"},
        },
        "required": ["action"],
    },
}

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _creds():
    addr = os.environ.get("GMAIL_ADDRESS", "")
    pw   = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    if not addr or not pw:
        raise RuntimeError(
            "GMAIL_ADDRESS / GMAIL_APP_PASSWORD 환경변수가 없습니다. "
            "config/.env 파일을 확인하세요."
        )
    return addr, pw


def _decode_str(s: str) -> str:
    parts = decode_header(s)
    result = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc or "utf-8", errors="ignore")
        else:
            result += part
    return result


def execute(params: dict) -> str:
    action = params.get("action", "read")
    try:
        if action == "read":
            return _read(params.get("count", 5))
        elif action == "send":
            return _send(params)
        elif action == "search":
            return _search(params.get("query", ""), params.get("count", 5))
        return f"알 수 없는 동작: {action}"
    except RuntimeError as e:
        return str(e)
    except Exception as e:
        return f"Gmail 오류: {e}"


def _read(count: int) -> str:
    addr, pw = _creds()
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(addr, pw)
    mail.select("INBOX")

    _, data = mail.search(None, "UNSEEN")
    ids = data[0].split()
    if not ids:
        mail.logout()
        return "읽지 않은 이메일이 없습니다."

    summaries = []
    for uid in ids[-count:][::-1]:
        _, msg_data = mail.fetch(uid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        sender  = _decode_str(msg.get("From", "알 수 없음"))
        subject = _decode_str(msg.get("Subject", "(제목 없음)"))
        # 발신자 이름만 추출
        if "<" in sender:
            sender = sender.split("<")[0].strip().strip('"')
        summaries.append(f"{sender}으로부터 '{subject}'")

    mail.logout()
    result = f"읽지 않은 이메일 {len(summaries)}개입니다. "
    result += ". ".join(summaries[:5])
    return result


def _send(params: dict) -> str:
    addr, pw = _creds()
    to      = params.get("to", "")
    subject = params.get("subject", "")
    body    = params.get("body", "")
    if not to or not body:
        return "수신자와 본문을 입력해주세요."

    msg = MIMEMultipart()
    msg["From"]    = addr
    msg["To"]      = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(addr, pw)
        s.sendmail(addr, to, msg.as_string())
    return f"{to}에게 이메일을 전송했습니다."


def _search(query: str, count: int) -> str:
    if not query:
        return "검색어를 입력해주세요."
    addr, pw = _creds()
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(addr, pw)
    mail.select("INBOX")

    _, data = mail.search(None, f'SUBJECT "{query}"')
    ids = data[0].split()
    mail.logout()

    if not ids:
        return f"'{query}' 관련 이메일을 찾지 못했습니다."
    return f"'{query}' 관련 이메일 {len(ids)}개를 찾았습니다."
