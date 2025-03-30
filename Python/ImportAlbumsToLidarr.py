
import csv
import requests
import time
import difflib
import re
import sys
import getpass
import os

# === CONFIGURATION ===
LOG_FILE = "lidarr_output.log"

# === INTERACTIVE OPTIONS ===
def prompt_lidarr_settings():
    print("📡 Enter Lidarr connection info:")
    lidarr_url = input("Lidarr URL (e.g., http://localhost:8686): ").strip()
    api_key = getpass.getpass("API Key: ").strip()
    return lidarr_url, api_key

def prompt_csv_file():
    print("📄 Enter the path to your CSV file (drag and drop is fine):")
    path = input("CSV File: ").strip().strip('"')
    while not os.path.isfile(path):
        print("❌ File not found. Try again:")
        path = input("CSV File: ").strip().strip('"')
    return path

def prompt_main_mode():
    print("🎧 Spotify to Lidarr Importer")
    print("1. Add Artists only")
    print("2. Add Artists + All Albums (Monitored)")
    print("3. Add Specific Albums from CSV")
    print("4. Exit")
    return input("Choose mode [1-4]: ").strip()

def prompt_options():
    use_fuzzy = input("Enable fuzzy album matching? [y/N]: ").strip().lower() == 'y'

    print("\nWhat would you like to show in the console?")
    print("1. All")
    print("2. Only errors")
    print("3. Only successes")
    console_choice = input("Choice (default = 2): ").strip() or "2"

    print("\nWhat would you like to write to the log file?")
    print("1. All")
    print("2. Only errors")
    print("3. Only successes")
    print("4. No log file")
    log_choice = input("Choice (default = 2): ").strip() or "2"

    return use_fuzzy, console_choice, log_choice

# === LOGGING & DISPLAY ===
def should_log(message_type, mode):
    if mode == "1":
        return True
    if mode == "2" and message_type == "error":
        return True
    if mode == "3" and message_type == "success":
        return True
    return False

def output(message, message_type="info"):
    if should_log(message_type, log_mode):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    if should_log(message_type, console_mode):
        print(message)

# === UTILS ===
def normalize(text):
    text = text.lower()
    text = re.sub(r"[\[\(\{].*?[\]\)\}]", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()

def read_csv_entries(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return {(row["Artist Name(s)"], row["Album Name"]) for row in reader if row["Artist Name(s)"] and row["Album Name"]}

# === LIDARR API ===
def search_artist(name):
    res = requests.get(f"{LIDARR_URL}/api/v1/artist/lookup?term={name}", headers=HEADERS)
    return res.json() if res.ok else []

def add_artist(artist, monitor_all_albums=False):
    payload = {
        "artistName": artist["artistName"],
        "foreignArtistId": artist["foreignArtistId"],
        "metadataProfileId": 1,
        "monitored": True,
        "rootFolderPath": artist.get("rootFolderPath", "D:\\Music"),
        "qualityProfileId": 1,
        "addOptions": {
            "searchForMissingAlbums": monitor_all_albums,
            "monitor": "all" if monitor_all_albums else "none"
        }
    }
    res = requests.post(f"{LIDARR_URL}/api/v1/artist", json=payload, headers=HEADERS)
    return res.ok

def get_existing_artists():
    res = requests.get(f"{LIDARR_URL}/api/v1/artist", headers=HEADERS)
    return res.json() if res.ok else []

def get_albums_for_artist(artist_id):
    res = requests.get(f"{LIDARR_URL}/api/v1/album?artistId={artist_id}", headers=HEADERS)
    return res.json() if res.ok else []

def monitor_album(album):
    album["monitored"] = True
    res = requests.put(f"{LIDARR_URL}/api/v1/album/{album['id']}", json=album, headers=HEADERS)
    return res.ok

# === MODES ===
def mode_add_artists(entries, monitor_all):
    existing_artists = {a['artistName'].lower(): a for a in get_existing_artists()}

    for artist_name, _ in entries:
        if artist_name.lower() in existing_artists:
            output(f"✔️ Artist already in Lidarr: {artist_name}", "success")
            continue

        search_results = search_artist(artist_name)
        if not search_results:
            output(f"❌ Artist not found: {artist_name}", "error")
            continue

        added = add_artist(search_results[0], monitor_all_albums=monitor_all)
        if not added:
            output(f"❌ Failed to add artist: {artist_name}", "error")
        else:
            output(f"✅ Added artist: {artist_name}", "success")

        time.sleep(0.5)

def mode_add_specific_albums(entries, use_fuzzy):
    seen = set()
    existing_artists = {a['artistName'].lower(): a for a in get_existing_artists()}

    for artist_name, album_name in entries:
        key = (artist_name.lower(), album_name.lower())
        if key in seen:
            continue
        seen.add(key)

        artist = existing_artists.get(artist_name.lower())

        if not artist:
            search_results = search_artist(artist_name)
            if not search_results:
                output(f"❌ Artist not found: {artist_name}", "error")
                continue

            added = add_artist(search_results[0], monitor_all_albums=False)
            if not added:
                output(f"❌ Failed to add artist: {artist_name}", "error")
                continue
            else:
                output(f"✅ Added artist: {artist_name}", "success")

            time.sleep(1)
            existing_artists = {a['artistName'].lower(): a for a in get_existing_artists()}
            artist = existing_artists.get(artist_name.lower())

        albums = get_albums_for_artist(artist['id'])

        matched = []
        if not use_fuzzy:
            matched = [a for a in albums if a['title'].lower() == album_name.lower()]
        else:
            norm_album_name = normalize(album_name)
            normalized_titles = {normalize(a['title']): a for a in albums}
            if norm_album_name in normalized_titles:
                matched = [normalized_titles[norm_album_name]]
            else:
                close_matches = difflib.get_close_matches(norm_album_name, normalized_titles.keys(), n=1, cutoff=0.8)
                matched = [normalized_titles[m] for m in close_matches] if close_matches else []

        if not matched:
            output(f"⚠️ Album not found: {album_name} by {artist_name}", "error")
            continue

        for album in matched:
            if not album['monitored']:
                success = monitor_album(album)
                if not success:
                    output(f"❌ Failed to monitor album: {album['title']} by {artist_name}", "error")
                else:
                    output(f"✅ Monitoring album: {album['title']} by {artist_name}", "success")
            else:
                output(f"✔️ Already monitored: {album['title']} by {artist_name}", "success")

        time.sleep(0.5)

# === MAIN ===
def main():
    global console_mode, log_mode, LIDARR_URL, API_KEY, HEADERS
    LIDARR_URL, API_KEY = prompt_lidarr_settings()
    HEADERS = {"X-Api-Key": API_KEY}

    mode = prompt_main_mode()
    if mode not in ["1", "2", "3"]:
        print("👋 Exiting.")
        sys.exit(0)

    csv_path = prompt_csv_file()
    entries = read_csv_entries(csv_path)
    use_fuzzy, console_mode, log_mode = prompt_options()

    if log_mode != "4":
        open(LOG_FILE, "w").close()

    if mode == "1":
        mode_add_artists(entries, monitor_all=False)
    elif mode == "2":
        mode_add_artists(entries, monitor_all=True)
    elif mode == "3":
        mode_add_specific_albums(entries, use_fuzzy)

if __name__ == "__main__":
    main()
