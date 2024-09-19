#!/bin/bash

while true; do
    echo -e "Please input an install directory:"
    read WORKDIR
    if [[ "$WORKDIR"  != "" ]]; then
        mkdir -p "$WORKDIR"
        if [ -z "$( ls -A "$WORKDIR" )" ]; then
            mkdir -p "$WORKDIR/cache"
            break
        else
            echo "$WORKDIR is not empty. Please specify an empty dir."
        fi
    fi
done

while true; do
    echo -e "Please input your Spotify Client ID:"
    read SPOTIFY_CLIENT_ID
    if [[ "$SPOTIFY_CLIENT_ID" != "" ]]; then
        break
    fi
done

while true; do
    echo -e "Please input your Spotify Client Secret:"
    read -s SPOTIFY_CLIENT_SECRET
    if [[ "$SPOTIFY_CLIENT_SECRET" != "" ]]; then
        break
    fi
done


echo -e "Please input your Subsonic Address. Leave blank for default (http://127.0.0.1):"
read SUBSONIC_API_HOST
if [[ "$SUBSONIC_API_HOST" == "" ]]; then
    SUBSONIC_API_HOST="http://127.0.0.1"
fi

echo -e "Please input your Subsonic Port. Leave blank for default (4533):"
read SUBSONIC_API_PORT
if [[ "$SUBSONIC_API_PORT" == "" ]]; then
    SUBSONIC_API_PORT="4533"
fi

echo -e "Please input your Subsonic Path (Leave blank for default: Empty):"
read SUBSONIC_API_BASE_URL


while true; do
    echo -e "Please input your Subsonic Username:"
    read SUBSONIC_API_USER
    if [[ "$SUBSONIC_API_USER" != "" ]]; then
        break
    fi
done

while true; do
    echo -e "Please input your Subsonic Password:"
    read -s SUBSONIC_API_PASS
    if [[ "$SUBSONIC_API_PASS" != "" ]]; then
        break
    fi
done

echo "name: spotisub" >> "${WORKDIR}/docker-compose.yml"
echo "services:" >> "${WORKDIR}/docker-compose.yml"
echo "  spotisub:" >> "${WORKDIR}/docker-compose.yml"
echo "    container_name: spotisub" >> "${WORKDIR}/docker-compose.yml"
echo "    environment:" >> "${WORKDIR}/docker-compose.yml"
echo "      - SPOTIPY_CLIENT_ID=${SPOTIFY_CLIENT_ID}" >> "${WORKDIR}/docker-compose.yml"
echo "      - SPOTIPY_CLIENT_SECRET=${SPOTIFY_CLIENT_SECRET}" >> "${WORKDIR}/docker-compose.yml"
echo "      - SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080" >> "${WORKDIR}/docker-compose.yml"
echo "      - SUBSONIC_API_HOST=${SUBSONIC_API_HOST}" >> "${WORKDIR}/docker-compose.yml"
echo "      - SUBSONIC_API_PORT=${SUBSONIC_API_PORT}" >> "${WORKDIR}/docker-compose.yml"

if [[ "$SUBSONIC_API_BASE_URL" != "" ]]; then
    echo "      - SUBSONIC_API_BASE_URL=${SUBSONIC_API_BASE_URL}" >> "${WORKDIR}/docker-compose.yml"
fi

echo "      - SUBSONIC_API_USER=${SUBSONIC_API_USER}" >> "${WORKDIR}/docker-compose.yml"
echo "      - SUBSONIC_API_PASS=${SUBSONIC_API_PASS}" >> "${WORKDIR}/docker-compose.yml"
echo "    image: "blastbeng/spotisub:latest"" >> "${WORKDIR}/docker-compose.yml"
echo "    restart: always" >> "${WORKDIR}/docker-compose.yml"
echo "    volumes:" >> "${WORKDIR}/docker-compose.yml"
echo "      - "./cache:/home/user/spotisub/cache"" >> "${WORKDIR}/docker-compose.yml"
echo "    ports:" >> "${WORKDIR}/docker-compose.yml"
echo "      - \"5183:5183\"" >> "${WORKDIR}/docker-compose.yml"
echo "    healthcheck:" >> "${WORKDIR}/docker-compose.yml"
echo "      test: [\"CMD\", \"curl\", \"-f\", \"http://127.0.0.1:5183/utils/healthcheck\"]" >> "${WORKDIR}/docker-compose.yml"
echo "      interval: 15s" >> "${WORKDIR}/docker-compose.yml"
echo "      timeout: 5s" >> "${WORKDIR}/docker-compose.yml"
echo "      retries: 12" >> "${WORKDIR}/docker-compose.yml"

cd "$WORKDIR"

docker compose up -d
docker exec -it spotisub ./first_run.sh
docker compose down

echo "Spotisub has been initialized, you can now start the container by going to ${WORKDIR} and executing 'docker compose up'"