#Music Platform Playlist Curator
A Django web application that allows users to convert explicit playlists to clean versions across Spotify and YouTube Music platforms. The application provides an intuitive interface for managing and converting playlists while maintaining high-quality matches for clean versions of songs.
Features

####Spotify Integration:

OAuth2 authentication with Spotify API
Fetch and display user playlists
Convert explicit playlists to clean versions
Smart matching algorithm for finding clean alternatives
Batch processing of playlist tracks
Token management and automatic refresh


###YouTube Music Integration:

Google OAuth2 authentication
Access to YouTube Music playlists
Playlist conversion capabilities
Track search functionality
Playlist creation and management


###User Interface:

Modern, responsive design using Bootstrap
Real-time updates with HTMX
Interactive playlist browsing
Detailed conversion results
Progress indicators for long-running operations



##Prerequisites

Python 3.x
Django 5.1+
Memcached
Node.js and npm (for frontend development)

##Environment Setup

###Create a virtual environment:

```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

###Install dependencies:

```
pip install -r requirements.txt
```

###Create a .env file in the root directory with the following variables:


SP_CLIENT_ID=your_spotify_client_id
SP_CLIENT_SECRET=your_spotify_client_secret
SP_REDIRECT_URI=your_spotify_redirect_uri

YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_REDIRECT_URI=your_youtube_redirect_uri

###Set up the database:

```
python manage.py migrate
```
###Start the development server:
```
python manage.py runserver
```
##Project Structure
CopynewMusicCleaner/
├── spotify_app/           # Spotify integration
│   ├── api.py            # API endpoints
│   ├── models.py         # Database models
│   ├── spotify_service.py # Spotify service layer
│   └── views.py          # View controllers
├── youtube_app/          # YouTube Music integration
├── templates/            # HTML templates
│   ├── base.html
│   ├── components/       # Reusable components
│   └── navbar.html
├── static/              # Static assets
└── manage.py
##API Endpoints
###Spotify Endpoints

GET /api/user - Get current user information
GET /api/playlists - Get user's playlists
GET /api/playlists/{playlist_id}/tracks - Get tracks from a playlist
POST /api/playlist/{playlist_id}/convert - Convert playlist to clean version
POST /api/playlist/{playlist_id}/additionalSongs - Add songs to playlist

###YouTube Music Endpoints

GET /api/youtube/user - Get YouTube user information
GET /api/youtube/playlists - Get user's YouTube playlists
GET /api/youtube/playlists/{playlist_id}/tracks - Get playlist tracks
POST /api/youtube/playlist/{playlist_id}/convert - Convert YouTube playlist
GET /api/youtube/search - Search for tracks
POST /api/youtube/playlist/create - Create new playlist
POST /api/youtube/playlist/{playlist_id}/tracks - Add tracks to playlist

###Authentication
The application uses OAuth2 for both Spotify and YouTube Music authentication. Users need to authorize the application to access their account data. Token management is handled automatically, including refresh token rotation.
