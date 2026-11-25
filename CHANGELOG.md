# Changelog

All notable changes to Spotisub are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Sections up to `0.3.6` were backfilled from the existing git tags and GitHub
Releases when automated releases were introduced; they are not itemised
commit-by-commit.

## [0.3.10] - 2026-11-25

### Fixed

- **Spotify login works with the stock configuration again.** The compiled-in
  `SPOTIPY_REDIRECT_URI` default was `http://127.0.0.1:8080/`, a port the container never
  publishes, so an install that did not set the variable sent the browser to a page that
  does not exist (#101). The default is now `http://127.0.0.1:5183/callback`, and the
  dashboard names the exact URL to whitelist when the credentials are incomplete.
- Spotisub now warns at startup when `SPOTIPY_REDIRECT_URI` does not end in `/callback` —
  the one misconfiguration that looks like "the Spotify login does nothing".

### Changed

- The README is rewritten as a usable quickstart: the documentation site first, then
  requirements, a copy-pasteable compose file, how matching works, the settings that
  change behaviour, the cache files worth backing up, and where to get help.
- The documentation states Spotify's February 2026 developer policy: the account that
  owns the app needs **Premium**, because Spotify blocks free accounts from the Web API
  with `403` (#105). The requirements table, the FAQ, the Spotify walkthrough, a new
  troubleshooting section and `README.md` all say so.

### Upgrade notes

- If your `.env` still carries `SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080/` from an old
  setup, change it to `http://127.0.0.1:5183/callback` and add that exact URL to the
  Spotify app. Leaving the variable out now also works.

## [0.3.9] - 2026-11-25

### Fixed

- The documentation site is now republished as part of every release, so
  [Release history](https://blastbeng.github.io/spotisub/release-history/) contains
  the version that was just published. Until now the release commit was pushed with
  the default `GITHUB_TOKEN`, which cannot start other workflows, and the newest
  section stayed missing until the site was rebuilt by hand.
- The release workflow can be dispatched again after a release has been made. Its
  preflight asserted that `latest` is an ancestor of `dev`, which the release itself
  turns false when it creates `latest` with a `--no-ff` merge; the second release
  would have been refused.

### Upgrade notes

- Nothing changes at runtime; this release only affects how the documentation site
  and the release pipeline behave.

## [0.3.8] - 2026-11-25

### Added
- A documentation site at <https://blastbeng.github.io/spotisub/>: a four-step
  quickstart, per-page guides for the dashboard, playlists, missing tracks and
  ignoring, the full environment-variable reference, scheduler semantics,
  reverse-proxy recipes, Navidrome / spotdl / Lidarr integrations, the REST API and a
  troubleshooting page built from the recurring issue reports. It replaces the GitHub
  wiki, which is retired. The content is versioned with the code in `docs/` and is
  published by the new `pages` workflow.
- A `release` workflow is now the only release path: it preflights the branch, bumps
  `VERSION`, appends to `VERSIONS`, writes the `CHANGELOG.md` section, merges `dev`
  into `latest`, tags, builds the multi-arch image through `docker.yml`, verifies the
  published platforms and digests, and creates the GitHub Release.
- A `version-guard` workflow fails a push when `VERSION`, the `vX.Y.Z` tag and
  `CHANGELOG.md` disagree.
- `SUBSONIC_API_PORT` may be left empty; the port is inferred from the scheme of
  `SUBSONIC_API_HOST` (443 for https, 80 for http) (#104).
- A Logout button in the sidebar; stale cookies can no longer bounce a browser between
  `/overview/` and `/login` (#104, #103).

### Changed
- The image is based on `python:3.10-slim-bookworm` instead of the end-of-life bullseye
  base (#102).
- Every container image is built by CI with an explicit tag list and a tag-to-`VERSION`
  assertion, so a build cannot publish tags the git ref does not describe.
- `VERSIONS` history repaired to the versions that were actually released (`0.3.4` was
  the last entry although `0.3.5` and `0.3.6` had been published).
- `.env.sample` rewritten from `constants.py`: the recommendation interval was
  misspelled and therefore ignored, and the artist top-tracks, text-comparison,
  playlist-prefix, spotdl and Lidarr keys were missing from it.

### Removed
- `create_tag.sh` and `docker-compose.tag.yml`, the local single-arch release scripts
  that produced the `vv0.3.6` image and the untagged `v0.3.7` image on Docker Hub.

### Fixed
- Playlist import against `GET /v1/playlists/{id}/items`, where Spotify renamed the
  `track` field to `item` and `fields=items.track.*` started returning nothing (#100,
  #106).
- One inaccessible playlist no longer aborts the whole reimport: a 403 on a single
  playlist is logged and skipped (#106).
- MusicBrainz ISRC lookups retry on transient network errors with a backoff instead of
  marking the track permanently unmatched (#99, #108).
- **Check Subsonic** reports the real error — wrong password, wrong path, TLS — instead
  of a generic failure, because the check uses `getMusicFolders()` where `ping()`
  swallowed every exception (#98, #104).
- The `/api/v1/import/*` endpoints and `/api/v1/generate/artist_top_tracks` raised
  `NameError` on every call because `routes.py` used the scheduler without importing
  it.
- The installer no longer writes a redirect URI for a port Spotisub does not publish,
  health-checks `/api/v1/utils/healthcheck`, and leaves the container running after the
  Spotify authorisation instead of stopping it.
- The spotdl and Lidarr clients are created on first use, so a boot with
  `SPOTDL_ENABLED=0` cannot fail while importing them.

### Upgrade notes
- The first automated release is `0.3.8`. The Docker Hub tags `v0.3.7` (no git tag, no
  GitHub Release) and `vv0.3.6` (a typo from the retired script) are artefacts of the
  old local release path. They are left in place but are **not** supported; do not use
  them.
- Sessions are signed with a key persisted in `cache/secret_key`. `SECRET_KEY` in the
  environment takes precedence; clearing `cache/` logs users out once.
- The two recommendation endpoints remain declared but their jobs are not registered:
  Spotify removed `/v1/recommendations` in December 2024.

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

[0.3.10]: https://github.com/blastbeng/spotisub/compare/v0.3.6...v0.3.10
[0.3.9]: https://github.com/blastbeng/spotisub/compare/v0.3.6...v0.3.9
[0.3.8]: https://github.com/blastbeng/spotisub/compare/v0.3.6...v0.3.8
[0.3.6]: https://github.com/blastbeng/spotisub/compare/v0.3.5...v0.3.6
[0.3.5]: https://github.com/blastbeng/spotisub/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/blastbeng/spotisub/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/blastbeng/spotisub/compare/v0.3.1...v0.3.3
[0.3.1]: https://github.com/blastbeng/spotisub/compare/v0.2.5...v0.3.1
