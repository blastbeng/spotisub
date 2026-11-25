# spotdl: automatic downloads

With spotdl enabled, a track that Spotisub **cannot find** in your library is downloaded
from Spotify into your music folder, so that after your server's next scan the playlist
is complete.

It is off by default because it writes to your music library and because it needs a
Spotify Premium account.

## Requirements

1. **Spotify Premium** on the account whose app credentials you use. The download path
   uses Spotify's streaming endpoints; free accounts get HTTP 403.
2. **Your music folder mounted into the container** — Spotisub cannot write to a folder
   it does not see.
3. `ffmpeg` — already installed in the official image.
4. Enough disk space, and a music server that rescans that folder.

## Configuration

```yaml
  spotisub:
    volumes:
      - "./cache:/home/user/spotisub/cache"
      - "/music:/music"                 # must be writable, no :ro
    environment:
      - SPOTDL_ENABLED=1
      - SPOTDL_FORMAT=/music/{artist}/{artists} - {album} ({year}) - {track-number} - {title}.{output-ext}
```

| Variable | Meaning |
|---|---|
| `SPOTDL_ENABLED` | `1` turns automatic downloads on |
| `SPOTDL_FORMAT` | Output path **template**, absolute, starting with the mounted music path |

Placeholders (`{artist}`, `{artists}`, `{album}`, `{year}`, `{track-number}`, `{title}`,
`{output-ext}`, ...) are documented upstream in the
[spotdl usage guide](https://spotdl.github.io/spotify-downloader/usage/).

!!! warning "`SPOTDL_FORMAT` is a path, not a file extension setting"

    The container writes exactly to the path the template produces. If it does not start
    with your mounted music folder, the download "succeeds" outside the library and
    nothing appears in your server.

## When a download happens

Only during an import, and only for tracks that:

- were **not** matched (MBID or text comparison),
- were **not** excluded or ignored,
- have a Spotify URL,
- and, if [Lidarr](lidarr.md) is enabled, belong to an artist you monitor there.

Downloads run on a **single-worker queue**: one at a time, in the background, while the
import continues. A large backlog drains slowly; that is intentional (yt-dlp and Spotify
both dislike bursts).

There is also a manual **Download** button on each missing track in the playlist view.

## What happens afterwards

Nothing automatic inside Spotisub:

1. spotdl writes the file(s) to your music folder,
2. your server scans them (Navidrome with `ND_SCANSCHEDULE` does this on a timer),
3. Spotisub's library index becomes stale and is rebuilt on the next import,
4. the next import of that playlist matches the track.

Until step 4 the track still shows as missing. That is expected.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `403` from Spotify during download | The account is not Premium |
| Download "succeeds" but no file in the library | `SPOTDL_FORMAT` points outside the mounted folder |
| Files appear, playlists do not | The server has not scanned; then rescan the playlist |
| Download fails with a Python/yt-dlp traceback | spotdl and yt-dlp move fast; check the log line and the upstream issue tracker |
| Wrong versions/metadata | spotdl matches by search; a different release can be picked |

!!! note "Python version"

    The official image runs Python 3.10. Recent yt-dlp releases (used by spotdl) have
    started warning about, and in some versions refusing, 3.10. If the log shows a
    `Deprecated Feature: Support for Python version 3.10` error, spotdl cannot run in that
    image — pin an older `spotdl`/`yt-dlp`, or run Spotisub from source on a newer Python.
    The rest of Spotisub is unaffected: the spotdl client is only loaded when a download
    is attempted.

## Disabling again

Set `SPOTDL_ENABLED=0` and recreate the container. Nothing is deleted; already
downloaded tracks stay in your library.
