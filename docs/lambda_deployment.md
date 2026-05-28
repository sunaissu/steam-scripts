# Lambda Deployment

Runs the steam-scripts check on AWS Lambda on a daily schedule. No server required. Uses S3 to persist the notification cache between runs.

---

## Architecture

```
EventBridge (cron: daily at 9 AM UTC / 5 PM PHT)
        ↓
   Lambda Function
   (lambda_function.py → check_full_discount_games.run())
        ↓
   Reads/writes cache from S3
   ├── notified_games_owner.json   ← owner notification history
   └── notified_games_guests.json  ← per-guest notification history (HMAC-keyed)
        ↓
   Sends email via Gmail SMTP
   └── Logs show masked emails only (e.g. al***@g***.com)
```

---

## Prerequisites

- AWS account (free tier is enough)
- S3 bucket to store the cache files
- Gmail App Password (see `docs/send_email.md`)

---

## Step 1 — Create an S3 Bucket (for cache)

1. Go to **AWS Console** → S3 → **Create bucket**
2. Name it something like `steam-scripts-cache`
3. Region: pick the closest to you (e.g. `ap-southeast-1` for Southeast Asia)
4. Leave all other settings as default → **Create bucket**
5. Note the bucket name — you'll need it as `CACHE_BUCKET`

---

## Step 2 — Create the Lambda Function

1. Go to **AWS Console** → Lambda → **Create function**
2. Select **Author from scratch**
3. Settings:
   - **Function name:** `steam-free-games-check`
   - **Runtime:** Python 3.12
   - **Architecture:** x86_64
4. Click **Create function**

---

## Step 3 — Set Environment Variables

In your Lambda function → **Configuration** → **Environment variables** → Edit → Add:

| Key | Value |
|---|---|
| `FULL_DISCOUNT_URL` | Your deals feed URL |
| `GET_OWNED_GAMES_URL` | `https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/` |
| `STEAM_API_KEY` | Your Steam API key |
| `STEAM_ID` | Your 64-bit Steam ID |
| `EMAIL_SENDER` | Your Gmail address |
| `EMAIL_PASSWORD` | Your Gmail App Password |
| `EMAIL_TO` | Owner recipient email address |
| `CACHE_BUCKET` | Your S3 bucket name |
| `GUEST_EMAILS` | Comma-separated guest emails (e.g. `alice@gmail.com,bob@gmail.com`) |
| `GUEST_HASH_SECRET` | A long random secret string (see note below) |

> **Do NOT upload a `.env` file** — Lambda reads these directly from its config.

### Generating `GUEST_HASH_SECRET`

This secret is used to hash guest emails in the cache file so they are never stored in plain text. Generate one locally and paste it in:

```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 40 | % {[char]$_})
```

Keep this secret. If it changes, existing guests will receive one repeat notification (their cached history becomes unreadable) and tracking will resume normally after that.

---

## Step 4 — Give Lambda Permission to Access S3

1. In your Lambda function → **Configuration** → **Permissions**
2. Click the **role name** (opens IAM)
3. **Add permissions** → **Attach policies**
4. Search for `AmazonS3FullAccess` → Attach

> For tighter security, create a custom policy that only allows `s3:GetObject` and `s3:PutObject` on your specific bucket ARN.

---

## Step 5 — Package and Upload the Code

Run this from your project folder:

```powershell
package.bat
```

This creates `lambda.zip` containing:
- `lambda_function.py`
- `scripts/` folder
- `requests` library (pre-installed)

Then in AWS Lambda → **Code** → **Upload from** → **.zip file** → upload `lambda.zip`

Verify the handler is set to: `lambda_function.lambda_handler`

---

## Step 6 — Set the Timeout

Lambda defaults to 3 seconds — too short for HTTP requests.

1. **Configuration** → **General configuration** → Edit
2. Set **Timeout** to `1 min 0 sec`
3. Save

---

## Step 7 — Create the EventBridge Schedule

1. Go to **AWS Console** → **EventBridge** → **Rules** → **Create rule**
2. **Name:** `steam-free-games-daily`
3. **Rule type:** Schedule
4. **Schedule pattern:** Cron expression

```
0 9 * * ? *
```

*(9 AM UTC = 5 PM Philippine Time. Adjust as needed.)*

UTC offset reference:
| Your timezone | UTC offset | Cron for 5 PM local |
|---|---|---|
| PHT (Philippines) | +8 | `0 9 * * ? *` |
| SGT (Singapore) | +8 | `0 9 * * ? *` |
| EST (US East) | -5 | `0 22 * * ? *` |

5. **Target:** Lambda function → select `steam-free-games-check`
6. **Create rule**

---

## Step 8 — Test it manually

In your Lambda function → **Test** tab:
1. Create a test event (content doesn't matter, use `{}`)
2. Click **Test**
3. Check the **Execution results** panel for logs
4. Verify emails are masked in the logs (e.g. `al***@g***.com`) — full addresses are never printed
5. Check your email inbox

---

## Resetting the cache (Lambda)

The script now uses two separate cache files in S3:

| File | Purpose |
|---|---|
| `notified_games_owner.json` | Tracks games already sent to the owner |
| `notified_games_guests.json` | Tracks games sent per guest (HMAC-keyed, no plain emails) |

To reset all notifications, delete both files from your S3 bucket:

1. Go to S3 → your bucket
2. Select `notified_games_owner.json` and `notified_games_guests.json`
3. **Delete** → confirm

The next run will treat all games as new and re-send all emails.

### Adding a new guest

Simply add their email to the `GUEST_EMAILS` environment variable (comma-separated). Because the guest cache is tracked per-email, a new guest starts with no history and will be notified of all currently available deals on their first run.

---

## Cost estimate

| Service | Usage | Free tier | Cost |
|---|---|---|---|
| Lambda | 1 run/day = ~30/month | 1,000,000 runs/month | $0 |
| EventBridge | 1 rule | 14M events/month free | $0 |
| S3 | 2 tiny JSON files | 5 GB storage free | $0 |

**Total: $0.00/month**
