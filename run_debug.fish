#!/usr/bin/env fish
uvicorn app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level debug \
    --ssl-keyfile ./localhost-key.pem \
    --ssl-certfile ./localhost.pem
