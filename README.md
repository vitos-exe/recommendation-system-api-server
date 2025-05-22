# Music Recommendation API Server

## Overview

This project is a FastAPI-based API server for a music recommendation system. The system analyzes the emotional content of songs based on their lyrics and provides music recommendations tailored to a user's current or historical mood. It integrates with Spotify to fetch user listening history and to queue recommended songs.

## Features

- **User Authentication:** Secure user registration and login using JWT (JSON Web Tokens).
- **Spotify Integration:**
    - OAuth 2.0 for connecting a user's Spotify account.
    - Fetches recently played tracks from Spotify.
    - Queues recommended songs directly to the user's Spotify player.
- **Mood Analysis:**
    - Fetches song lyrics from an external API (lyrics.ovh).
    - Utilizes an external AI service to predict the emotional mood (happy, sad, angry, relaxed) from song lyrics.
    - Records user mood entries manually or generates them from recent listening history.
- **Music Recommendations:**
    - Provides song recommendations based on a user's current mood (derived from recent mood records) or a custom mood vector.
    - Leverages an external AI service that uses a vector database to find songs matching a given mood profile.
- **Mood Statistics:** Tracks and displays user mood statistics over time.
- **Database:** Uses SQLAlchemy to interact with a PostgreSQL database (or SQLite for development) to store user information, mood records, and Spotify tokens.
- **Configuration:** Uses Pydantic settings management, allowing configuration via environment variables or a `.env` file.
- **HTTPS:** Supports HTTPS using self-signed SSL certificates for local development.
- **Dockerization:** Includes a `Dockerfile` for containerizing the application.

## Design and Technical Decisions

### Framework and Language

- **Python 3.12:** The application is built using Python, leveraging its extensive ecosystem for web development and data handling.
- **FastAPI:** Chosen for its high performance, ease of use, and automatic data validation and serialization (thanks to Pydantic). It also provides automatic OpenAPI (Swagger) and ReDoc documentation.
- **Uvicorn:** Used as the ASGI server to run the FastAPI application.

### Database

- **SQLAlchemy:** Provides an Object-Relational Mapper (ORM), allowing interaction with the database using Python objects. This abstracts away direct SQL queries and provides a more Pythonic way to manage data.
- **PostgreSQL (Production) / SQLite (Development):** The application is configured to use PostgreSQL, a robust open-source relational database. For simpler local development, it can also be configured to use SQLite.
- **Alembic:** While not explicitly shown in the provided file structure for migrations, Alembic is listed as a dependency, suggesting its intended use for database schema migrations.
- **Models:**
    - `User`: Stores user credentials (email, hashed password), Spotify tokens, and links to their mood records.
    - `MoodRecord`: Stores individual mood entries, including emotional scores (happy, sad, angry, relaxed), optional notes, and a timestamp.

### Authentication and Authorization

- **JWT (JSON Web Tokens):** Used for securing API endpoints. After a user logs in, a JWT is issued and must be included in the `Authorization` header for protected routes.
- **Passlib:** Used for hashing and verifying passwords (specifically bcrypt).
- **OAuth2PasswordBearer:** FastAPI's utility for handling token-based authentication.

### API Structure

- **Modular Routers:** API endpoints are organized into modules (`auth.py`, `mood.py`, `recommendations.py`, `spotify.py`, `users.py`) under `app/api/v1/endpoints/`. This promotes a clean and maintainable codebase.
- **Versioning:** The API is versioned (e.g., `/api/v1/`).
- **Pydantic Schemas:** Used for request and response data validation, serialization, and documentation. Schemas are defined in the `app/schemas/` directory.

### External Service Integration

- **Spotify API:**
    - `spotipy` library is listed as a dependency, though the custom `spotify_client.py` uses `httpx` for direct API calls.
    - Handles OAuth flow for authorization.
    - Fetches recently played tracks.
    - Adds tracks to the user's playback queue.
- **Lyrics API (lyrics.ovh):**
    - `lyrics_client.py` fetches song lyrics using `httpx`.
- **AI Mood Analysis & Recommendation API:**
    - `mood_client.py` interacts with an external AI service (specified by `AI_API_URL` in settings).
    - Sends lyrics to get mood predictions (a vector of emotion probabilities).
    - Sends a mood vector to get song recommendations.

### Configuration

- **Pydantic `BaseSettings`:** Application settings (database URI, API keys, secret keys, CORS origins, etc.) are managed via `app/config.py`.
- **`.env` file:** Settings can be loaded from an `.env` file, allowing for easy environment-specific configuration without modifying code.

### Error Handling

- **Custom HTTP Exceptions:** Defined in `app/utils/errors.py` for common error scenarios like `NotFoundError`, `AuthenticationError`, `AuthorizationError`, etc. This ensures consistent error responses.

### Asynchronous Operations

- **`async` / `await`:** FastAPI and `httpx` are used to perform asynchronous operations, particularly for I/O-bound tasks like making requests to external APIs. This improves the application's ability to handle concurrent requests efficiently.

### SSL/TLS

- **Self-Signed Certificates:** `generate_ssl.sh` script is provided to create `key.pem` and `cert.pem` for running the server over HTTPS locally. The `main.py` and `Dockerfile` are configured to use these files.

### Development and Deployment

- **`pyproject.toml`:** Defines project metadata and dependencies, managed by `uv` (a fast Python package installer and resolver, used in the `Dockerfile`).
- **`Dockerfile`:** Allows building a Docker image for the application, ensuring a consistent runtime environment.
- **`client.py`:** A simple command-line client is provided to interact with the API for testing and demonstration purposes. It handles user registration, login, Spotify connection, and fetching recent tracks.

## Project Structure

```
.
├── cert.pem                  # SSL certificate
├── client.py                 # Example API client
├── Dockerfile                # Docker configuration
├── generate_ssl.sh           # Script to generate SSL certs
├── key.pem                   # SSL private key
├── main.py                   # Main application entry point (runs uvicorn)
├── pyproject.toml            # Project metadata and dependencies
├── uv.lock                   # uv lock file for deterministic builds
├── app/
│   ├── __init__.py           # Initializes the FastAPI app and DB
│   ├── config.py             # Application settings
│   ├── database.py           # Database setup (SQLAlchemy)
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py       # API router aggregation
│   │       └── endpoints/        # API endpoint modules
│   │           ├── auth.py
│   │           ├── mood.py
│   │           ├── recommendations.py
│   │           ├── spotify.py
│   │           └── users.py
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── mood_record.py
│   │   └── user.py
│   ├── schemas/                # Pydantic schemas for data validation
│   │   ├── mood.py
│   │   ├── spotify.py
│   │   ├── token.py
│   │   └── user.py
│   ├── services/               # Business logic and external API clients
│   │   ├── jwt.py              # JWT creation and password hashing
│   │   ├── lyrics_client.py    # Client for lyrics.ovh API
│   │   ├── mood_client.py      # Client for the external AI mood/recommendation API
│   │   └── spotify_client.py   # Client for Spotify API
│   └── utils/
│       └── errors.py           # Custom HTTP exceptions
└── ... (other config files like .gitignore, .python-version)
```

## Setup and Running

### Prerequisites

- Python 3.12+
- `uv` (or `pip`) for installing dependencies
- Access to a PostgreSQL server (or configure for SQLite)
- Spotify Developer App credentials (Client ID, Client Secret, Redirect URI)
- URL for the external AI Mood Analysis & Recommendation API

### Local Development

1.  **Clone the repository.**
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate 
    ```
3.  **Install dependencies:**
    ```bash
    uv pip install -r pyproject.toml
    # or if you only have pip and want to install from pyproject.toml directly (experimental for some pip versions)
    # pip install .
    # or install dev dependencies as well
    # uv pip install -r pyproject.toml --all-extras 
    ```
4.  **Set up environment variables:**
    Create a `.env` file in the root directory with the following content (adjust as needed):
    ```env
    DATABASE_URI="postgresql://user:password@host:port/database_name"
    # For SQLite:
    # DATABASE_URI="sqlite:///./test.db" 

    SECRET_KEY="your-super-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES=10080 # 7 days

    SPOTIFY_CLIENT_ID="your_spotify_client_id"
    SPOTIFY_CLIENT_SECRET="your_spotify_client_secret"
    SPOTIFY_REDIRECT_URI="https://127.0.0.1:8000/api/v1/spotify/callback" # Must match Spotify App settings and server address

    AI_API_URL="your_ai_service_url"

    # Optional: For CORS, if your frontend is on a different origin
    # BACKEND_CORS_ORIGINS="http://localhost:3000,https://your-frontend-domain.com"
    ```
5.  **Generate SSL Certificates:**
    Run the script to generate `key.pem` and `cert.pem`:
    ```bash
    bash generate_ssl.sh
    ```
    *Note: These are self-signed certificates, so your browser or client might show a warning.*
6.  **Run the application:**
    ```bash
    python main.py
    ```
    The API will be available at `https://0.0.0.0:8000` (or `https://localhost:8000`).
    Interactive API documentation (Swagger UI) will be at `https://localhost:8000/docs`.
    Alternative API documentation (ReDoc) will be at `https://localhost:8000/redoc`.

### Running with Docker

1.  **Ensure Docker is installed and running.**
2.  **Set up environment variables:**
    The Docker container will also need the environment variables. You can pass them using the `--env-file` option with `docker run` or configure them in a `docker-compose.yml` file.
    Make sure your `.env` file is ready.
3.  **Build the Docker image:**
    ```bash
    docker build -t music-recommendation-api .
    ```
4.  **Run the Docker container:**
    ```bash
    docker run -d -p 8000:8000 --env-file .env --name music-api music-recommendation-api
    ```
    The API will be available at `https://localhost:8000` (assuming your Docker host is localhost and you have configured SSL appropriately for Docker, or you might need to adjust the `CMD` in `Dockerfile` if not using SSL within the container directly and handling SSL termination externally).

    *Note on SSL with Docker: The current `Dockerfile` copies `cert.pem` and `key.pem` and runs uvicorn with SSL. Ensure these files are present during the build or mount them as volumes if they are generated outside the build context.*

## API Endpoints

(Refer to the `/docs` endpoint when the server is running for a detailed and interactive API specification.)

### Authentication (`/api/v1/auth`)

-   `POST /register`: Register a new user.
-   `POST /login`: Log in and get an access token.

### Users (`/api/v1/users`)

-   `GET /me`: Get current user's profile.
-   `PUT /me`: Update current user's profile.

### Spotify (`/api/v1/spotify`)

-   `GET /auth`: Get the Spotify authorization URL.
-   `GET /callback`: Spotify OAuth callback to exchange code for tokens.
-   `GET /recent-tracks`: Get the user's recently played tracks.

### Mood (`/api/v1/mood`)

-   `POST /record`: Record a new mood entry for the current user.
-   `GET /statistics`: Get mood statistics for the current user.
-   `GET /current`: Get the current average mood for the user based on recent records.

### Recommendations (`/api/v1/recommendations`)

-   `GET /analyze-recent-tracks`: Analyze recently played Spotify tracks to determine and record a mood profile.
-   `GET /get-recommendations`: Get music recommendations based on mood (either current or custom).
-   `POST /queue-song`: Queue a recommended song in the user's Spotify player (requires `track_id`).

## Future Considerations / Potential Improvements

-   **Database Migrations:** Fully implement Alembic for robust schema management.
-   **Testing:** Add comprehensive unit and integration tests (pytest is a dependency, but tests are not shown).
-   **More Sophisticated AI Integration:**
    -   Explore more nuanced mood models.
    -   Allow users to fine-tune recommendations.
-   **Scalability:**
    -   Implement caching strategies (e.g., for lyrics, AI API responses).
    -   Consider asynchronous task queues (e.g., Celery) for long-running processes like mood analysis of many tracks.
-   **Security Enhancements:**
    -   Rate limiting.
    -   More robust input validation.
    -   Regular dependency updates and security audits.
-   **Deployment:**
    -   Set up a proper CI/CD pipeline.
    -   Use a production-grade ASGI server setup (e.g., Uvicorn with Gunicorn workers).
    -   Use managed database services.
    -   Proper SSL certificate management (e.g., Let's Encrypt) instead of self-signed certs for production.
-   **Frontend:** Develop a user interface to interact with the API.
-   **Error Monitoring:** Integrate an error tracking service (e.g., Sentry).
-   **Logging:** Enhance logging for better debugging and monitoring.
