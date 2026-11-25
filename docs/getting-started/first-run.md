# 3. Log in to Spotify

Open <http://127.0.0.1:5183/> (or your own URL). On a fresh install Spotisub sends you
straight to **Create Spotisub credentials**.

## A local account first

Spotisub protects its web interface with one local account. This account has nothing to
do with Spotify: it only stops other people on your network from using your instance.

1. Choose a username and a password, submit.
2. Log in with those credentials.

The password is stored hashed in `cache/spotisub.db`. There is exactly **one** account;
registering again is refused ([multi-user is not supported yet](../help/faq.md)).

!!! danger "Never expose Spotisub to the internet with `LOGIN_DISABLED=1`"

    `LOGIN_DISABLED=1` turns authentication off entirely. It exists for local UI work.
    See [Login and security](../configuration/security.md).

## Then connect Spotify

1. In the sidebar, click :fontawesome-brands-spotify: **Authenticate Spotify**.
2. A new tab opens on `accounts.spotify.com` asking you to allow your own Spotify app to
   *read your library, your playlists and your listening data*.
3. Approve. Spotify redirects back to `…/callback`, Spotisub stores the token in
   `cache/spotipy_cache`, and the tab can be closed.

That is the whole flow. The token refreshes itself from then on; you only repeat this if
you revoke the app in Spotify or delete the `cache/` folder.

### If the tab shows "INVALID_CLIENT: Invalid redirect URI"

The URI in `.env` (`SPOTIPY_REDIRECT_URI`) and the one registered in your Spotify app
differ. Copy the exact value from `.env` into
<https://developer.spotify.com/dashboard> → your app → **Settings** → **Redirect URIs**
and save. No restart is needed for the Spotify side; restart Spotisub after editing
`.env`:

```bash
docker compose up -d --force-recreate
```

More cases: [Troubleshooting](../help/troubleshooting.md).

### If the tab shows "redirect_uri: Not matching configuration"

Same cause, other direction: you registered `http://127.0.0.1:5183/callback` in Spotify
but set `SPOTIPY_REDIRECT_URI` to something else (a trailing slash is a difference).
They must be identical strings.

## Optional: headless seeding with `first_run.sh`

On a server with no browser you can seed the token from a terminal. Spotisub prints a
URL, you open it **on any machine**, approve, and paste the resulting
`http://127.0.0.1:5183/callback?code=…` URL back:

```bash
docker exec -it spotisub ./first_run.sh
```

This writes the same `cache/spotipy_cache` file. It is a fallback; the button is the
normal path.

## Check that everything is connected

Sidebar → **Check Subsonic** should report a working connection. If it does not, fix
that before importing anything: see [Troubleshooting](../help/troubleshooting.md).

## Next

[:octicons-arrow-right-24: 4. Import your first playlist](first-import.md)
