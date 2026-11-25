# FAQ

## Does Spotisub need Spotify Premium?

Yes. Spotify's [February 2026 developer
policy](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security)
requires the account that owns the app to have Premium: a free account gets the
application blocked from the Web API with `403`, whatever scopes it asks for. The scopes
Spotisub uses are read-only, so this is Spotify's rule for every third-party client, not
a Spotisub limitation. [spotdl](../integrations/spotdl.md) needs Premium on top of that,
because it uses Spotify's streaming endpoints.

## Does it modify my Spotify account?

No. It only reads (`playlist-read-private`, `user-library-read`, `user-top-read`,
`user-read-recently-played`). It never creates, edits or unfollows anything on Spotify.

## Can two people use it, with different Spotify accounts?

No. Spotisub is single-tenant: one local web account, one Spotify account, one Subsonic
account. Multi-user is an open feature request upstream and needs a scheduler redesign.

## Does it delete my music files?

Never. It only creates/updates playlists through the Subsonic API. The one exception is
[spotdl](../integrations/spotdl.md) **writing** new files; it does not delete anything
either.

## Why is only one of my playlists updated every few hours?

The `user_playlists` job imports one playlist per interval, on purpose, to stay under
Spotify's rate limits. See
[the scheduler](../configuration/scheduler.md#one-random-playlist-per-interval-read-this).
Use **Rescan → all playlists** when you want everything now.

## Why are recommendation playlists missing?

Spotify shut down the `/recommendations` API in December 2024. The feature cannot work
any more; the code paths are disabled, not removed. Artist top tracks and your own
playlists are unaffected.

## Why is a track that exists in my library reported as missing?

Because matching is by MBID first, and text comparison is opt-in. See
[Missing tracks](../guide/missing-tracks.md) — in most libraries the files simply lack the
`musicBrainzId` tag.

## Can I change the playlist prefix?

Yes: `PLAYLIST_PREFIX`, default `Spotisub - `. Changing it does not rename playlists that
already exist; it affects newly created ones. Empty means no prefix, which makes the
playlists indistinguishable from hand-made ones — not recommended.

## Can I use it with Airsonic / Gonic / Astiga?

Yes, anything with the Subsonic API and writable playlists. Set host, port, base path and
credentials accordingly.

## Does it support M3U export instead of the API?

No. Playlists are created through the Subsonic API only.

## Where does the version come from?

`spotisub/database.py` (`VERSION`). The startup banner prints it. Image tags and the
[release history](../release-history.md) follow the same number.

## How do I reset everything?

Stop the container, delete `cache/`, start it again. You will register a new local
account and reconnect Spotify. [Data and cache](../guide/data-and-cache.md) explains what
you lose (match history, not music).

## Is there a settings page?

No. Everything is environment variables
([reference](../configuration/environment-variables.md)). A dashboard-based configuration
is a planned feature upstream.

## How do I back it up?

Back up `cache/` and `.env`. That is the whole state —
[Data and cache](../guide/data-and-cache.md).

## Can I run it without Docker?

Yes, with Python 3.10 and a virtualenv: [Run without Docker](../getting-started/no-docker.md).

## Which ports does it need?

Inbound: `5183` for the web interface. Outbound: HTTPS to `api.spotify.com`,
`accounts.spotify.com` and `musicbrainz.org`, plus your Subsonic server.

## Does it work with a self-hosted Spotify alternative?

No. The source of truth for the input playlists is Spotify.
