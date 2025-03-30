import csv
import requests
import time

# === CONFIGURATION ===
LIDARR_URL = "http://localhost:8686"
API_KEY = "ENTER YOUR LIDARR API KEY HERE"
CSV_FILE = "CSV PATH.csv"
LOG_FILE = "lidarr_errors.log"

HEADERS = {"X-Api-Key": API_KEY}

# === FUNCTIONS ===
def log_issue(message):
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def search_artist(name):
    res = requests.get(f"{LIDARR_URL}/api/v1/artist/lookup?term={name}", headers=HEADERS)
    return res.json() if res.ok else []

def add_artist(artist):
    payload = {
        "artistName": artist["artistName"],
        "foreignArtistId": artist["foreignArtistId"],
        "metadataProfileId": 1,
        "monitored": True,
        "rootFolderPath": artist.get("rootFolderPath", "D:\\Music"),
        "qualityProfileId": 1,
        "addOptions": {
            "searchForMissingAlbums": True,
            "monitor": "all"
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

# === MAIN ===
def main():
    seen = set()

    # Clear log file
    open(LOG_FILE, "w").close()

    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        entries = {(row["Artist Name(s)"], row["Album Name"]) for row in reader if row["Artist Name(s)"] and row["Album Name"]}

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
                log_issue(f"❌ Artist not found: {artist_name}")
                continue

            artist_info = search_results[0]
            added = add_artist(artist_info)
            if not added:
                log_issue(f"❌ Failed to add artist: {artist_name}")
                continue

            time.sleep(1)
            existing_artists = {a['artistName'].lower(): a for a in get_existing_artists()}
            artist = existing_artists.get(artist_name.lower())

        albums = get_albums_for_artist(artist['id'])
        matched = [a for a in albums if a['title'].lower() == album_name.lower()]
        if not matched:
            log_issue(f"⚠️ Album not found: {album_name} by {artist_name}")
            continue

        for album in matched:
            if not album['monitored']:
                success = monitor_album(album)
                if not success:
                    log_issue(f"❌ Failed to monitor album: {album['title']} by {artist_name}")

        time.sleep(0.5)

if __name__ == "__main__":
    main()
