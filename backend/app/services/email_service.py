import httpx

from app.core import config


def send_password_reset_email(to_email: str, reset_url: str) -> None:
    if not config.RESEND_API_KEY:
        print(f"[dev] Password reset link for {to_email}: {reset_url}")
        return

    minutes = config.PASSWORD_RESET_TTL_SECONDS // 60
    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {config.RESEND_API_KEY}"},
        json={
            "from": config.MAIL_FROM,
            "to": [to_email],
            "subject": "Reset your Knowvia password",
            "text": (
                "We got a request to reset your Knowvia password.\n\n"
                f"Open this link to choose a new one (valid for {minutes} "
                f"minutes):\n{reset_url}\n\n"
                "If you didn't ask for this, you can ignore this email."
            ),
        },
        timeout=10,
    )
    response.raise_for_status()