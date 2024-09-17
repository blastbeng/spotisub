#!/usr/bin/env bash
export TAG=$1; docker compose -f docker-compose.tag.yml build
export TAG=$1; docker compose -f docker-compose.tag.yml push
git tag v$1
git push origin --tags

export TAG=latest; docker compose -f docker-compose.tag.yml build
export TAG=latest; docker compose -f docker-compose.tag.yml push