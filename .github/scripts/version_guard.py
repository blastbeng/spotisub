#!/usr/bin/env python3
"""Guard the relationship between VERSION, VERSIONS, tags and CHANGELOG.

Fails when the application version, its history, the changelog or the release
tags drift apart. Run from a full-history checkout.
"""

import os
import re
import subprocess
import sys

VERSION_FILE = 'spotisub/database.py'
CHANGELOG_FILE = 'CHANGELOG.md'

VERSION_RE = re.compile(r'^VERSION\s*=\s*"([^"]+)"', re.MULTILINE)
VERSIONS_RE = re.compile(r'^VERSIONS\s*=\s*\[([^\]]*)\]', re.MULTILINE | re.DOTALL)
HEADER_RE = re.compile(r'^## \[([^\]]+)\]\s+-\s+(\d{4}-\d{2}-\d{2})$', re.MULTILINE)
LINK_RE = re.compile(r'^\[([^\]]+)\]:\s+(\S+)$', re.MULTILINE)
SEMVER_RE = re.compile(
    r'^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'
    r'(?:-(?P<pre>[0-9A-Za-z.-]+))?$'))

errors = []


def fail(message):
    """Record a guard violation."""
    errors.append(message)


def git(*args, check=False):
    """Run a git command and return stdout (empty string on failure)."""
    result = subprocess.run(
        ('git',) + args, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip() if result.returncode == 0 else ''


def semver_key(version):
    """Return a sortable key for a version, stable releases above pre-releases."""
    match = SEMVER_RE.match(version)
    if not match:
        return None
    pre = match.group('pre')
    return (int(match.group('major')), int(match.group('minor')),
            int(match.group('patch')), 0 if pre else 1, pre or '')


def read_version(source):
    """Extract VERSION from a database.py source string."""
    match = VERSION_RE.search(source)
    return match.group(1) if match else None


def read_versions(source):
    """Extract VERSIONS from a database.py source string."""
    match = VERSIONS_RE.search(source)
    if not match:
        return []
    return re.findall(r'"([^"]+)"', match.group(1))


def commit_subject(ref='HEAD'):
    """Return the subject of a commit."""
    return git('log', '-1', '--format=%s', ref)


def previous_source():
    """Return the database.py source at the comparison ref, if resolvable."""
    before = os.environ.get('PREV_COMMIT', '')
    base_ref = os.environ.get('BASE_REF', '')
    if before and set(before) != {'0'}:
        return git('show', f'{before}:{VERSION_FILE}')
    if base_ref:
        merge_base = git('merge-base', f'origin/{base_ref}', 'HEAD')
        if merge_base:
            return git('show', f'{merge_base}:{VERSION_FILE}')
    if git('rev-parse', '--verify', '-q', 'HEAD~1'):
        return git('show', f'HEAD~1:{VERSION_FILE}')
    return ''


def main():
    """Run all guard checks."""
    with open(VERSION_FILE, encoding='utf-8') as handle:
        source = handle.read()
    version = read_version(source)
    if not version:
        fail(f'{VERSION_FILE}: VERSION not found')
        return report()
    if not SEMVER_RE.match(version):
        fail(f'VERSION "{version}" is not valid semver')

    versions = read_versions(source)
    if not versions:
        fail(f'{VERSION_FILE}: VERSIONS not found')
    if version not in versions:
        fail(f'VERSION "{version}" is missing from VERSIONS')

    keys = [semver_key(entry) for entry in versions]
    if any(key is None for key in keys):
        fail(f'VERSIONS contains an unparsable entry: {versions}')
    elif keys != sorted(keys):
        fail(f'VERSIONS is not in ascending order: {versions}')
    elif len(set(versions)) != len(versions):
        fail(f'VERSIONS contains duplicates: {versions}')

    try:
        with open(CHANGELOG_FILE, encoding='utf-8') as handle:
            changelog = handle.read()
    except FileNotFoundError:
        fail(f'{CHANGELOG_FILE} is missing')
        changelog = ''

    if changelog:
        headers = HEADER_RE.findall(changelog)
        names = [name for name, _ in headers]
        if len(names) != len(set(names)):
            fail(f'{CHANGELOG_FILE} has duplicate version headers: {names}')
        if names.count(version) != 1:
            fail(f'{CHANGELOG_FILE} has no single "## [{version}]" section '
                 f'(headers: {names})')
        parsed = [semver_key(name) for name in names]
        if any(key is None for key in parsed):
            fail(f'{CHANGELOG_FILE} has a malformed version header: {names}')
        elif parsed != sorted(parsed, reverse=True):
            fail(f'{CHANGELOG_FILE} sections are not newest-first: {names}')
        links = dict(LINK_RE.findall(changelog))
        for name in names:
            if name not in links:
                fail(f'{CHANGELOG_FILE} has no compare link for [{name}]')

    tags_at_head = [tag for tag in git('tag', '--points-at', 'HEAD').splitlines()
                    if tag]
    for tag in tags_at_head:
        if tag != f'v{version}':
            fail(f'tag {tag} points at HEAD but VERSION is {version} '
                 f'(expected v{version})')

    previous = read_version(previous_source() or '')
    if previous and previous != version:
        # The release workflow moves VERSION in a chore(release) commit on dev
        # and then merges dev into latest; both heads are legitimate carriers.
        expected = (f'chore(release): v{version}',
                    f'Merge dev into latest for v{version}')
        if commit_subject() not in expected:
            fail(f'VERSION changed from {previous} to {version} but the head '
                 f'commit is "{commit_subject()}" instead of one of {expected}')

    return report()


def report():
    """Print the outcome and return an exit code."""
    if errors:
        for message in errors:
            print(f'::error::{message}')
        return 1
    print('version guard OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
