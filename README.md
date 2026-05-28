# steam-scripts

A Python automation project that checks Steam for 100% free games, filters out games you already own, and emails you a styled notification — once per game per month.

Runs locally or on AWS Lambda (free tier).

---

## Project Structure

```
steam-scripts/
├── main.py                        ← local entry point
├── lambda_function.py             ← AWS Lambda entry point
├── package.bat                    ← builds lambda.zip for deployment
├── run.bat                        ← local Task Scheduler launcher
├── .env                           ← your secrets (never commit this)
├── .gitignore
├── notified_games_owner.json      ← owner notification cache (auto-generated)
├── notified_games_guests.json     ← per-guest notification cache, HMAC-keyed (auto-generated)
├── run_log.txt                    ← local run log (auto-generated)
└── scripts/
    ├── __init__.py
    ├── check_full_discount_games.py
    └── send_email.py
```

---

## Requirements

- Python 3.10+
- `pip install requests python-dotenv`

---

## Local Setup

### 1. Install dependencies

```powershell
pip install requests python-dotenv
```

### 2. Create your `.env` file

```ini
STEAM_API_KEY=your_steam_api_key
STEAM_ID=your_64bit_steam_id
FULL_DISCOUNT_URL=your_deals_feed_url
GET_OWNED_GAMES_URL=https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/

EMAIL_SENDER=yourgmail@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=youremail@gmail.com

# Optional: comma-separated guest emails
GUEST_EMAILS=guest1@gmail.com,guest2@gmail.com

# Required if GUEST_EMAILS is set — keeps guest emails out of the cache file
GUEST_HASH_SECRET=some_long_random_secret_here
```

### 3. Run

```powershell
python main.py check_full_discount_games
```

---

## AWS Lambda Deployment

See [`docs/lambda_deployment.md`](docs/lambda_deployment.md) for the full guide.

**Quick steps:**
1. Create an S3 bucket for the cache
2. Create a Lambda function (Python 3.12)
3. Set environment variables in Lambda config (same keys as `.env`, including `GUEST_EMAILS`, `GUEST_HASH_SECRET`, and `CACHE_BUCKET`)
4. Run `package.bat` → upload `lambda.zip`
5. Create an EventBridge rule with cron `0 9 * * ? *` (5 PM PHT / 9 AM UTC)

---

## How local vs Lambda differs

| | Local | Lambda |
|---|---|---|
| Entry point | `main.py` | `lambda_function.py` |
| Config | `.env` file | Lambda environment variables |
| Owner cache | `notified_games_owner.json` (file) | S3 bucket (`CACHE_BUCKET`) |
| Guest cache | `notified_games_guests.json` (file) | S3 bucket (`CACHE_BUCKET`) |
| Guest privacy | Emails HMAC-hashed in cache file | Same — secret set via env var |
| Log output | Emails masked (e.g. `al***@g***.com`) | Same |
| Scheduling | Windows Task Scheduler / `run.bat` | EventBridge cron rule |
| Trigger detection | No `AWS_LAMBDA_FUNCTION_NAME` env var | Auto-set by AWS |

---

## Available Commands (local)

| Command | Description |
|---|---|
| `python main.py check_full_discount_games` | Check for free games and send email |

---

## Resetting the notification cache

**Local:**
```powershell
del notified_games_owner.json
del notified_games_guests.json
```

**Lambda:**
Delete `notified_games_owner.json` and `notified_games_guests.json` from your S3 bucket in the AWS Console.

---

## Adding a new script

1. Create `scripts/my_script.py` with a `run()` function
2. Add `from scripts import my_script` to `main.py`
3. Add an `elif command == "my_script":` branch in `main.py`
4. Call `my_script.run()` from `lambda_function.py` if you want it on Lambda too

---

## Documentation

| File | Contents |
|---|---|
| [`docs/check_full_discount_games.md`](docs/check_full_discount_games.md) | Script reference, Steam API setup |
| [`docs/send_email.md`](docs/send_email.md) | Gmail App Password setup, SMTP providers |
| [`docs/lambda_deployment.md`](docs/lambda_deployment.md) | Full AWS Lambda + EventBridge setup guide |
