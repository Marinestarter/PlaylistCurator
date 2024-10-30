import pytest
from unittest.mock import Mock, patch
from django.core.cache import cache, CacheKeyWarning
from django.test import override_settings
from django.utils.deprecation import RemovedInDjango60Warning

from spotify_app.services.spotify_service import SpotifyService

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'spotify_app.tests.test_settings'

import warnings
warnings.filterwarnings("ignore", category=RemovedInDjango60Warning)
warnings.filterwarnings("ignore", message="Support for class-based `config` is deprecated")
warnings.filterwarnings("ignore", category=CacheKeyWarning)


@pytest.fixture(autouse=True)
def setup_django_settings():
    """Setup Django settings before each test"""
    with override_settings(
            CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                    'LOCATION': 'unique-snowflake',
                }
            }
    ):
        # Clear cache before each test
        cache.clear()
        yield

@pytest.fixture
def mock_cache():
    """Mock cache for testing"""
    with patch('django.core.cache.cache') as mock_cache:
        mock_cache.get.return_value = None
        yield mock_cache
@pytest.fixture
def spotify_service():
    return SpotifyService()


@pytest.fixture
def mock_spotipy():
    with patch('spotify_app.services.spotify_service.spotipy.Spotify') as mock:
        yield mock


@pytest.fixture
def sample_user_data():
    return {
        'id': 'test_user_id',
        'display_name': 'Test User',
        'external_urls': {'spotify': 'https://open.spotify.com/user/test_user_id'}
    }


@pytest.fixture
def sample_playlist_data():
    return {
        'items': [
            {
                'id': 'playlist1',
                'name': 'My Playlist 1',
                'tracks': {'total': 10}
            },
            {
                'id': 'playlist2',
                'name': 'My Playlist 2',
                'tracks': {'total': 5}
            }
        ]
    }


@pytest.fixture
def sample_tracks_data():
    return {
        'items': [
            {
                'track': {
                    'id': 'track1',
                    'name': 'Test Track 1',
                    'uri': 'spotify:track:track1',
                    'artists': [{'name': 'Artist 1', 'id': 'artist1', 'uri': 'spotify:artist:artist1'}],
                    'explicit': True,
                    'external_urls': {'spotify': 'https://open.spotify.com/track/track1'}
                }
            },
            {
                'track': {
                    'id': 'track2',
                    'name': 'Test Track 2',
                    'uri': 'spotify:track:track2',
                    'artists': [{'name': 'Artist 2', 'id': 'artist2', 'uri': 'spotify:artist:artist2'}],
                    'explicit': False,
                    'external_urls': {'spotify': 'https://open.spotify.com/track/track2'}
                }
            }
        ],
        'next': None
    }


def test_get_user(spotify_service, mock_spotipy, sample_user_data):
    # Arrange
    mock_instance = mock_spotipy.return_value
    mock_instance.current_user.return_value = sample_user_data

    # Act
    user = spotify_service.get_user()

    # Assert
    assert user == sample_user_data
    mock_instance.current_user.assert_called_once()


def test_get_playlists(spotify_service, mock_spotipy, sample_playlist_data):
    # Arrange
    mock_instance = mock_spotipy.return_value
    mock_instance.current_user_playlists.return_value = sample_playlist_data

    # Act
    playlists = spotify_service.get_playlists()

    # Assert
    assert playlists == sample_playlist_data['items']
    mock_instance.current_user_playlists.assert_called_once()


def test_get_playlist_tracks(spotify_service, mock_spotipy, sample_tracks_data):
    # Arrange
    mock_instance = mock_spotipy.return_value
    mock_instance.playlist_items.return_value = sample_tracks_data
    playlist_id = 'test_playlist_id'

    # Act
    tracks = spotify_service.get_playlist_tracks(playlist_id)
    # Assert
    expected_tracks = [item['track'] for item in sample_tracks_data['items']]
    assert tracks == expected_tracks
    mock_instance.playlist_items.assert_called_once_with(playlist_id)


def test_convert_playlist(spotify_service, mock_spotipy, sample_user_data, sample_tracks_data):
    # Arrange
    mock_instance = mock_spotipy.return_value
    playlist_id = 'test_playlist_id'

    mock_instance.playlist.return_value = {'name': 'Original Playlist'}
    mock_instance.playlist_items.return_value = sample_tracks_data
    mock_instance.current_user.return_value = sample_user_data
    mock_instance.user_playlist_create.return_value = {'id': 'new_playlist_id'}
    mock_instance.search.return_value = {
        'tracks': {
            'items': [
                {
                    'name': 'Clean Test Track 1',
                    'uri': 'spotify:track:clean1',
                    'explicit': False,
                    'artists': [{'name': 'Artist 1'}],
                    'external_urls': {'spotify': 'https://open.spotify.com/track/clean1'}
                }
            ]
        }
    }

    # Act
    result = spotify_service.convert_playlist(playlist_id, to_clean=True)
    # Assert
    assert isinstance(result, dict)
    assert 'playlist_id' in result
    assert 'num_original_clean' in result
    assert 'num_clean_found' in result
    assert 'num_still_missing' in result
    assert 'potential_matches' in result

    mock_instance.playlist.assert_called_once_with(playlist_id)
    mock_instance.user_playlist_create.assert_called_once()
    assert mock_instance.playlist_add_items.called


def test_contain_same_artists(spotify_service):
    # Arrange
    track1 = {
        'artists': [
            {'name': 'Artist 1'},
            {'name': 'Artist 2'}
        ]
    }
    track2 = {
        'artists': [
            {'name': 'Artist 1'},
            {'name': 'Artist 2'}
        ]
    }
    track3 = {
        'artists': [
            {'name': 'Artist 1'},
            {'name': 'Different Artist'}
        ]
    }

    # Act & Assert
    assert spotify_service.contain_same_artists(track1, track2) is True
    assert spotify_service.contain_same_artists(track1, track3) is False


def test_search_for_track(spotify_service, mock_spotipy):
    # Arrange
    mock_instance = mock_spotipy.return_value
    search_results = {
        'tracks': {
            'items': [
                {
                    'name': 'Test Track',
                    'uri': 'spotify:track:test',
                    'artists': [{'name': 'Test Artist'}]
                }
            ]
        }
    }
    mock_instance.search.return_value = search_results
    query = 'Test Track Test Artist'

    # Act
    results = spotify_service.search_for_track(query)

    # Assert
    assert results == search_results['tracks']['items']
    mock_instance.search.assert_called_once_with(q=query, type='track', limit=50)