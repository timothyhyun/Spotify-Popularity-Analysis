import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import json
import os
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import MinMaxScaler, RobustScaler, OneHotEncoder
import matplotlib.pyplot as plt

#hidden for security purposes. 
#must create own spotify app and gather client id and secret
cid ="XXXXXX"
secret = "XXXXXX"

os.environ['SPOTIPY_CLIENT_ID']= cid
os.environ['SPOTIPY_CLIENT_SECRET']= secret
os.environ['SPOTIPY_REDIRECT_URI']= 'http://127.0.0.1:5000/authorize'


username = ""
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret) 
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
scope = 'user-top-read'
token = util.prompt_for_user_token(username, scope)


if token: 
    sp = spotipy.Spotify(auth=token)
    #load trained model
    new_model = keras.models.load_model('trained_model')
    #gather top 50 songs
    result = sp.current_user_top_tracks(limit=50,offset=0,time_range='short_term')
    song_list = result['items']
    list_ids = []
    artists = []
    valence = []
    year = []
    acousticness = []
    danceability = []
    duration_ms = []
    loudness = []
    energy = []
    explicit = []
    instrumentalness = []
    key = []
    liveness = []
    mode = []
    speechiness = []
    tempo = []
    name = []
    #gather audio features for each song
    for song in song_list: 
        empty = []
        list_ids.append(song['id'])
        artists.append(song['album']['artists'][0]['name'])
        if song['explicit']:
            explicit.append(1)
        else: 
            explicit.append(0)
        year.append(int(song['album']['release_date'][:4]))
        name.append(song['name'])
    features_list = sp.audio_features(tracks=list_ids)
    for song in features_list: 
        valence.append(song['valence'])
        acousticness.append(song['acousticness'])
        danceability.append(song['danceability'])
        duration_ms.append(song['duration_ms'])
        energy.append(song['energy'])
        instrumentalness.append(song['instrumentalness'])
        key.append(song['key'])
        liveness.append(song['liveness'])
        mode.append(song['mode'])
        speechiness.append(song['speechiness'])
        tempo.append(song['tempo'])
        loudness.append(song['loudness'])
    array = []
    #compine into dataframe to input into model
    for i in range(50):
        array.append([valence[i], year[i], acousticness[i],artists[i], danceability[i], duration_ms[i], energy[i], explicit[i], 
        instrumentalness[i], key[i], liveness[i], loudness[i], mode[i], name[i], speechiness[i], tempo[i]])
    dataframe = pd.DataFrame(array, columns=['valence', 'year', 'acousticness', 'artists', 'danceability', 'duration_ms', 'energy', 'explicit', 
    'instrumentalness', 'key', 'liveness', 'loudness', 'mode', 'name', 'speechiness', 'tempo'])
    predictions = []
    #map artist popularity
    meanPopularity = 31.7209
    with open('artists.json') as json_file:
        artistDict = json.load(json_file)
    
    keys = list(artistDict.keys())
    #use tuples to store artists as the key for the dictionary
    tupleKeys = []
    for i in keys:
        af = len(i)
        tupleKeys.append(i[2:af-2])
    values = list(artistDict.values())
    res = {tupleKeys[i]: values[i] for i in range(len(tupleKeys))}
    dataframe['artists'] = dataframe['artists'].map(lambda artist: res.get(artist, meanPopularity))
    dataframe.drop(columns='name')
    #store data into csv file
    dataframe.to_csv('song_data.csv')
    #normalize data for testing
    ct = ColumnTransformer([('minmax', MinMaxScaler(), ['year', 'tempo', 'duration_ms']),
                        ('categorial', OneHotEncoder(), ['key']),
                       ('drop_cols', 'drop', ['name'])],
                       remainder='passthrough')
    ct.fit(dataframe)
    dataframeProcessed = ct.transform(dataframe)
    #predict popularities
    ans = new_model.predict(dataframeProcessed)
    ansList = ans.tolist()
    roundList = []
    for i in ansList:
        roundList.append(round(i[0]))
    combined = list(zip(name, roundList))
    ansDataframe = pd.DataFrame(combined, columns=['Song', 'Popularity'])
    #sort songs by most popular to least
    ansDataframe.sort_values(by='Popularity', inplace=True, ascending=False)
    ansDataframe.reset_index()
    #move prediction into a dataframe and save into csv file
    ansDataframe.to_csv('result.csv')

else: 
    print("Unable to Log in")
