# Playlists overview

There are three list pages. All of them are in the sidebar under **Playlists**:

| Sidebar entry | URL | Shows |
|---|---|---|
| **Playlists → Overview** | `/overview/` | One row per playlist, with counts |
| **Playlists → Manage** | `/playlists/0/` | One row per **track**, across all playlists |
| **Playlists → Missing** | `/playlists/1/` | The same list, filtered to **unmatched** tracks |

The track views are where you work when something is missing: they show the Spotify
title, artist and album next to the match status, and let you search across everything.

## Status icons

| Icon | Meaning |
|---|---|
| :material-check-box: green check | Matched: the track exists in your library and is in the playlist |
| :material-alert: orange triangle | **Missing**: no library track matched |
| :material-minus-circle: grey circle | Ignored in some playlists |
| :material-cancel: ban | Ignored in every playlist |
| :material-battery-empty: battery | The playlist is empty (no track matched at all) |

"Missing" has one precise definition in the database: no Subsonic song id **and** no
Subsonic artist id recorded for that Spotify track in that playlist.

## Toolbar

The toolbar is the same on every page; only the relevant buttons are shown.

- **Search** — filters the current list by title. Matching is a substring search on the
  Spotify song title (and, on the track pages, artist/album too).
- **Filter** — show only missing tracks, hide empty playlists, and similar toggles.
- **Sort** — click any column header to sort, click again to reverse.
- **View** — switch between table and poster layout.
- **Rows per page** — 25, 50, 100, 250, 500.

The page size and sort order are encoded in the URL (`/playlists/1/2/100/spotify_song.title/1/`),
so a filtered view can be bookmarked or shared.

## Pagination

There is no infinite scroll on the track pages: use the page selector. Deep pages on a
very large library are normal — the Missing page for a 30 000-track library can be
hundreds of pages long, which is exactly why
[fixing matching](missing-tracks.md) matters more than clicking through it.
