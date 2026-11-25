# How matching works

Spotisub decides whether a Spotify track exists in your library in one of two ways:
**MBID matching** (precise, default) and **text comparison** (fuzzy, opt-in).

## The pipeline

For every track in a Spotify playlist:

1. **Fill in metadata.** Spotify's playlist payload omits the album and the ISRC, so
   Spotisub fetches each track's full object (cached in
   `cache/spotify_object_cache.pkl`). Podcast episodes are skipped.
2. **ISRC → MBID.** Spotify tracks carry an [ISRC](https://musicbrainz.org/doc/ISRC)
   but never an MBID. Spotisub asks MusicBrainz to translate ISRC → recording MBID(s).
   MusicBrainz's ISRC coverage is incomplete; some tracks return nothing.
3. **MBID → library track.** The library is indexed once into
   `cache/subsonic_cache.pkl` as `musicBrainzId → song`. A hit means an exact match and
   the track is added.
4. **Text comparison** *(only if `TEXT_COMAPRE_MATCHING_ENABLED=1` and step 3 missed)*.
   Search the library for the title, then compare title and artist after
   normalisation: lowercase, strip punctuation, and split on `(`, `-` and `feat`, so that
   `Song (Live)`, `Song - Remastered 2011` and `Song feat. X` all reduce to `Song`.
   The first surviving candidate wins.
5. **Exclusions.** `EXCLUDED_WORDS` is applied to the *candidate's* title and album
   **only in the text-comparison path**. MBID matches are never rejected by an excluded
   word.
6. **Persist.** Every outcome is written to `cache/spotisub.db`, matched or missing, then
   the playlist is (re)written with the matched song ids.

## Why MBID first

- It is exact: no confusion between a studio track and its live version.
- It is cheap for the library: one index, many comparisons.
- It is stable across metadata clean-ups.

Its weakness is that it needs the `musicBrainzId` tag in your files, and the ISRC in
MusicBrainz. Missing tags mean missing matches, silently.

## Why text comparison is opt-in

A wrong match is worse than a missing track: it puts the live version in your playlist
and nobody notices until they listen. Enable it per problem library, not by default.

If you enable it, also review the [Missing page](missing-tracks.md) afterwards — tracks
that *used to be* missing will be gone from that page whether the match was right or
wrong.

## What is cached, and when it is invalidated

| File | Contents | Invalidated by |
|---|---|---|
| `spotify_object_cache.pkl` | Full Spotify track objects (album, ISRC, URI) | Entries expire after 12 hours; the file is rewritten as it is used |
| `subsonic_cache.pkl` | `musicBrainzId → song` index of your library | Library song count changing (`is_subsonic_cache_stale`) |
| `spotisub.db` | Playlists, songs, artists, albums, relations, ignore flags | Nothing; it is the source of truth |

The library index is rebuilt automatically when your server reports a different song
count. Adding one album is enough to trigger it.

## Rate limits are deliberate

`time.sleep(0.25)` after each Spotify object fetch and `time.sleep(2)` between pages
exist to stay under Spotify's limits, and MusicBrainz allows roughly one request per
second. Removing them produces HTTP 429 and incomplete playlists, not speed.

## Known limitations

- No matching against a different edition (deluxe, regional) beyond text comparison.
- No manual pinning of "this Spotify track is that library track" yet.
- No ISRC cache: every import re-asks MusicBrainz.
