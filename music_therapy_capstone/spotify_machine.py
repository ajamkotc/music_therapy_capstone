"""Module for interacting with Spotify API."""

import os
import base64
from dotenv import load_dotenv
import requests
import pandas as pd


class SpotifyMachine:
    """Contains various methods for querying the Spotify API for data.
    
    Attributes:
        CLIENT_ID (str) -- Required ID to acquire access token
        CLIENT_SECRET (str) -- Required Passkey to acquire access token
    
    Methods:
        gen_header():
            Generates authorization header for API calls.
        search_for_playlist(name):
            Extract single playlist JSON from Spotify.
        get_tracks(playlist_url):
            Gets list of top 50 tracks from the playlist_url.
        get_track_urls(track_dict):
            Returns a list of track IDs which can be used to query Spotify for audio features.
        get_track_features(track_id):
            Query Spotify for audio features of track and return dictionary result.
        gen_genre_def(genre):
            Generate pandas DataFrame containing audio features of 50 songs in specified genre.
        """

    # Extract CLIENT_ID and CLIENT_SECRET from local .env file
    load_dotenv()
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')

    def gen_header(self):
        """Generates authorization header for API calls.
        
        Returns:
            Header with the format: 'Bearer {access_token}'
        """

        # Creates authorization parameter for Client Credentials
        credentials = self.CLIENT_ID + ':' + self.CLIENT_SECRET
        auth_string = "Basic " + str(base64.b64encode(credentials.encode('utf-8')), 'utf-8')

        # Url to request token
        url = 'https://accounts.spotify.com/api/token'

        # Required headers for Client Credentials
        headers = {'Authorization':auth_string,
                'Content-Type':'application/x-www-form-urlencoded'}

        data = {'grant_type':'client_credentials'}

        # Request token by sending POST request and converting response to json
        r = requests.post(url=url, headers=headers, data=data)
        access_token = r.json()['access_token']

        return f"Bearer {access_token}"

    def search_for_playlist(self, name):
        """Extract single playlist JSON from Spotify.
        
        Params:
            name (str) -- Name of playlist to search
        
        Returns:
            Dictionary containing result of playlist search
        """

        url = 'https://api.spotify.com/v1/search?'

        headers = {'Authorization':self.gen_header()}

        params = {
            'q' : name,
            'type' : 'playlist',
            'limit' : 1
        }

        r = requests.get(url=url, params=params, headers=headers)

        if len(r.json()['playlists']['items']) > 0:
            return r.json()
        else:
            raise IndexError

    def get_tracks(self, playlist_url):
        """Gets list of top 50 tracks from the playlist_url.

        Params:
            playlist_url (str): Link to access Spotify playlist

        Returns:
            Dictionary containing the Spotify Track ID of each track
        """

        url = playlist_url
        headers = {'Authorization':self.gen_header()}
        params = {
            'fields':'items(track(uri))',
            'limit':50
                }

        r = requests.get(url=url, params=params, headers=headers)
        return r.json()

    def get_track_urls(self, track_dict):
        """Returns a list of track IDs which can be used to query Spotify for audio features.
        
        Params
            track_dict (dict) -- Dictionary of track items

        Returns
            track_urls (list) -- List of track urls
        """

        track_urls = []

        for track in track_dict['items']:
            track_url_str = track['track']['uri']
            track_urls.append(track_url_str.removeprefix('spotify:track:'))

        return track_urls

    def get_track_features(self, track_id):
        """Query Spotify for audio features of track and return dictionary result.
        
        Params
            track_ID (str) -- track id used by Spotify

        Returns
            Dictionary containing audio features of track corresponding to the track_ID
        """

        url = f"https://api.spotify.com/v1/audio-features/{track_id}"
        headers = {'Authorization':self.gen_header()}

        r = requests.get(url=url, headers=headers)

        return r.json()


    def gen_genre_df(self, genre):
        """Generate pandas DataFrame containing audio features of 50 songs in specified genre.
        
        Params
            genre (str) -- Genre to create df for
            header (str) -- Authorization header for making Spotify api calls
            
        Returns
            Dataframe containing audio features of 50 songs in top playlist of 'genre'"""

        try:
            # Get top playlist for genre
            playlist_json = self.search_for_playlist(genre)
        except IndexError:
            playlist_json = self.search_for_playlist(genre.lower())

        url = playlist_json['playlists']['items'][0]['tracks']['href']

        # Get list of tracks
        track_list = self.get_tracks(url)

        # Get list of track urls
        track_urls = self.get_track_urls(track_list)

        # Create list of dictionaries which contain audio features for each track
        data = []

        for track in track_urls:
            data.append(self.get_track_features(track))

        data_df = pd.DataFrame.from_dict(data)

        self.__save_data(data_df, genre)

        # Convert list of dicts to pandas DataFrame
        return data_df

    @staticmethod
    def __save_data(data, genre):
        """Save DataFrame as .csv file in raw folder.
        
        Params:
            data (DataFrame) -- data to be saved
            genre (str) -- genre of the data    
        """

        datapath = f"./../data/raw/{genre}.csv"
        data.to_csv(datapath, index=False)
