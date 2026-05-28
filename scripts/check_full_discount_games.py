import os
import json
import time
import hashlib
import hmac
import requests
import re
from scripts import send_email

CACHE_EXPIRATION_HOURS = 31 * 24
OWNER_CACHE_FILE = "notified_games_owner.json"
GUEST_CACHE_FILE = "notified_games_guests.json"
CACHE_BUCKET = os.getenv("CACHE_BUCKET", "")
IS_LAMBDA = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
GUEST_HASH_SECRET = os.getenv("GUEST_HASH_SECRET", "").encode()


def load_cache(cache_file: str) -> dict:
    if IS_LAMBDA:
        import boto3
        try:
            s3 = boto3.client("s3")
            obj = s3.get_object(Bucket=CACHE_BUCKET, Key=cache_file)
            return json.loads(obj["Body"].read().decode())
        except Exception:
            return {}
    else:
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)
        return {}


def save_cache(cache_data: dict, cache_file: str):
    if IS_LAMBDA:
        import boto3
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=CACHE_BUCKET,
            Key=cache_file,
            Body=json.dumps(cache_data, indent=4),
        )
    else:
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=4)


def filter_already_notified(games: list[dict], cache_file: str) -> list[dict]:
    cache_data = load_cache(cache_file)
    current_time = time.time()
    expiration_seconds = CACHE_EXPIRATION_HOURS * 3600

    new_games = []
    for game in games:
        app_id_str = str(game["appid"])
        if app_id_str in cache_data:
            if current_time - cache_data[app_id_str] < expiration_seconds:
                continue
        new_games.append(game)
        cache_data[app_id_str] = current_time

    save_cache(cache_data, cache_file)
    return new_games


def get_game_details(app_id: int) -> dict:
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us&l=en"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            app_data = data.get(str(app_id), {})
            if app_data.get("success"):
                info = app_data["data"]
                return {
                    "appid": app_id,
                    "name": info.get("name", f"App {app_id}"),
                    "logo": info.get("header_image", ""),
                }
    except Exception as e:
        print(f"Could not fetch details for app {app_id}: {e}")
    return {"appid": app_id, "name": f"App {app_id}", "logo": ""}


def get_unowned_apps(app_ids: list, get_owned_games_url: str, steam_id: str, api_key: str) -> list[int]:
    req_body = {
        "steamid": steam_id,
        "appids_filter": app_ids,
        "include_appinfo": 1,
        "include_played_free_games": 1,
    }
    params = {
        "key": api_key,
        "input_json": json.dumps(req_body),
    }

    response = requests.get(get_owned_games_url, params=params)
    if response.status_code == 200:
        data = response.json()
        owned_games = data.get("response", {}).get("games", [])
        owned_app_ids = {game.get("appid") for game in owned_games}
        return [app for app in app_ids if app not in owned_app_ids]
    else:
        print(f"Failed to fetch owned games. Status code: {response.status_code}")
        return []


def notify_owner(all_games: list[dict], get_owned_games_url: str, steam_id: str, api_key: str):
    print("\n--- Owner ---")
    unowned_ids = get_unowned_apps(
        [g["appid"] for g in all_games], get_owned_games_url, steam_id, api_key
    )
    unowned_games = [g for g in all_games if g["appid"] in set(unowned_ids)]

    new_games = filter_already_notified(unowned_games, OWNER_CACHE_FILE)
    print(f"{len(unowned_games)} unowned, {len(new_games)} not yet notified.")

    if not new_games:
        print("Nothing new for owner.")
        return

    for game in new_games:
        print(f"  - [{game['appid']}] {game['name']}")

    html = send_email.build_games_html(new_games)
    send_email.send(
        subject=f"🎮 {len(new_games)} New Free Steam Game(s) Available!",
        html_body=html,
    )


def notify_guests(all_games: list[dict], guest_emails: list[str]):
    print("\n--- Guests ---")

    cache_data = load_cache(GUEST_CACHE_FILE)
    current_time = time.time()
    expiration_seconds = CACHE_EXPIRATION_HOURS * 3600

    for email in guest_emails:
        email_key = hmac.new(GUEST_HASH_SECRET, email.encode(), hashlib.sha256).hexdigest()
        guest_cache = cache_data.get(email_key, {})

        new_games = []
        for game in all_games:
            app_id_str = str(game["appid"])
            if app_id_str in guest_cache:
                if current_time - guest_cache[app_id_str] < expiration_seconds:
                    continue
            new_games.append(game)
            guest_cache[app_id_str] = current_time

        cache_data[email_key] = guest_cache

        print(f"  [{send_email.mask_email(email)}] {len(new_games)} new game(s) to notify.")
        if not new_games:
            continue

        for game in new_games:
            print(f"    - [{game['appid']}] {game['name']}")

        html = send_email.build_games_html(new_games)
        subject = f"🎮 {len(new_games)} Free Steam Game(s) Right Now!"
        send_email.send(subject=subject, html_body=html, to_override=email)

    save_cache(cache_data, GUEST_CACHE_FILE)


def run():
    url                 = os.getenv("FULL_DISCOUNT_URL", "")
    get_owned_games_url = os.getenv("GET_OWNED_GAMES_URL", "")
    steam_id            = os.getenv("STEAM_ID", "")
    api_key             = os.getenv("STEAM_API_KEY", "")
    guest_emails        = [e.strip() for e in os.getenv("GUEST_EMAILS", "").split(",") if e.strip()]

    response = requests.get(url)
    if response.status_code != 200:
        print(f"Deals request failed with status code: {response.status_code}")
        return

    print("Deals request successful!\n")
    data = response.json()

    app_ids = []
    for item in data.get("items", []):
        logo_url = item.get("logo", "")
        match = re.search(r"/apps/(\d+)/", logo_url)
        if match:
            app_ids.append(int(match.group(1)))

    if not app_ids:
        print("No App IDs found in the deals list.")
        return

    print(f"Found {len(app_ids)} deals. Fetching details...")
    all_games = [get_game_details(app_id) for app_id in app_ids]

    notify_owner(all_games, get_owned_games_url, steam_id, api_key)

    if guest_emails:
        notify_guests(all_games, guest_emails)
    else:
        print("\nNo guest emails configured (GUEST_EMAILS not set).")
