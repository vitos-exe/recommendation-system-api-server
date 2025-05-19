import json
import os
import ssl

import httpx

ssl._create_default_https_context = ssl._create_unverified_context

# Configuration
BASE_URL = "https://127.0.0.1:8000/api/v1"
# Assuming client.py is in the same directory as cert.pem
CERT_PATH = "./cert.pem"


def register_user(client: httpx.Client, email: str, password: str) -> str | None:
    """Registers a new user and returns the API access token."""
    print(f"Attempting to register user {email}...")
    try:
        response = client.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password},
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        print("Registration successful.")
        return data.get("access_token")
    except httpx.HTTPStatusError as e:
        print(
            f"Error during registration: {e.response.status_code} - {e.response.text}"
        )
    except httpx.RequestError as e:
        print(f"Request error during registration: {e}")
    return None


def login_user(client: httpx.Client, email: str, password: str) -> str | None:
    """Logs in an existing user and returns the API access token."""
    print(f"Attempting to login user {email}...")
    try:
        response = client.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": email,
                "password": password,
            },  # OAuth2PasswordRequestForm expects form data
        )
        response.raise_for_status()
        data = response.json()
        print("Login successful.")
        return data.get("access_token")
    except httpx.HTTPStatusError as e:
        print(f"Error during login: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"Request error during login: {e}")
    return None


def get_spotify_auth_details(
    client: httpx.Client, api_token: str
) -> tuple[str | None, str | None]:
    """Gets the Spotify authorization URL and state from the API."""
    print("Fetching Spotify authorization URL...")
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = client.get(f"{BASE_URL}/spotify/auth", headers=headers)
        response.raise_for_status()
        data = response.json()
        auth_url = data.get("auth_url")
        state = data.get("state")
        if auth_url and state:
            print("Spotify auth details received.")
            return auth_url, state
        else:
            print("Could not retrieve Spotify auth URL or state from response.")
            return None, None
    except httpx.HTTPStatusError as e:
        print(
            f"Error fetching Spotify auth URL: {e.response.status_code} - {e.response.text}"
        )
    except httpx.RequestError as e:
        print(f"Request error fetching Spotify auth URL: {e}")
    return None, None


def call_spotify_callback(client: httpx.Client, api_token: str, code: str, state: str):
    """Calls the Spotify callback endpoint with the code and state."""
    print("Sending code and state to Spotify callback...")
    headers = {"Authorization": f"Bearer {api_token}"}
    params = {"code": code, "state": state}
    try:
        response = client.get(
            f"{BASE_URL}/spotify/callback", headers=headers, params=params
        )
        response.raise_for_status()
        print("Spotify callback successful:", response.json().get("message"))
    except httpx.HTTPStatusError as e:
        print(
            f"Error during Spotify callback: {e.response.status_code} - {e.response.text}"
        )
    except httpx.RequestError as e:
        print(f"Request error during Spotify callback: {e}")


def get_recent_tracks(client: httpx.Client, api_token: str, limit: int = 10):
    """Fetches the user's recently played tracks from Spotify via the API."""
    print(f"Fetching last {limit} recent tracks...")
    headers = {"Authorization": f"Bearer {api_token}"}
    params = {"limit": limit}
    try:
        response = client.get(
            f"{BASE_URL}/spotify/recent-tracks", headers=headers, params=params
        )
        response.raise_for_status()
        tracks = response.json()
        print("Recent tracks:")
        if tracks:
            for i, track in enumerate(tracks):
                print(f"  {i + 1}. {track.get('name')} by {track.get('artist')}")
        else:
            print("  No tracks found or an empty list was returned.")
    except httpx.HTTPStatusError as e:
        print(
            f"Error fetching recent tracks: {e.response.status_code} - {e.response.text}"
        )
    except httpx.RequestError as e:
        print(f"Request error fetching recent tracks: {e}")
    except json.JSONDecodeError:
        print(
            f"Error decoding JSON from recent tracks response. Raw response: {response.text}"
        )


def main():
    # Create an httpx client that trusts the self-signed certificate
    # If CERT_PATH is not found or invalid, requests will fail.
    # For quick testing without proper cert handling, you could use verify=False,
    # but this is insecure and not recommended for anything beyond trivial local tests.
    context = httpx.create_ssl_context(verify=False)

    with httpx.Client(verify=context) as client:
        api_token = None
        user_email = input("Enter your email: ")
        user_password = input("Enter your password: ")

        action = input("Do you want to (r)egister or (l)ogin? ").lower()
        if action == "r":
            api_token = register_user(client, user_email, user_password)
        elif action == "l":
            api_token = login_user(client, user_email, user_password)
        else:
            print("Invalid action. Exiting.")
            return

        if not api_token:
            print("Could not get API token. Exiting.")
            return

        print(f"API Token: {api_token[:15]}...")  # Print a snippet for confirmation

        if input("Do you want to connect to Spotify? (y/n) ").lower() == "y":
            auth_url, spotify_state = get_spotify_auth_details(client, api_token)
            if auth_url and spotify_state:
                print("\\n--- Spotify Authorization Needed ---")
                print(f"1. Open this URL in your browser: {auth_url}")
                print("2. Authorize the application with Spotify.")
                print(
                    "3. After Spotify redirects you, copy the 'code' and 'state' from your browser's address bar."
                )
                print(
                    "   The redirect URL will look like: https://127.0.0.1:8000/api/v1/spotify/callback?code=YOUR_CODE&state=YOUR_STATE"
                )

                spotify_code = input("Enter the 'code' from the redirect URL: ")
                # The state from the redirect URL should match the one we got earlier.
                # For simplicity, we're asking the user to input it, but you could also
                # just use the `spotify_state` variable we already have if you trust the user
                # or if the API validates it strictly (which it should).
                user_provided_state = input(
                    f"Enter the 'state' from the redirect URL (should be {spotify_state}): "
                )

                if user_provided_state != spotify_state:
                    print(
                        "Warning: The state you entered does not match the expected state. Proceeding anyway."
                    )

                call_spotify_callback(
                    client, api_token, spotify_code, user_provided_state
                )  # Use user_provided_state or spotify_state

        if input("Do you want to fetch recent Spotify tracks? (y/n) ").lower() == "y":
            get_recent_tracks(client, api_token)

        print("\\nClient finished.")


if __name__ == "__main__":
    if not os.path.exists(CERT_PATH):
        print(f"Error: Certificate file not found at {CERT_PATH}")
        print("Please ensure 'cert.pem' is in the same directory as this script.")
        print("You can generate 'key.pem' and 'cert.pem' using OpenSSL:")
        print(
            "openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365"
        )
    else:
        main()
