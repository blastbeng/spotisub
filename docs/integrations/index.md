# Integrations

Spotisub talks to your music server, and optionally to two more services.

<div class="grid cards" markdown>

-   **Navidrome**
    ---
    The most common companion. Playlists, `ND_BASEURL`, and how the two containers find
    each other.

    [:octicons-arrow-right-24: Navidrome setup](navidrome.md)

-   **spotdl**
    ---
    Download the tracks that are missing from your library, automatically, during an
    import.

    [:octicons-arrow-right-24: Automatic downloads](spotdl.md)

-   **Lidarr**
    ---
    Only download tracks whose artist you actually monitor — the "don't download that
    artist" switch.

    [:octicons-arrow-right-24: Lidarr gating](lidarr.md)

</div>

## Other Subsonic servers

Spotisub uses the standard Subsonic REST API, so the same settings work for Airsonic,
Gonic, Astiga, Ampache (Subsonic backend) and others. The only differences are:

- the port (Navidrome `4533`, Airsonic `4040`, ...),
- whether the server is mounted under a path prefix (`SUBSONIC_API_BASE_URL`),
- whether playlists are writable at all — Spotisub needs the `createPlaylist` and
  `updatePlaylist` endpoints.
