# Get help

Before asking, run the [five-minute diagnosis](index.md#the-five-minute-diagnosis): it
answers most questions on the spot.

## Where

| Channel | Best for |
|---|---|
| [GitHub Issues](https://github.com/blastbeng/spotisub/issues) | Reproducible bugs, feature requests — the only place maintainers track work |
| [Discord](https://discord.gg/jXQauuhy5w) | Quick questions, setup chat |
| [Reddit r/spotisub](https://www.reddit.com/r/spotisub/) | Discussion, screenshots |

Read the [documentation](index.md) and, for setup problems, the
[troubleshooting page](troubleshooting.md) first — issues that restate them are usually
closed with a link.

## What to include in a bug report

1. **Version**: the banner printed at startup (`v0.3.x`), or the image tag.
2. **How you run it**: Docker Compose (paste the compose file with secrets removed) or
   source, plus your OS/architecture.
3. **What you expected** and **what happened**, in one sentence each.
4. **The relevant log window**, not the whole file:

   ```bash
   docker compose logs --since 30m spotisub | tail -100
   ```

   Redact: usernames, passwords, the Spotify client secret, and the contents of
   `cache/spotipy_cache`.
5. **For matching problems**: whether the file has a `musicBrainzId` tag, whether
   `TEXT_COMAPRE_MATCHING_ENABLED` is `1`, and what **Check Subsonic** says.

## What not to paste

- Your `SPOTIPY_CLIENT_SECRET`, `SUBSONIC_API_PASS`, `LIDARR_TOKEN`.
- Your `cache/spotipy_cache` (it contains a live refresh token).
- The `cache/spotisub.db`.

## Feature requests

Say what you are trying to achieve, not only what to build. Several existing issues are
"artist allow-list", "multi-user", "configure from the UI"; if your request is one of
those, add your use case to the existing issue instead of opening a new one.
