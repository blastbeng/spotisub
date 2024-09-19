#!/usr/bin/env bash
# Modify user/group
PUID=${PUID:-1000}
PGID=${PGID:-1000}
groupmod -o -g "$PGID" user
usermod -o -u "$PUID" user

# Create cache directory and set permissions
CACHE_DIR=${CACHE_DIR:-"/home/user/spotisub/cache"}
mkdir -p ${CACHE_DIR}
chown -R user:user ${CACHE_DIR}

# Run the application as 'user'
gosu user uwsgi --ini uwsgi.ini --enable-threads --py-call-uwsgi-fork-hooks --log-4xx --log-5xx --lazy
