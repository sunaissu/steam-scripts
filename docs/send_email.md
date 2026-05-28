# send_email.py

A reusable email utility used by other scripts in this project. Sends styled HTML emails via Gmail SMTP using credentials stored in `.env`. Uses only Python's built-in `smtplib` — no extra packages needed.

---

## Functions

### `send(subject, html_body) → bool`

Sends an HTML email. Returns `True` on success, `False` on failure.

```python
from scripts import send_email

send_email.send(
    subject="Hello!",
    html_body="<h1>It works</h1>"
)
```

### `build_games_html(games) → str`

Builds a Steam-themed HTML email body from a list of game dicts.

Each game dict must have:
```python
{
    "appid": 12345,
    "name": "Game Name",
    "logo": "https://...header_image..."
}
```

---

## Required `.env` Variables

| Variable | Description |
|---|---|
| `EMAIL_SENDER` | Gmail address you're sending **from** |
| `EMAIL_PASSWORD` | Gmail **App Password** (NOT your login password) |
| `EMAIL_TO` | Address to send notifications **to** (can be the same as sender) |

### Setting up Gmail (step by step)

Gmail blocks normal password logins from scripts. You must use an **App Password**.

**Step 1 — Enable 2-Step Verification**
> [myaccount.google.com/security](https://myaccount.google.com/security) → 2-Step Verification → Turn On

**Step 2 — Create an App Password**
> [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
> - App name: `steam-scripts` (or anything)
> - Click **Create**
> - Google gives you a 16-character password like `abcd efgh ijkl mnop`

**Step 3 — Add to `.env`**
```ini
EMAIL_SENDER=yourgmail@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop    # paste the 16-char password, spaces are fine
EMAIL_TO=youremail@gmail.com       # can be the same address as sender
```

---

## Using a different email provider

The script currently uses Gmail's SMTP server. To switch providers, edit the connection line in `send_email.py`:

| Provider | SMTP Host | Port | Auth |
|---|---|---|---|
| **Gmail** (current) | `smtp.gmail.com` | `465` | App Password |
| **Outlook / Hotmail** | `smtp-mail.outlook.com` | `587` | Normal password + STARTTLS |
| **Yahoo Mail** | `smtp.mail.yahoo.com` | `465` | App Password |

For Outlook, change the connection to:
```python
with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
    server.starttls()
    server.login(sender, password)
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `SMTPAuthenticationError` | Wrong password or not using App Password | Generate a new App Password |
| `Email config missing` | One of the `.env` variables is empty | Check `EMAIL_SENDER`, `EMAIL_PASSWORD`, `EMAIL_TO` in `.env` |
| `Connection refused` | Firewall or wrong port | Try port `587` with STARTTLS instead |
| Email goes to spam | No SPF/DKIM on sender domain | Use Gmail or check your spam folder first |
