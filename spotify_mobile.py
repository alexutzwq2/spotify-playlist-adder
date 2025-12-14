from flask import Flask, request, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import re

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")  # trebuie HTTPS pe Heroku

SCOPE = "playlist-modify-public playlist-modify-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
))

app = Flask(__name__)
tracks_cache = []
playlist_id_cache = None

def extrage_playlist_id(link):
    if not link:
        return None
    if "open.spotify.com" in link:
        m = re.search(r"playlist/([a-zA-Z0-9]+)", link)
        if m:
            return m.group(1)
    if link.startswith("spotify:playlist:"):
        return link.split(":")[-1]
    return None

HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Spotify Playlist Adder</title>
<style>
body { font-family: Arial; background:#121212; color:white; padding:20px; }
input, button { width:100%; padding:12px; margin:8px 0; font-size:16px; }
button { background:#1DB954; border:none; color:black; font-weight:bold; }
.card { background:#1e1e1e; padding:10px; margin:8px 0; border-radius:6px; }
</style>
</head>
<body>

<h2>Spotify Playlist Adder</h2>

<form method="post">
<input name="playlist" placeholder="Link playlist Spotify" required>
<input name="query" placeholder="Caută melodie">
<button name="action" value="search">Caută</button>
</form>

{% for i, t in tracks %}
<div class="card">
<b>{{ i }}.</b> {{ t.name }} - {{ t.artists }}
<form method="post">
<input type="hidden" name="track_uri" value="{{ t.uri }}">
<button name="action" value="add">Adaugă</button>
</form>
</div>
{% endfor %}

<p>{{ message }}</p>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global tracks_cache, playlist_id_cache
    message = ""
    tracks = []

    if request.method == "POST":
        playlist_link = request.form.get("playlist")
        playlist_id = extrage_playlist_id(playlist_link)

        if not playlist_id:
            message = "❌ Link playlist invalid"
        else:
            playlist_id_cache = playlist_id

            if request.form["action"] == "search":
                query = request.form.get("query", "")
                results = sp.search(q=query, type="track", limit=5)
                tracks_cache = results["tracks"]["items"]

            elif request.form["action"] == "add":
                uri = request.form.get("track_uri")
                sp.playlist_add_items(playlist_id_cache, [uri])
                message = "✅ Melodia a fost adăugată!"

    for i, t in enumerate(tracks_cache, start=1):
        tracks.append({
            "name": t["name"],
            "artists": ", ".join(a["name"] for a in t["artists"]),
            "uri": t["uri"]
        })

    return render_template_string(
        HTML,
        tracks=list(enumerate(tracks, 1)),
        message=message
    )

if __name__ == "__main__":
    app.run(debug=True)
