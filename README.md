# Music Recommendation API Server

This API server provides a system for generating music recommendations based on emotional analysis of users' listening history.

## Features

- **Spotify Integration**: Connect to users' Spotify accounts to analyze their listening history
- **Lyrics Analysis**: Fetch lyrics for tracks and analyze their emotional content
- **Mood Prediction**: Uses AI service to predict mood from song lyrics
- **Emotional Profile**: Creates an emotional profile for users based on their listening history
- **Recommendations**: Generates music recommendations based on users' emotional profiles
- **Historical Tracking**: Records users' mood data over time for analysis
- **Statistics**: Provides endpoints to retrieve mood statistics over specific periods

## Technical Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy ORM with flexible backend support
- **Authentication**: JWT-based auth for API + OAuth for Spotify
- **External Services**:
  - Spotify API for music data
  - Genius API for lyrics
  - AI service for mood prediction and recommendations

## Getting Started

### Prerequisites

- Python 3.12+
- Spotify Developer API credentials
- Genius API access token
- Access to the AI mood prediction and recommendation service

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -e .
   ```
3. Create a `.env` file with the following configuration:
   ```
   SECRET_KEY=your-secret-key-for-jwt
   DATABASE_URI=sqlite:///./app.db  # or your preferred DB
   SPOTIFY_CLIENT_ID=your-spotify-client-id
   SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
   SPOTIFY_REDIRECT_URI=http://localhost:8000/api/v1/auth/spotify/callback
   GENIUS_ACCESS_TOKEN=your-genius-access-token
   AI_API_URL=https://your-ai-service-url.com/api
   AI_API_KEY=your-ai-api-key
   ```

### Running the Server

```
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

When the server is running, comprehensive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Core Endpoints

- **Authentication**:
  - POST `/api/v1/auth/register` - Register a new user
  - POST `/api/v1/auth/login` - Login and get access token

- **Spotify Connection**:
  - GET `/api/v1/spotify/auth` - Get Spotify auth URL
  - GET `/api/v1/spotify/callback` - Handle Spotify OAuth callback
  - GET `/api/v1/spotify/recent-tracks` - Get user's recently played tracks

- **Mood Analysis**:
  - GET `/api/v1/recommendations/analyze-recent-tracks` - Analyze recent tracks to determine mood
  - POST `/api/v1/mood/record` - Manually record user mood
  - GET `/api/v1/mood/statistics` - Get mood statistics over time
  - GET `/api/v1/mood/current` - Get user's current mood state

- **Recommendations**:
  - GET `/api/v1/recommendations/get-recommendations` - Get music recommendations based on mood
  - POST `/api/v1/recommendations/queue-song` - Add a recommended song to Spotify queue

## System Architecture

1. User connects their Spotify account through OAuth
2. The system fetches their recently played tracks
3. For each track, lyrics are retrieved from Genius API
4. The lyrics are sent to the AI service to predict emotional content
5. The system calculates the user's emotional profile by averaging these results
6. The emotional profile is stored in the database for historical tracking
7. The AI service provides recommendations based on the emotional profile
8. The system can queue recommended songs in the user's Spotify player

## License

MIT