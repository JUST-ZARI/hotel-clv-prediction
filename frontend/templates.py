"""
Guest message templates (email subject, email and SMS text), written as the hotel.

Used by Guest Lookup (one guest, editable before sending) and by the bulk send on the
Action Board (many guests at once).
"""

from __future__ import annotations

from utils import HOTEL_NAME

TEMPLATES = ["Win-back offer", "Suite upgrade", "Loyalty thank-you", "Seasonal news", "Follow-up"]


def template_for(action: str) -> str:
    """The message template that matches a recommended action."""
    a = action.lower()
    if "upsell" in a:
        return "Suite upgrade"
    if any(k in a for k in ("loyalty", "concierge")):
        return "Loyalty thank-you"
    if "cost-efficient" in a:
        return "Seasonal news"
    return "Win-back offer"     # win-back, retention and re-engagement actions


def messages(template: str, name: str = "") -> tuple[str, dict[str, str]]:
    """Email subject plus Email and SMS text for a template, addressed to the guest by name if given."""
    name = " ".join(name.split())
    if template == "Suite upgrade":
        subject = f"An upgrade for your next stay at {HOTEL_NAME}"
        lead = ("As one of our valued guests, we would like to make your next stay even more special. "
                "On your next booking we are pleased to offer you an upgrade to one of our suites, "
                "with late check-out and breakfast for two included, subject to availability.")
        sms = (f"{HOTEL_NAME}: As a valued guest, enjoy a suite upgrade with breakfast for two and late "
               f"check-out on your next stay. Reply to this message to reserve. T&Cs apply.")
    elif template == "Loyalty thank-you":
        subject = f"Thank you for staying with {HOTEL_NAME}"
        lead = ("Thank you for choosing us time and again. As a token of our appreciation, you are invited "
                "to enjoy exclusive member privileges on your next visit, including a complimentary welcome "
                "drink, priority check-in and a dedicated guest relations contact who will arrange every "
                "detail of your stay.")
        sms = (f"{HOTEL_NAME}: Thank you for staying with us. Enjoy priority check-in and a complimentary "
               f"welcome drink on your next visit. Reply to this message to book.")
    elif template == "Seasonal news":
        subject = f"What's new at {HOTEL_NAME}"
        lead = ("We have some exciting news to share: our restaurant has a new seasonal menu, and our "
                "weekend packages are now available at special rates. We would love to welcome you back.")
        sms = (f"{HOTEL_NAME}: Our new seasonal menu and weekend packages are here. "
               f"Reply to this message to book your stay.")
    elif template == "Follow-up":
        subject = f"A reminder from {HOTEL_NAME}"
        lead = ("We recently wrote to you with an offer for your next stay, and we wanted to let you know "
                "that it is still available. If you have any questions, our team will be happy to help.")
        sms = (f"{HOTEL_NAME}: A quick reminder that your offer for your next stay is still available. "
               f"Reply to this message to book. T&Cs apply.")
    else:   # Win-back offer
        subject = f"We miss you at {HOTEL_NAME}"
        lead = ("It has been a while since your last visit, and we would love to welcome you back. "
                "As a valued guest, you are invited to enjoy a special returning-guest rate on your next "
                "stay, together with a complimentary room upgrade, subject to availability.")
        sms = (f"{HOTEL_NAME}: We miss you! Enjoy a special returning-guest rate and a complimentary room "
               f"upgrade on your next stay. Reply to this message to book. T&Cs apply.")
    if name:   # "Hotel: We miss you!" → "Hotel: Dear Jane, we miss you!"
        body = sms.removeprefix(f"{HOTEL_NAME}: ")
        sms = f"{HOTEL_NAME}: Dear {name}, {body[:1].lower()}{body[1:]}"
    email = (f"Dear {name or 'Valued Guest'},\n\n"
             f"Warm greetings from {HOTEL_NAME}.\n\n"
             f"{lead}\n\n"
             f"To reserve, simply reply to this email and our reservations team will be glad to assist you.\n\n"
             f"We look forward to welcoming you back.\n\n"
             f"Warm regards,\n"
             f"Guest Relations Team\n"
             f"{HOTEL_NAME}, Nairobi")
    return subject, {"Email": email, "SMS": sms}
