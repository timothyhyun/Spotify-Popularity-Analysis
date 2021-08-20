import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
from flask import Flask, url_for, session, request, redirect
import json
import os
import tensorflow as tf
from tensorflow import keras
import time
import pandas as pd
import requests
import logging

# App config
app = Flask(__name__)

app.secret_key = 'placeholder'
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

@app.route('/')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()

    return redirect(auth_url)

@app.route('/authorize')
def authorize():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect("/display")

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/display')
def display():
    session['token_info'], authorized = get_token()
    session.modified = True
    if not authorized:
        return redirect('/')

    #sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    #userSongs = sp.current_user_top_tracks(limit=50, offset=0, time_range='short_term')
    headers = {"Authorization": "Bearer {}".format(session.get('token_info').get('access_token'))}
    response = getRequest('https://api.spotify.com/v1/me/top/tracks', headers, {'limit': 50, 'time_range': 'short_term'})
 
    new_model = keras.models.load_model('trained_model')
    song_data = pd.read_csv("songs.csv")
    ids = []
    for track in response['items']:
        ids.append(track['id'])
    
    return "done"

def getRequest(url, headers, params):
	response = requests.get(url, headers=headers, params=params)
	if response.status_code == 200:
		return response.json()
	else:
		logging.error('makeGetRequest:' + str(response.status_code))
		return None


# Checks to see if token is valid and gets a new token if not
def get_token():
    token_valid = False
    token_info = session.get("token_info", {})

    # Checking if the session already has a token stored
    if not (session.get('token_info', False)):
        token_valid = False
        return token_info, token_valid

    # Checking if token has expired
    now = int(time.time())
    is_token_expired = session.get('token_info').get('expires_at') - now < 60

    # Refreshing token if it has expired
    if (is_token_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid


def create_spotify_oauth():
    return SpotifyOAuth(
            client_id="1fb9a829517342e6b5d4a70915c6f626",
            client_secret="c80700e80d2f4be1934628e7369c968a",
            redirect_uri=url_for('authorize', _external=True),
            scope="user-library-read")