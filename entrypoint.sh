#!/usr/bin/env bash
uwsgi --ini uwsgi.ini --enable-threads --py-call-uwsgi-fork-hooks --log-4xx --log-5xx --lazy
