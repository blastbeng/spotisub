#!/usr/bin/env python3
"""Render (and optionally insert) the CHANGELOG section for a release.

The text is built from the commits between the previous release tag and HEAD,
grouped by their ``area:`` prefix. A curated body can be supplied with
``--notes`` instead, in which case it is used verbatim.

Usage:
    changelog_section.py --prev v0.3.6 --version 0.3.8 [--notes FILE] [--write]
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

SECTION_ORDER = [
    'Added',
    'Changed',
    'Deprecated',
    'Removed',
    'Fixed',
    'Security',
    'Upgrade notes',
]

PREFIX_SECTIONS = {
    'feat': 'Added',
    'add': 'Added',
    'new': 'Added',
    'fix': 'Fixed',
    'bugfix': 'Fixed',
    'hotfix': 'Fixed',
    'perf': 'Changed',
    'refactor': 'Changed',
    'ci': 'Changed',
    'build': 'Changed',
    'docker': 'Changed',
    'deps': 'Changed',
    'remove': 'Removed',
    'drop': 'Removed',
    'revert': 'Removed',
    'security': 'Security',
}

SKIP_PREFIXES = {'docs', 'test', 'tests', 'style', 'chore', 'release', 'lint'}

# Legacy-style subjects ("Added stale cookie checking") without an area prefix.
FIRST_WORD_SECTIONS = {
    'add': 'Added', 'added': 'Added', 'new': 'Added',
    'fix': 'Fixed', 'fixed': 'Fixed', 'hotfix': 'Fixed',
    'remove': 'Removed', 'removed': 'Removed', 'drop': 'Removed',
    'change': 'Changed', 'changed': 'Changed', 'improve': 'Changed',
    'improved': 'Changed', 'update': 'Changed', 'rework': 'Changed',
    'refactor': 'Changed', 'move': 'Changed', 'moved': 'Changed',
}

VAGUE_SUBJECTS = {'bugfix', 'bugfixes', 'bug fix', 'bug fixes', 'fix', 'fixes'}

SUBJECT_RE = re.compile(r'^(?P<area>[A-Za-z]+)(?:\([^)]*\))?!?:\s*(?P<text>.+)$')
ISSUE_RE = re.compile(r'(?:fix(?:e[sd])?|close[sd]?|resolve[sd]?)\s+#(\d+)', re.IGNORECASE)
INLINE_ISSUE_RE = re.compile(r'\(#(\d+)\)')
UPGRADE_RE = re.compile(r'^Upgrade-Note:\s*(?P<text>.+)$', re.IGNORECASE)


def git(*args):
    """Run a git command and return its stdout."""
    result = subprocess.run(
        ('git',) + args, capture_output=True, text=True, check=True)
    return result.stdout


def read_commits(prev_tag):
    """Return (subject, body) tuples for non-merge commits since prev_tag."""
    rev_range = f'{prev_tag}..HEAD' if prev_tag else 'HEAD'
    raw = git('log', '--no-merges', '--format=%s%x1f%b%x1e', rev_range)
    commits = []
    for record in raw.split('\x1e'):
        record = record.strip('\n')
        if not record:
            continue
        subject, _, body = record.partition('\x1f')
        commits.append((subject.strip(), body.strip()))
    return commits


def normalise(text):
    """Turn a commit subject remainder into a changelog entry."""
    text = text.strip().rstrip('.')
    if not text:
        return text
    return text[0].upper() + text[1:]


def entries_from_commits(commits):
    """Group commit subjects into changelog sections."""
    sections = {}
    upgrade_notes = []
    seen = set()
    for subject, body in commits:
        for line in body.splitlines():
            match = UPGRADE_RE.match(line.strip())
            if match:
                upgrade_notes.append(normalise(match.group('text')))
        if subject.startswith('Merge '):
            continue
        if subject.strip().lower() in VAGUE_SUBJECTS:
            continue
        match = SUBJECT_RE.match(subject)
        if match:
            area = match.group('area').lower()
            if area in SKIP_PREFIXES:
                continue
            section = PREFIX_SECTIONS.get(area, 'Changed')
            entry = normalise(match.group('text'))
        else:
            first_word = re.match(r'[A-Za-z]+', subject)
            keyword = first_word.group(0).lower() if first_word else ''
            section = FIRST_WORD_SECTIONS.get(keyword, 'Changed')
            entry = normalise(subject)
        issues = INLINE_ISSUE_RE.findall(entry)
        issues += ISSUE_RE.findall(body)
        entry = re.sub(r'\s*\(#\d+\)', '', entry).strip()
        for number in dict.fromkeys(issues):
            entry = f'{entry} (#{number})'
        key = (section, entry)
        if key in seen:
            continue
        seen.add(key)
        sections.setdefault(section, []).append(entry)
    if upgrade_notes:
        sections['Upgrade notes'] = upgrade_notes
    return sections


def render_section(version, date, sections=None, body=None):
    """Return the markdown section for a release."""
    if body is not None:
        body = body.strip('\n')
    else:
        lines = []
        for name in SECTION_ORDER:
            entries = (sections or {}).get(name) or []
            if not entries:
                continue
            lines.append(f'### {name}')
            for entry in entries:
                bullet = entry if entry.startswith('- ') else f'- {entry}'
                lines.append(bullet)
            lines.append('')
        body = '\n'.join(lines).strip('\n')
        if not body:
            body = '- No user-facing changes.'
    return f'## [{version}] - {date}\n\n{body}\n'


def insert_section(path, section, version, prev_version):
    """Insert the section after the preamble and register its compare link."""
    with open(path, encoding='utf-8') as handle:
        content = handle.read()
    anchor = re.search(r'^## \[', content, re.MULTILINE)
    if anchor:
        content = content[:anchor.start()] + section + '\n' + content[anchor.start():]
    else:  # pragma: no cover - defensive
        content = content.rstrip('\n') + '\n\n' + section + '\n'
    if prev_version:
        link = (f'[{version}]: https://github.com/blastbeng/spotisub/compare/'
                f'{prev_version}...v{version}\n')
        content = content.rstrip('\n') + '\n' + link
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(content)


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prev', default='', help='previous release tag (vX.Y.Z)')
    parser.add_argument('--version', required=True, help='version being released')
    parser.add_argument('--date', default=datetime.date.today().isoformat())
    parser.add_argument('--notes', default='', help='file with a curated body')
    parser.add_argument('--changelog', default='CHANGELOG.md')
    parser.add_argument('--write', action='store_true',
                        help='insert into the changelog instead of printing')
    parser.add_argument('--summary', default=os.environ.get('GITHUB_STEP_SUMMARY', ''))
    args = parser.parse_args()

    body = None
    if args.notes:
        with open(args.notes, encoding='utf-8') as handle:
            body = handle.read().strip('\n')
    sections = None if body is not None else entries_from_commits(
        read_commits(args.prev))
    section = render_section(args.version, args.date, sections, body)

    if args.write:
        insert_section(args.changelog, section, args.version, args.prev)
    print(section)
    if args.summary:
        with open(args.summary, 'a', encoding='utf-8') as handle:
            handle.write('## Generated changelog section\n\n```markdown\n')
            handle.write(section)
            handle.write('```\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
