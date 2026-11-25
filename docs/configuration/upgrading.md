# Upgrading

## Before you upgrade

1. Read the [release history](../release-history.md) entry for the version you are
   moving to — configuration changes and upgrade notes are listed there.
2. Back up `cache/` and `.env`:

   ```bash
   docker compose stop spotisub
   tar czf spotisub-cache-$(date +%F).tar.gz -C /opt/spotisub cache
   ```

## Upgrade

```bash
docker compose pull        # fetch the new image
docker compose up -d       # recreate the container
docker compose logs -f --tail=100
```

Or pin and switch explicitly:

```yaml
    image: "blastbeng/spotisub:0.3.9"
```

```bash
docker compose up -d
```

## What survives an upgrade

`cache/` is untouched by the image: the database, the Spotify token, the secret key and
the caches are all there. An upgrade normally changes nothing on your side except the
version reported at startup.

!!! warning "Database changes require a manual step"

    This version has **no automatic schema migration**. Any release that changes the
    database schema documents the required `ALTER TABLE` (and its rollback) in its
    release notes. If you skip several versions, read every entry you skipped, oldest
    first.

## Roll back

```bash
docker compose stop spotisub
tar xzf spotisub-cache-2026-11-25.tar.gz -C /opt/spotisub
# edit image: back to the previous version
docker compose up -d
```

A rollback is only complete with the matching `cache/` backup, because a newer version
may have written rows an older one does not understand.

## Which version am I running?

The version is printed in the startup banner and logged:

```bash
docker compose logs | head -20
# ...                                  v0.3.9
```

Image tags, platforms and digests for every release are listed in the
[release history](../release-history.md).

## Upgrading from 0.3.6 or older

- `dev` images are rebuilt on every push and are not a release channel for production.
- `create_tag.sh` and `docker-compose.tag.yml` no longer exist: releases are built only
  by GitHub Actions.
- The base image moved from Debian bullseye to bookworm; nothing changes for users.
