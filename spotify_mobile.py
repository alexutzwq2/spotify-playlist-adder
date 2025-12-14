import os
from flask import Flask, request, redirect, session, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = "supersecretkey123"  # secret pentru sesiuni
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

# Config Spotify
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

SCOPE = "playlist-modify-public playlist-modify-private"

sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE
)

# HTML simplu
HTML_PAGE = """
<!doctype html>
<title>Spotify Playlist Adder</title>
<h2>Adaugă melodie în playlist</h2>
{% if message %}
<p style="color:red;">{{ message }}</p>
{% endif %}
<form method="post">
  Link playlist:<br>
  <input type="text" name="playlist_url" size="50" required><br><br>
  Nume melodie:<br>
  <input type="text" name="track_name" size="50" required><br><br>
  <input type="submit" value="Caută și Adaugă">
</form>

{% if results %}
<h3>Rezultate:</h3>
<form method="post">
{% for idx, track in results %}
  <input type="radio" name="choice" value="{{ idx }}" required>
  {{ idx+1 }}. {{ track['name'] }} - {{ track['artists'][0]['name'] }}<br>
{% endfor %}
<input type="hidden" name="playlist_url" value="{{ playlist_url }}">
<input type="submit" value="Adaugă melodia aleasă">
</form>
{% endif %}

{% if success %}
<p style="color:green;">{{ success }}</p>
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def index():
    token_info = session.get("token_info", None)

    # 🔹 Debug: vezi token în Logs Render
    print("Token info in session:", token_info)

    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    sp = spotipy.Spotify(auth=token_info["access_token"])

    # Refresh token dacă expiră
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session["token_info"] = token_info
        sp = spotipy.Spotify(auth=token_info["access_token"])

    message = None
    results = None
    success = None
    playlist_url = ""

    if request.method == "POST":
        playlist_url = request.form.get("playlist_url")
        track_name = request.form.get("track_name")
        choice = request.form.get("choice")

        try:
            if choice is not None:
                idx = int(choice)
                track_uri = session["last_results"][idx]["uri"]
                playlist_id = playlist_url.split("/")[-1].split("?")[0]
                sp.playlist_add_items(playlist_id, [track_uri])
                success = f"Melodia '{session['last_results'][idx]['name']}' a fost adăugată!"
                session.pop("last_results")
            elif track_name:
                search_results = sp.search(q=track_name, type="track", limit=5)
                results = search_results['tracks']['items']
                if not results:
                    message = "Nu am găsit melodii cu acest nume."
                else:
                    session["last_results"] = results
        except Exception as e:
            message = f"Eroare: {str(e)}"

    # 🔹 Creăm listă (index, track) pentru Jinja
    results_with_index = list(enumerate(results)) if results else None

    return render_template_string(
        HTML_PAGE,
        message=message,
        results=results_with_index,
        success=success,
        playlist_url=playlist_url
    )

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    # 🔹 Debug: vezi token după callback
    print("Token after callback:", token_info)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
