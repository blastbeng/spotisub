# 1. Create a Spotify app

Spotify only lets a third-party program read your playlists if it authenticates as an
application that **you** own. Creating the application costs nothing and takes a couple
of minutes — but since Spotify's February 2026 developer policy the account that owns it
must have **Spotify Premium**, otherwise the app is blocked from the Web API with `403`.
You will end up with two values:

- a **Client ID**
- a **Client Secret**

Keep the secret private. It is stored in your `.env` file and never leaves your machine.

## Step by step

1. Go to <https://developer.spotify.com/dashboard> and log in with your normal Spotify
   account. Accept the developer terms the first time.
2. Click **Create app**.
3. Fill in:
   - **App name** — anything, for example `Spotisub`.
   - **App description** — anything, for example `Personal playlist importer`.
   - **Website** — can be left empty.
   - **Redirect URI** — this one matters, see below.
   - **Which API/SDKs are you planning to use?** — tick **Web API**.
4. Save, then open the app and click **Settings** to see **Client ID** and
   **Client Secret** (click *View client secret*).

## The redirect URI

The redirect URI is where Spotify sends you back after you approve access. It must match
your `SPOTIPY_REDIRECT_URI` **character for character** — same scheme, same host, same
port, same path, trailing slash included or excluded exactly as configured.

With the default Docker setup, Spotisub listens on port `5183` and its callback route is
`/callback`, so register:

```text
http://127.0.0.1:5183/callback
```

Those are the values used in the shipped `.env.sample`:

```ini
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5183/callback
```

!!! warning "Only `http://127.0.0.1` is exempt from HTTPS"

    Spotify accepts plain `http://` only for loopback addresses (`127.0.0.1` and
    `localhost`). If Spotisub lives on another machine, behind a domain, or behind a
    reverse proxy, the redirect URI must be `https://` and must be reachable from the
    browser you use — not just from the server.

    Example for a proxied install at `https://music.example.com/spotisub/`:

    ```text
    https://music.example.com/spotisub/callback
    ```

    and in `.env`:

    ```ini
    SPOTIPY_REDIRECT_URI=https://music.example.com/spotisub/callback
    ```

    See [Reverse proxy](../configuration/reverse-proxy.md) for the `APPLICATION_ROOT`
    part of that setup.

## What creates the token

After the app exists, Spotisub completes the OAuth flow itself when you press
**Connect Spotify** in the web interface, and stores the resulting token in
`cache/spotipy_cache`. There is nothing else to configure and no separate script to run.

!!! note "Legacy: `first_run.sh`"

    Older instructions told you to run `docker exec -it spotisub ./first_run.sh` to
    paste an OAuth URL by hand. That script still exists for headless installs, but the
    in-app **Connect Spotify** button is the supported path and does the same thing with
    fewer steps.

## Next

[:octicons-arrow-right-24: 2. Install with Docker](docker.md)
