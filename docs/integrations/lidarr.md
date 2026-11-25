# Lidarr

Lidarr is a music collection manager. The integration does one thing: it answers *"do I
want this artist?"* before [spotdl](spotdl.md) downloads a missing track.

Without Lidarr, every unmatched track gets downloaded. With Lidarr, a track is only
downloaded when its artist is **monitored** in Lidarr — which is how you say "download
the artists I collect, skip the ones I do not".

## Requirements

- [spotdl](spotdl.md) enabled. Lidarr alone changes nothing: it only gates downloads.
- Lidarr reachable from the Spotisub container, with an API key.

## Configuration

```ini
LIDARR_ENABLED=1
LIDARR_IP=lidarr                # host or IP, no scheme
LIDARR_PORT=8686
LIDARR_TOKEN=your-api-key       # Lidarr > Settings > General > Security
LIDARR_BASE_API_PATH=           # only for a Lidarr behind a path prefix
LIDARR_USE_SSL=0                # 1 for HTTPS
```

The API key lives in Lidarr under **Settings → General → Security → API Key**.

## How the decision is made

For each missing track, Spotisub asks Lidarr for its artist list (cached for an hour,
one request for the whole import) and compares the Spotify artist name with the Lidarr
artist name using the same normalisation as text matching.

- Artist found **and monitored** → the track is queued for spotdl.
- Artist found but **not monitored** → skipped, with a log line.
- Artist **not in Lidarr at all** → skipped, with a log line.

So the way to exclude an artist permanently is to leave it unmonitored in Lidarr, not to
ignore it in Spotisub.

## What it does not do

- It does not add artists to Lidarr, or trigger Lidarr searches.
- It does not sync Lidarr's library into Subsonic.
- It does not look at albums or tracks, only artists.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Every track skipped, log says "hasn't been found in your Lidarr database" | `LIDARR_IP`/`LIDARR_PORT` unreachable from the container, or the name differs between Spotify and Lidarr |
| `LIDARR_ENABLED is set but LIDARR_IP and LIDARR_PORT are required` at startup | Missing configuration; the client is built on first use, so the message appears on the first download attempt |
| HTTPS errors | `LIDARR_USE_SSL=1` for `https://`, `0` for `http://` |
