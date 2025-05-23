#! /usr/bin/env fish
docker compose down api
docker image rm final-paper-api
docker compose up -d api
