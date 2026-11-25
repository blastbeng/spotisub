# Playlist detail

Opening a playlist from the dashboard shows one row per Spotify track in it, with:

- the Spotify title, artist and album (each clickable),
- the matched Subsonic track, or an orange *missing* marker,
- the ignore state for this playlist,
- a download button when [spotdl](../integrations/spotdl.md) is enabled.

## What the toolbar does here

| Button | Effect |
|---|---|
| :material-refresh: **Rescan and reimport** | Re-read the Spotify playlist and rewrite the Subsonic one |
| :material-eye-off: **Ignore / un-ignore playlist** | Skip this playlist in every future import |
| **Filter / Sort / View** | Same as everywhere else |
| :material-download: **Download** (per row) | Send that track to spotdl |

The ignore button toggles. A playlist marked ignored keeps its existing Subsonic
playlist but is not rewritten any more.

## Drill-down: song, album, artist

Clicking a track opens the **song** page; clicking an artist or album name opens the
artist/album page. Each of them lists every playlist where that item appears, which is
how you answer questions like:

- *"I ignore this song but it keeps coming back"* → check which playlists still include
  it and ignore it in each one.
- *"Which of my Spotify playlists contain this album?"* → the album page.

Every song, album and artist page has its own ignore toggle, and ignoring an album or an
artist is stronger than ignoring a song: it applies everywhere.

## Why a playlist on the server differs from Spotify

Some differences are expected and permanent:

1. **Duplicates** — Spotify playlists can contain the same track twice; a Subsonic
   playlist cannot, so the duplicate is dropped.
2. **Missing tracks** — anything not in your library is not written.
3. **Ignored tracks** — your own exclusions.
4. **Podcasts** — Spotify episodes are skipped; Spotisub only handles music tracks.
5. **Ordering** — matched tracks are appended in Spotify order, but re-importing an
   existing playlist can reorder it. Do not hand-edit a Spotisub-managed playlist: the
   next import overwrites it.

## Zero matches

If nothing matched, the Subsonic playlist is **deleted** rather than left empty. The
playlist row stays in the dashboard so you can fix the cause and rescan. See
[Missing tracks](missing-tracks.md).
