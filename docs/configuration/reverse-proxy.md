# Reverse proxy

Spotisub serves plain HTTP on port `5183` and uses a WebSocket (`socket.io`) for its live
logs. A reverse proxy must forward both, and must not break the absolute URLs Flask
generates.

## What the proxy must do

1. Forward `/` to `http://<spotisub>:5183/`.
2. Forward WebSocket upgrades (`Upgrade`/`Connection` headers) — otherwise the Logs page
   never updates.
3. If you serve it under a sub-path, strip the prefix before proxying and set
   `APPLICATION_ROOT` to the same prefix so generated links and the session cookie use
   it.
4. Do not enable gzip on the proxied response; Spotisub's HTML is rewritten by proxies
   in the sub-path case, and pre-compressed bodies break that.

Spotify's redirect URI must be the **public** HTTPS URL (loopback is the only `http://`
exception):

```ini
SPOTIPY_REDIRECT_URI=https://music.example.com/callback
```

## Nginx

Full example, including the optional `/spotisub/` sub-path. Drop the `sub_filter` lines
and the `rewrite` if you serve it at the root of a dedicated host.

```nginx
server {
    server_name music.example.com;
    listen 443 ssl;
    http2 on;

    # Certificates managed by Certbot
    ssl_certificate     /etc/letsencrypt/live/music.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/music.example.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # --- Root install: use this block -------------------------------------
    location / {
        proxy_pass http://127.0.0.1:5183;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $http_connection;
        proxy_read_timeout 300s;
    }
    # ----------------------------------------------------------------------

    # --- Sub-path install (/spotisub/): replace the block above -----------
    # location = /spotisub { return 301 https://$host/spotisub/; }
    #
    # location /spotisub/ {
    #     rewrite ^/spotisub/(.*) /$1 break;
    #     proxy_pass http://127.0.0.1:5183/;
    #     proxy_redirect http://127.0.0.1:5183 /spotisub;
    #     proxy_http_version 1.1;
    #     proxy_set_header Host $host;
    #     proxy_set_header X-Forwarded-Proto $scheme;
    #     proxy_set_header Upgrade $http_upgrade;
    #     proxy_set_header Connection $http_connection;
    #     gzip off;
    #     sub_filter 'src="/'  'src="/spotisub/';
    #     sub_filter 'href="/' 'href="/spotisub/';
    #     sub_filter_once off;
    #     sub_filter_types text/xml text/css text/javascript application/javascript;
    # }
    #
    # # socket.io lives at the root path and will conflict with other apps that use it
    # location /socket.io/ {
    #     proxy_pass http://127.0.0.1:5183/socket.io/;
    #     proxy_http_version 1.1;
    #     proxy_set_header Upgrade $http_upgrade;
    #     proxy_set_header Connection $http_connection;
    # }
    # ----------------------------------------------------------------------
}

server {
    listen 80;
    server_name music.example.com;
    return 301 https://$host$request_uri;
}
```

and in `.env`, for the sub-path case:

```ini
APPLICATION_ROOT=/spotisub
SPOTIPY_REDIRECT_URI=https://music.example.com/spotisub/callback
```

## Caddy

Caddy handles TLS and WebSockets automatically:

```caddyfile
music.example.com {
    reverse_proxy 127.0.0.1:5183
}
```

Sub-path:

```caddyfile
music.example.com {
    handle_path /spotisub/* {
        reverse_proxy 127.0.0.1:5183
    }
}
```

## Traefik

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.spotisub.rule=Host(`music.example.com`)"
  - "traefik.http.routers.spotisub.tls.certresolver=letsencrypt"
  - "traefik.http.services.spotisub.loadbalancer.server.port=5183"
```

Traefik forwards WebSocket upgrades without extra configuration.

## Healthcheck through the proxy

```bash
curl -fsS https://music.example.com/api/v1/utils/healthcheck   # Ok!
```

If this works but the dashboard spins, the WebSocket is not being forwarded. If the
dashboard redirects to `/login` in a loop after a sub-path change, clear the site
cookies: the session cookie path is derived from `APPLICATION_ROOT`.
