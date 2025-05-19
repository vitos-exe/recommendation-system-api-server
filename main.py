import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug",
        ssl_keyfile="./key.pem",  # Path to your key file
        ssl_certfile="./cert.pem",  # Path to your certificate file
    )
