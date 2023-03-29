##Libraries
import yt_dlp
import os
import spotipy
import auth ##File to store clientId and secret for Spotify Authentication
import unicodedata
import re


##Extractions
from ytmusicapi import YTMusic
from spotipy.oauth2 import SpotifyClientCredentials


##Spotify Authentication
client = SpotifyClientCredentials(client_id = auth.get_clientid(), client_secret = auth.get_secret()) 
sp = spotipy.Spotify(client_credentials_manager = client)


##Search
def VideoSearch(Query):
    ytmusic = YTMusic("headers_auth.json") ##json file to store client auth
    return ("https://www.youtube.com/watch?v=" + ytmusic.search(Query)[0]['videoId'])


##Directory Friendly String Manipulation
def slugify(value, allow_unicode=False):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


##Debug Logger
class MyLogger:
    def debug(self, msg):
        # For compatability with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass
        else:
            self.info(msg)

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


##Callback for Progress
def my_hook(d):
    if d['status'] == 'finished':
        print(f'Download Complete ({b_to_mb(d["total_bytes"])}MB) -> Converting File Format\n')
        

##Config
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
}


def get_uri(URL):
    return URL.split("/")[-1].split("?")[0]

def b_to_mb(b):
    return round((b / 1024 / 1000), 2)

def get_all_tracks(playlist_url):
    ##Playlist URI
    playlist_uri = get_uri(playlist_url)

    res = sp.playlist_tracks(playlist_uri)
    tracks = res['items']

    while res['next']:
        res = sp.next(res)
        tracks.extend(res['items'])

    return tracks


def get_queries(playlist_url):
    ##Playlist Tracks
    Tracks = get_all_tracks(playlist_url)

    ##List of Resulting Queries
    res_queries = []
    res_data = []

    ##Create Queries
    for Track in Tracks:
        new_song_data = []
        new_song_data.append(Track["track"]["artists"][0]["name"])
        new_song_data.append(Track["track"]["name"])

        res_queries.append((Track["track"]["artists"][0]["name"]) + " " + (Track["track"]["name"]) + " audio")
        res_data.append(new_song_data)
    
    print(f"Created Search Queries For: {len(res_queries)} Track(s)")
    return res_queries, res_data


def get_links(queries):
    ##List of Resulting URLs
    res_links = []

    print(f"Creating URL Results For: {len(queries)} Track(s)")
    for Query in queries:
        ##Search For Query
        new_search = VideoSearch(Query)

        ##Add Search Result Link Into List
        res_links.append(new_search)
        print(f"  - Created URL: {new_search}")

    print(f"Created URL Results For: {len(res_links)} Track(s)\n")
    return res_links


def change_dir(new_name, playlist_name):
    dest_dir  = os.path.abspath("./Download" + "/" + playlist_name)
    cur_dir   = os.path.abspath(".")

    for file in os.listdir(cur_dir):
        if file[-4:] == ".mp3":
            final_dest = (dest_dir + "/" + slugify(new_name) + ".mp3")
            os.rename(os.path.abspath(file), final_dest)


def download_playlist(URL):
    ##Fetch Data
    queries, song_data  = get_queries(URL)
    links               = get_links(queries)
    p_name              = sp.playlist(get_uri(URL))['name']

    ##Create New Directory
    dir_index = len([name for name in os.listdir(os.path.abspath('./Download'))])
    dir_name  = slugify(("Playlist_" + str(dir_index) + "_" + p_name))
    dir_path  = (os.path.abspath("./Download/" + dir_name))

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


    ##Download Audio Stream
    for index in range(len(links)):
        ##Fetch Data
        cur_data  = song_data[index]

        ##Query Data
        artist_name  = cur_data[0]
        song_name    = cur_data[1]

        ##Call Download Method
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"{(artist_name + ' - ' + song_name)}: id = {links[index][-11:]}")
            ydl.download(links[index])
            

        ##Change Directory of New Download
        change_dir((artist_name + " - " + song_name), dir_name)