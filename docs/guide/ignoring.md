# Ignoring songs, albums, artists and playlists

Spotisub writes what it matches. When you disagree with a match (or want something out
of the way for good), **ignore** it instead of deleting it in the music server — a
deleted track comes back on the next import.

Ignore exists at four levels, from narrowest to broadest:

| Level | Where | Effect |
|---|---|---|
| **Relation** | Playlist detail row | Excluded from that one playlist |
| **Song** | Song page | Excluded from every playlist |
| **Album** | Album page | Every track of the album, everywhere |
| **Artist** | Artist page | Every track by the artist, everywhere |
| **Playlist** | Playlist toolbar | The playlist is no longer written or refreshed |

## How to ignore something

1. Open the playlist, then click the track to reach the song page (or click the artist /
   album name).
2. Press the **ignore** button in the toolbar. It toggles; press again to un-ignore.

The dashboard then shows the grey half-circle (ignored somewhere) or the ban icon
(ignored everywhere), so you can tell a deliberate exclusion from a genuine miss.

## Why ignoring beats deleting

- Deleting the track in Navidrome/Subsonic makes it *missing*, not *ignored*: Spotisub
  will keep reporting it and, with [spotdl](../integrations/spotdl.md) enabled, may even
  download it again.
- Ignored items stay in the database, so your decision survives rescans, restarts and
  cache rebuilds.
- If a track is ignored because it is a live version you dislike but the album version is
  fine, ignore the **song**, not the album.

## Un-ignoring

Same button, opposite state. Then rescan the affected playlist — ignore flags are
applied at import time, so a change does not rewrite an existing Subsonic playlist until
the next import.

## Ignoring a whole playlist

Useful for playlists you follow but never listen to (a friend's 400-track dump, a
"discover weekly" archive). On the playlist page press **Ignore playlist**: the existing
Subsonic playlist is left as it is and the job stops refreshing it.

!!! tip "Followed playlists you cannot read"

    A playlist that Spotify returns 403 for is skipped automatically during import; the
    rest of your import continues. You do not need to ignore those.

## Limitations

- There is no artist allow-list yet: excluding "everything by this artist" means opening
  the artist page once. If you want a bulk editor, that is issue
  [#74](https://github.com/blastbeng/spotisub/issues/74) upstream.
- Ignore flags are per item, not per playlist *track position*: the same track twice in
  one playlist shares one relation.
