# Changelog

All notable changes to Spotisub are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Sections up to `0.3.6` were backfilled from the existing git tags and GitHub
Releases when automated releases were introduced; they are not itemised
commit-by-commit.

## [0.3.6] - 2025-12-15

### Added
- Colour-coded output on the Logs page, and a Subsonic REST API check button that
  verifies connectivity from the UI.
- Spotify authorisation can be completed from the running application (the
  `init.py` flow is integrated in the web UI).
- `SUBSONIC_API_VERIFY_SSL` to disable TLS verification, for Navidrome instances
  using a self-signed certificate.

### Changed
- Log level defaults to `INFO`; a flushing log handler keeps `cache/spotisub.log`
  up to date so the Logs page does not lag behind.
- `SUBSONIC_API_BASE_URL` and the Spotify redirect URI are configured from
  `.env` again instead of hard-coded values.

### Fixed
- Logs page: long logging messages no longer break the layout, page width fixed,
  the broken download-logs button was removed.
- Circular import between `spotisub`, `routes` and `generator` that could
  prevent the application from starting.

## [0.3.5] - 2025-06-17

### Added
- `TEXT_COMAPRE_MATCHING_ENABLED` to gate the string-comparison fallback (OFF by
  default), and `PLAYLIST_PREFIX` / `ITEMS_PER_PLAYLIST` tuning.
- `ARTIST_PLAYLIST_ENABLED` to gate artist top-tracks playlists, default OFF.
- Subsonic library cache (`cache/subsonic_cache.pkl`), rebuilt when the library
  song count changes, and `playlist-read-private` in the requested Spotify scopes.

### Changed
- Track matching reworked around MusicBrainz ISRC lookups and the cached
  Subsonic library, with clearer logging of MusicBrainz API errors.

### Removed
- Recommendation playlist generation is disabled: Spotify deprecated the
  `/recommendations` endpoint in December 2024. Scheduled jobs are only modified
  when they are actually registered.

### Fixed
- Playlist items that are not songs (for example podcast episodes) are skipped
  instead of breaking the import of the whole playlist.
- Typo in an environment variable name, and pylint errors.

## [0.3.4] - 2024-12-06

### Added
- `APPLICATION_ROOT` support for serving the app under a sub-path, and
  `LOGIN_DISABLED` for local use without a login.
- Optional spotdl download of tracks that are missing from the Subsonic library.
- ARM images for the published container.

### Fixed
- Assorted bugfixes.

## [0.3.3] - 2024-10-08

### Added
- Tasks page and Logs page, live-updated over websockets.
- Rescan and "reimport everything" actions.
- Search, ordering and pagination on the playlist/song/album/artist lists.

### Changed
- Replaced uwsgi with gunicorn and reworked the job scheduler and the database
  layer.

## [0.3.1] - 2024-09-27

### Added
- First dashboard implementation: overview page, toolbar, song page.
- Configuration table backing the dashboard.

### Changed
- REST endpoints drive the scheduler jobs instead of running work inline.

[0.3.6]: https://github.com/blastbeng/spotisub/compare/v0.3.5...v0.3.6
[0.3.5]: https://github.com/blastbeng/spotisub/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/blastbeng/spotisub/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/blastbeng/spotisub/compare/v0.3.1...v0.3.3
[0.3.1]: https://github.com/blastbeng/spotisub/compare/v0.2.5...v0.3.1
