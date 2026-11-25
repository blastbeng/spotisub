# Missing tracks

This is the question behind most reports: *Spotisub imported my playlist but half the
tracks are missing.*

Missing means: for this Spotify track, in this playlist, no song in your library was
matched. Spotisub cannot invent music; it matches. So either the track is not in your
library, or it is there under metadata that does not match.

## Step 1 — Is the track really in the library?

Search for it in your music server's own UI. If it is not there, that is the answer:
add it, rescan the server, then rescan the playlist.

## Step 2 — Check the `musicBrainzId` tag

MBID matching is the reliable path and it needs one tag on your files:

```bash
# any one of these will show it
ffprobe -v error -show_entries format_tags=musicbrainz_trackid -of default song.flac
mid3v2 --list song.mp3 | grep -i musicbrainz
metaflac --list --block-type=VORBIS_COMMENT song.flac | grep -i musicbrainz
```

The value Subsonic exposes as `musicBrainzId` must be the **recording** MBID, e.g.
`f151cb94-c909-46a8-ad99-fb77391abfb8`.

- Picard writes it by default (*Options → Tags → MusicBrainz*).
- beets writes it with the `chroma`/`musicbrainz` plugins enabled.
- Navidrome reads it from the file tags; **it does not compute it**.

If the tag is missing everywhere, matching falls back to text comparison (next step),
which is far less precise.

!!! tip "Bulk-checking a library"

    `musicbrainzngs` and `beets` can both report how many files lack an MBID. Doing a
    one-off Picard pass over the library fixes years of missing matches at once.

## Step 3 — Enable text comparison

Text comparison is **off by default** because a wrong match is worse than a missing one.
Turn it on and rescan a playlist to see how well it does on *your* library:

```ini
TEXT_COMAPRE_MATCHING_ENABLED=1
```

The misspelled name is real and is the public interface; do not "fix" it in your `.env`.

What it does: for each unmatched track it searches the library by title, then compares
titles and artists after splitting on `(`, `-` and `feat` and stripping punctuation. A
match must survive `EXCLUDED_WORDS` filtering as well.

Read [How matching works](matching.md) before enabling it globally: it can attach a
live version when you wanted the studio one.

## Step 4 — Excluded words

`EXCLUDED_WORDS` (default `acoustic,instrumental,demo`) removes candidates **only** in
text comparison. If a track with "live" in the title stays missing, the exclusion list
may be why:

```ini
EXCLUDED_WORDS=acoustic,instrumental,demo
```

Set it to an empty string to disable filtering entirely.

## Step 5 — Manual decisions

For the tracks that will never match, do not keep staring at them: **ignore** them. See
[Ignoring items](ignoring.md).

## Known causes, in order of frequency

| Cause | Fix |
|---|---|
| Files have no `musicBrainzId` tag | Tag them (Picard), rescan |
| ISRC missing on MusicBrainz | Text comparison, or add the ISRC upstream |
| Remaster/live/edit differs from the Spotify release | Text comparison, or ignore |
| Track is a podcast episode | Not supported, ignore |
| Library not scanned by the server | Scan the server first |
| Wrong Subsonic base URL / path | Fix `SUBSONIC_API_BASE_URL`, **Check Subsonic** |
| `SUBSONIC_API_PORT` pointing at the wrong service | Fix the port |
