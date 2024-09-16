#!/usr/bin/env bash
export TAG=$1; docker compose -f docker-compose.tag.yml build
export TAG=$1; docker compose -f docker-compose.tag.yml push