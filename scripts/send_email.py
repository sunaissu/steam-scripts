import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    masked_local = local[:2] + "***" if len(local) > 2 else "***"
    domain_parts = domain.split(".")
    masked_domain = domain_parts[0][:1] + "***" + "." + domain_parts[-1] if domain_parts else "***"
    return f"{masked_local}@{masked_domain}"


def send(subject: str, html_body: str, to_override: str = None) -> bool:
    sender   = os.getenv("EMAIL_SENDER", "")
    password = os.getenv("EMAIL_PASSWORD", "")
    to       = to_override or os.getenv("EMAIL_TO", "")

    if not all([sender, password, to]):
        print("Email config missing. Set EMAIL_SENDER, EMAIL_PASSWORD, and EMAIL_TO in .env")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to, msg.as_string())
        print(f"Email sent to {mask_email(to)}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("Email auth failed — check EMAIL_SENDER and EMAIL_PASSWORD in .env")
        print("Generate an App Password at: https://myaccount.google.com/apppasswords")
    except Exception as e:
        print(f"Failed to send email: {e}")

    return False


def build_games_html(games: list[dict]) -> str:
    rows = ""
    for game in games:
        store_url = f"https://store.steampowered.com/app/{game['appid']}"
        logo      = game.get("logo", "")
        name      = game.get("name", f"App {game['appid']}")

        img_tag = f'<img src="{logo}" style="width:120px;border-radius:6px;" />' if logo else ""

        rows += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #2a2a4a;">{img_tag}</td>
          <td style="padding:12px;border-bottom:1px solid #2a2a4a;vertical-align:middle;">
            <strong style="font-size:16px;">{name}</strong><br/>
            <a href="{store_url}" style="color:#66c0f4;">View on Steam Store →</a>
          </td>
        </tr>
        """

    return f"""
    <html>
    <body style="background:#1b2838;color:#c6d4df;font-family:Arial,sans-serif;padding:24px;">
      <div style="max-width:600px;margin:auto;background:#2a475e;border-radius:12px;padding:24px;">
        <h1 style="color:#66c0f4;margin-top:0;">🎮 New Free Steam Games!</h1>
        <p>The following games are currently <strong>100% off</strong> on Steam and not yet in your library:</p>
        <table style="width:100%;border-collapse:collapse;">
          {rows}
        </table>
        <p style="font-size:12px;color:#8f98a0;margin-top:24px;">
          Sent by your steam-scripts bot. Add them before the offer ends!
        </p>
      </div>
    </body>
    </html>
    """
