import csv

def load_tracks():
    tracks = []

    with open("tracks.csv", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            row["bpm"] = int(row["bpm"])
            row["duration"] = int(row["duration"])
            tracks.append(row)

    return tracks
def generate_playlist(task, time_minutes):
    tracks = load_tracks()
    filtered = []

    if task == "focus":
        filtered = [
            t for t in tracks
            if t["bpm"] <= 100 and t["lyrics"] != "yes"
        ]

    elif task == "study":
        filtered = [
            t for t in tracks
            if t["bpm"] <= 120 and t["lyrics"] == "min"
        ]

    playlist = []
    total_time = 0
    max_time = time_minutes * 60

    for song in filtered:
        if total_time + song["duration"] <= max_time:
            playlist.append(song)
            total_time += song["duration"]

    return playlist
