# check_full_discount_games.py

Checks a Steam deals feed for 100% free games and sends email notifications — separately for the owner and for any guests. The owner gets an ownership-filtered list; guests receive all free games.

---

## Flow

```
Fetch deals list
        ↓
Extract App IDs → fetch game details for all
        ↓
  ┌─────────────────────────┐   ┌──────────────────────────────┐
  │        OWNER            │   │          GUESTS               │
  │ Filter: not in library  │   │ No ownership filter           │
  │ Cache: owner cache      │   │ Cache: shared guest cache     │
  │ Email: EMAIL_TO         │   │ Email: each in GUEST_EMAILS   │
  └─────────────────────────┘   └──────────────────────────────┘
```

- Games are not re-sent to the same audience for **31 days** after first notification
- Owner and guests have **separate caches** — a game notified to the owner does not suppress it for guests, and vice versa

---

## Required `.env` Variables

| Variable | Who uses it | Description |
|---|---|---|
| `FULL_DISCOUNT_URL` | Both | URL returning the 100% off games list |
| `GET_OWNED_GAMES_URL` | Owner | `https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/` |
| `STEAM_API_KEY` | Owner | Your Steam Web API key |
| `STEAM_ID` | Owner | Your 64-bit Steam ID |
| `EMAIL_TO` | Owner | Where to send the owner notification |
| `GUEST_EMAILS` | Guests | Comma-separated list of guest email addresses |

### `GUEST_EMAILS` format

```ini
GUEST_EMAILS=friend@gmail.com,another@outlook.com,third@yahoo.com
```

Leave it empty or omit it entirely to skip guest notifications.

### Getting your Steam API Key
1. Go to [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
2. Log in → register any domain (e.g. `localhost`)
3. Copy the key → paste as `STEAM_API_KEY`

### Getting your Steam ID
1. Go to [steamid.io](https://steamid.io)
2. Enter your Steam profile URL or username
3. Copy the **steamID64** value → paste as `STEAM_ID`

---

## Cache Files

| File | Used by | Stores |
|---|---|---|
| `notified_games_owner.json` | Owner only | Games already emailed to the owner |
| `notified_games_guests.json` | All guests | Games already emailed to guests |

On Lambda, both files are stored in the S3 bucket defined by `CACHE_BUCKET`.

**Resetting the cache:**

Local:
```powershell
del notified_games_owner.json
del notified_games_guests.json
```

Lambda: delete the corresponding files from your S3 bucket in the AWS Console.

---

## Functions

| Function | Description |
|---|---|
| `run()` | Main entry point — called by `main.py` and `lambda_function.py` |
| `notify_owner()` | Ownership-filtered flow → emails `EMAIL_TO` |
| `notify_guests()` | Unfiltered flow → emails each address in `GUEST_EMAILS` |
| `get_unowned_apps()` | Calls Steam API to find which app IDs you don't own |
| `get_game_details()` | Calls Steam Store API for a single app's name and image |
| `filter_already_notified()` | Reads/writes a specific cache, returns only unseen games |
| `load_cache()` / `save_cache()` | Read and write a cache file (local or S3) |

---

## Example Output

```
Deals request successful!

Found 3 deals. Fetching details...

--- Owner ---
1 unowned, 1 not yet notified.
  - [2218460] Bunny Guys!
Email sent to you@gmail.com

--- Guests ---
2 games not yet sent to guests.
  - [2218460] Bunny Guys!
  - [3343840] Dino running from a FURRY: GAMESFORFARM
Email sent to friend@gmail.com
Email sent to another@outlook.com
```

---

## Run it manually

```powershell
python main.py check_full_discount_games
```
