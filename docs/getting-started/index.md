# Start here

This section takes you from "nothing installed" to "my playlists are on my server".
Read the four numbered pages in order; the rest are alternative installation methods
you can skip unless you need them.

<div class="grid cards" markdown>

-   **1. Create a Spotify app** — [Open](spotify-app.md)
-   **2. Install with Docker** — [Open](docker.md)
-   **3. Log in to Spotify** — [Open](first-run.md)
-   **4. Import your first playlist** — [Open](first-import.md)

</div>

## Other ways to install

| Method | Use it when |
|---|---|
| [Installer script](install-script.md) | You want the fewest keystrokes on a Linux box |
| [Manual Docker](manual-docker.md) | You want to read and edit the compose file yourself |
| [Build from source](from-source.md) | You want a local image from a branch with unreleased fixes |
| [Run without Docker](no-docker.md) | You have Python 3.10+ and do not want containers |

## What you should have before starting

- The address, port, username and password of your Subsonic server.
- Your Subsonic server's music folder already scanned (Spotisub only sees what the
  server has indexed).
- About 10 minutes.

!!! tip "Your music server must be reachable from the container"

    If Subsonic runs in Docker too, put both containers on the same Docker network and
    use the service name as the host (for example `http://navidrome`), not
    `http://localhost` — inside a container, `localhost` is the container itself.
