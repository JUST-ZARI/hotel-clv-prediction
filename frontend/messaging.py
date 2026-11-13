"""
Real email (Gmail SMTP) and SMS (Africa's Talking) for the Marketing Team's guest actions.

Configured in .streamlit/secrets.toml under [messaging] (see secrets.example.toml):

    gmail_address        the Gmail account that sends
    gmail_app_password   a Google *app password* (not the account password)
    africastalking_username / africastalking_api_key   ("sandbox" = free test mode)
    africastalking_sender_id   optional approved sender name (default: the shared one)
    daily_limit          sends per staff member per 24 hours (default 20)
    test_recipient       optional: bulk emails go to this address instead of the guests (test mode)
    test_phone           optional: bulk SMS go to this number instead of the guests (test mode)

Guests in the historical data have demo addresses (@example.com) and no
marketing consent, so the app only sends to a *demo recipient* typed in by the
user (e.g. a lecturer at a demonstration).
"""

from __future__ import annotations

import html
import re
import smtplib
import ssl
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid

import httpx
import streamlit as st

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
DEMO_DOMAINS = ("example.com", "example.org", "example.net", "example.invalid")
DEFAULT_DAILY_LIMIT = 20
TIMEOUT = 20


class SendError(Exception):
    """User-facing reason a message was not sent. `blocked`: the network refused this number
    for bulk SMS (opt-out / Do-Not-Disturb) — a normal text from a phone still gets through."""

    def __init__(self, message: str, blocked: bool = False):
        super().__init__(message)
        self.blocked = blocked


@dataclass(frozen=True)
class SendResult:
    recipient_masked: str
    provider_id: str


def _cfg() -> dict:
    return dict(st.secrets.get("messaging", {}))


def _filled(*keys: str) -> bool:
    cfg = _cfg()
    return all(str(cfg.get(k) or "").strip() and "YOUR-" not in str(cfg.get(k)) for k in keys)


def email_ready() -> bool:
    return _filled("gmail_address", "gmail_app_password")


def sms_provider() -> str:
    """'africastalking' (default) or 'infobip', chosen with sms_provider in [messaging]."""
    return str(_cfg().get("sms_provider") or "africastalking").strip().lower()


def sms_ready() -> bool:
    if sms_provider() == "infobip":
        return _filled("infobip_base_url", "infobip_api_key")
    return _filled("africastalking_username", "africastalking_api_key")


def daily_limit() -> int:
    return int(_cfg().get("daily_limit") or DEFAULT_DAILY_LIMIT)


def test_recipient() -> str | None:
    """Test mode: bulk emails go to this address instead of the guests (test_recipient under [messaging])."""
    raw = str(_cfg().get("test_recipient") or "").strip()
    if not raw or "YOUR-" in raw:
        return None
    try:
        return normalize_email(raw)
    except SendError:
        return None


def test_phone() -> str | None:
    """Test mode for bulk SMS: every SMS goes to this number instead of the guests (test_phone under [messaging])."""
    raw = str(_cfg().get("test_phone") or "").strip()
    if not raw or "YOUR-" in raw:
        return None
    try:
        return normalize_phone(raw)
    except SendError:
        return None


# ---------------------------------------------------------------------------
# Recipients
# ---------------------------------------------------------------------------

def normalize_email(raw: str) -> str:
    email = (raw or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise SendError("Enter a valid email address, e.g. name@strathmore.edu.")
    if email.split("@")[1] in DEMO_DOMAINS:
        raise SendError("That is a demo address that cannot receive mail.")
    return email


def normalize_phone(raw: str) -> str:
    """Kenyan numbers in any common form (0712…, 712…, 254712…, +254712…) or any +E.164 number."""
    digits = re.sub(r"[^\d+]", "", raw or "")
    if digits.startswith("+"):
        number = digits
    elif digits.startswith("254"):
        number = "+" + digits
    elif digits.startswith("0") and len(digits) == 10:
        number = "+254" + digits[1:]
    elif len(digits) == 9 and digits[0] in "17":
        number = "+254" + digits
    else:
        number = ""
    if not re.fullmatch(r"\+[1-9]\d{7,14}", number):
        raise SendError("Enter a valid phone number, e.g. 0712 345 678 or +254712345678.")
    return number


def mask(recipient: str) -> str:
    """What is stored in the action log: enough to recognise, not enough to reuse."""
    if "@" in recipient:
        name, domain = recipient.split("@", 1)
        return f"{name[:1]}***@{domain}"
    return f"{recipient[:4]}*****{recipient[-3:]}"


# ---------------------------------------------------------------------------
# Senders
# ---------------------------------------------------------------------------

def _email(sender: str, to: str, subject: str, body: str, hotel_name: str) -> EmailMessage:
    """The email as plain text plus a simple branded HTML version."""
    msg = EmailMessage()
    msg["From"] = f"{hotel_name} <{sender}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[1])
    msg.set_content(body)
    paragraphs = "".join(f"<p style='margin:0 0 14px'>{html.escape(p).replace(chr(10), '<br>')}</p>"
                         for p in body.split("\n\n"))
    msg.add_alternative(f"""\
<div style="font-family:'Times New Roman',Times,serif;max-width:560px;margin:auto;color:#14213D">
  <div style="background:#0F3D3E;color:#B8F28A;padding:18px 22px;border-radius:10px 10px 0 0;font-size:20px">
    <b>{html.escape(hotel_name)}</b></div>
  <div style="border:1px solid #CCD5D1;border-top:none;padding:22px;border-radius:0 0 10px 10px;font-size:16px">
    {paragraphs}</div>
  <p style="font-size:12px;color:#6b7280;text-align:center">Sent from the Hotel CLV decision support system
  (student project demonstration).</p>
</div>""", subtype="html")
    return msg


@contextmanager
def email_batch(hotel_name: str) -> Iterator[Callable[[str, str, str], SendResult]]:
    """One Gmail connection for one or many emails. Yields send(to, subject, body) -> SendResult.

    Raises SendError if email is not set up or Gmail refuses the login; each send raises
    SendError for its own email only, so a bulk send can carry on with the next guest.
    """
    if not email_ready():
        raise SendError("Email is not set up. Add gmail_address and gmail_app_password under [messaging] in secrets.")
    cfg = _cfg()
    sender = str(cfg["gmail_address"]).strip()
    try:
        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=TIMEOUT)
        smtp.login(sender, str(cfg["gmail_app_password"]).replace(" ", ""))
    except smtplib.SMTPAuthenticationError as e:
        raise SendError("Gmail rejected the login. Check gmail_address and the 16-letter app password.") from e
    except (smtplib.SMTPException, OSError) as e:
        raise SendError("The email could not be sent. Check the internet connection and try again.") from e

    def send(to: str, subject: str, body: str) -> SendResult:
        to = normalize_email(to)
        msg = _email(sender, to, subject, body, hotel_name)
        try:
            smtp.send_message(msg)
        except (smtplib.SMTPException, OSError) as e:
            raise SendError("The email could not be sent. Check the internet connection and try again.") from e
        return SendResult(mask(to), str(msg["Message-ID"]))

    try:
        yield send
    finally:
        try:
            smtp.quit()
        except (smtplib.SMTPException, OSError):
            pass


def send_email(to: str, subject: str, body: str, hotel_name: str) -> SendResult:
    normalize_email(to)     # a bad address is reported before connecting to Gmail
    with email_batch(hotel_name) as send:
        return send(to, subject, body)


# ---------------------------------------------------------------------------
# SMS through Africa's Talking (Kenyan provider: any Kenyan number, KSh per SMS)
# ---------------------------------------------------------------------------
# Username "sandbox" uses the free sandbox: messages appear only in the Africa's
# Talking simulator, not on real phones. A live app (topped up via M-Pesa) texts
# real numbers.

BLOCKED_STATUSES = (406, 409)   # UserInBlacklist, DoNotDisturbRejection
AT_STATUS = {   # per-recipient status codes from the messaging API
    403: "Africa's Talking says this is not a valid phone number.",
    404: "This number type cannot receive SMS.",
    405: "Your Africa's Talking balance is too low. Top up via M-Pesa in the dashboard (Billing → Top up).",
    406: "The network blocks bulk SMS from Africa's Talking's shared sender to this number.",
    407: "Africa's Talking could not route a message to this number.",
    409: "This line blocks promotional bulk SMS (the network's Do-Not-Disturb setting).",
    402: "The sender ID is not approved. Remove africastalking_sender_id from secrets to use the default.",
    401: "The message was held for review by the network. Try again with a shorter, plainer message.",
}


def _at_base() -> str:
    sandbox = str(_cfg().get("africastalking_username", "")).strip() == "sandbox"
    return "https://api.sandbox.africastalking.com/version1" if sandbox else "https://api.africastalking.com/version1"


def _at_headers() -> dict:
    return {"apiKey": str(_cfg()["africastalking_api_key"]).strip(), "Accept": "application/json"}


def is_sandbox() -> bool:
    return sms_provider() == "africastalking" and str(_cfg().get("africastalking_username", "")).strip() == "sandbox"


def send_sms(to: str, body: str) -> SendResult:
    """Send through the configured provider (Africa's Talking or Infobip)."""
    return _send_infobip(to, body) if sms_provider() == "infobip" else _send_africastalking(to, body)


def _send_africastalking(to: str, body: str) -> SendResult:
    if not sms_ready():
        raise SendError("SMS is not set up. Add africastalking_username and africastalking_api_key under "
                        "[messaging] in secrets.")
    cfg = _cfg()
    to = normalize_phone(to)
    data = {"username": str(cfg["africastalking_username"]).strip(), "to": to, "message": body[:900]}
    sender = str(cfg.get("africastalking_sender_id") or "").strip()
    if sender and "YOUR-" not in sender:
        data["from"] = sender
    try:
        r = httpx.post(f"{_at_base()}/messaging", data=data, headers=_at_headers(), timeout=TIMEOUT)
    except httpx.HTTPError as e:
        raise SendError("Africa's Talking could not be reached. Check the internet connection and try again.") from e
    if r.status_code == 401:
        raise SendError("Africa's Talking rejected the login. Check africastalking_username and the API key "
                        "(the key must belong to that app; generate a new one if unsure).")
    try:
        result = r.json()["SMSMessageData"]
        recipient = (result.get("Recipients") or [{}])[0]
    except (ValueError, KeyError) as e:
        raise SendError(f"Africa's Talking refused the message ({r.status_code}): {r.text[:120]}") from e
    status = recipient.get("statusCode")
    if status not in (100, 101, 102):
        raise SendError(AT_STATUS.get(status, f"Africa's Talking refused the message: {result.get('Message', r.text[:120])}"),
                        blocked=status in BLOCKED_STATUSES)
    return SendResult(mask(to), str(recipient.get("messageId", "")))


# ---------------------------------------------------------------------------
# SMS through Infobip (alternative provider: sms_provider = "infobip")
# ---------------------------------------------------------------------------
# Free trial: a few test messages, only to numbers verified in the Infobip portal,
# sent from Infobip's test sender. Live use needs a paid account.

def _send_infobip(to: str, body: str) -> SendResult:
    if not sms_ready():
        raise SendError("SMS is not set up. Add infobip_base_url and infobip_api_key under [messaging] in secrets.")
    cfg = _cfg()
    to = normalize_phone(to)
    base = str(cfg["infobip_base_url"]).strip().removeprefix("https://").rstrip("/")
    message = {"destinations": [{"to": to.lstrip("+")}], "text": body[:900]}
    sender = str(cfg.get("infobip_sender") or "").strip()
    if sender and "YOUR-" not in sender:
        message["from"] = sender
    try:
        r = httpx.post(f"https://{base}/sms/2/text/advanced", json={"messages": [message]},
                       headers={"Authorization": f"App {str(cfg['infobip_api_key']).strip()}",
                                "Accept": "application/json"}, timeout=TIMEOUT)
    except httpx.HTTPError as e:
        raise SendError("Infobip could not be reached. Check the internet connection and try again.") from e
    if r.status_code == 401:
        raise SendError("Infobip rejected the API key. Check infobip_api_key and infobip_base_url.")
    try:
        msg = r.json()["messages"][0]
        status = msg.get("status", {})
    except (ValueError, KeyError, IndexError) as e:
        raise SendError(f"Infobip refused the message ({r.status_code}): {r.text[:120]}") from e
    if status.get("groupName") in ("REJECTED", "UNDELIVERABLE", "EXPIRED"):
        raise SendError(f"Infobip did not accept the message: {status.get('description') or status.get('name')}. "
                        "On a free trial, the number must be verified in the Infobip portal first.",
                        blocked=True)
    return SendResult(mask(to), str(msg.get("messageId", "")))
