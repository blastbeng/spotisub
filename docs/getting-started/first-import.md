# 4. Import your first playlist

By now Spotisub should know about Spotify and about your library. Importing is a
background job: the browser only starts it and then reports progress.

## What happens automatically

On the first start Spotisub scans your library and creates empty playlist rows:

- one playlist per Spotify playlist you own or follow that it can read,
- one playlist with all your **Liked Songs**,
- optionally one "Top Tracks" playlist per artist (only with
  `ARTIST_PLAYLIST_ENABLED=1`).

The rows are created empty on purpose: importing thousands of tracks during boot would
block the interface. **Rescan** fills them.

## Import

1. Open the dashboard (`/overview/`).
2. Press the **Rescan** button (the circular arrow in the playlist toolbar).
3. Confirm. Choose *This playlist* or *All playlists*.
4. Watch **System → Tasks**: the job appears with `running = 1` while it works, and
   **System → Logs** streams what it is doing.
5. When the job finishes, open the playlist row.

The first full import is the slow one: Spotisub asks MusicBrainz for one ISRC at a time
and waits about a quarter of a second between Spotify calls to stay inside rate limits.
A few thousand tracks can take several minutes. Later imports are incremental and much
faster.

!!! tip "Small first test"

    If you have a large library, rescan a single small playlist first. It proves the
    credentials, the matching and the playlist writing before you commit an hour to a
    full import.

## Reading the result

A playlist page shows one row per Spotify track and a status icon:

| Icon | Meaning |
|---|---|
| :material-check-box: green check | Matched to a track in your library |
| :material-alert: warning triangle | Missing — no track in your library matched |
| :material-minus-circle: | Ignored in *some* playlists |
| :material-cancel: ban | Ignored everywhere |

Open the playlist in your music server: it has the same name, prefixed with
`Spotisub - ` (configurable with `PLAYLIST_PREFIX`).

!!! warning "Empty playlist in the server?"

    A Subsonic playlist with **zero** matched tracks is deleted again instead of being
    created empty. If the whole playlist is empty, the problem is matching, not
    playlist writing — start at [Missing tracks](../guide/missing-tracks.md).

## Keep it fresh

With `SCHEDULER_ENABLED=1` (the default) Spotisub re-imports on its own:

| Job | Default interval |
|---|---|
| Saved tracks | every 2 hours |
| Your Spotify playlists | every 3 hours |
| Artist top tracks *(optional)* | every 1 hour |

Change the intervals, or disable a job with `0`, in
[the scheduler configuration](../configuration/scheduler.md).

## Next

- Learn the interface: [The dashboard](../guide/dashboard.md)
- Fix unmatched tracks: [Missing tracks](../guide/missing-tracks.md)
- Automate downloads: [spotdl](../integrations/spotdl.md)
