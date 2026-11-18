#!/usr/bin/env python3
"""Checks the relative links in the repository's Markdown files.

A link fails the check if the file it points to does not exist, or if it
names a heading that the file does not have. Links to web addresses are not
checked. Run it from anywhere inside the repository:

    python3 .github/scripts/check_links.py

It prints each broken link and exits with status 1 if there are any.
"""
import os
import re
import subprocess
import sys

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")
EXTERNAL = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def lines_outside_code(path):
    """Yields (line number, line) for the lines that are not in a code block."""
    in_block = False
    with open(path, encoding="utf-8") as file:
        for number, line in enumerate(file, start=1):
            if FENCE.match(line):
                in_block = not in_block
                continue
            if not in_block:
                yield number, line


def anchors(path):
    """Returns the heading anchors GitHub generates for a Markdown file."""
    found = set()
    counts = {}
    for _, line in lines_outside_code(path):
        match = HEADING.match(line)
        if not match:
            continue
        # GitHub lowercases the heading text, drops everything except
        # letters, digits, spaces, hyphens, and underscores, and turns each
        # space into a hyphen. A repeated heading gets -1, -2, and so on.
        text = match.group(1).replace("`", "").lower()
        anchor = re.sub(r"[^\w\- ]", "", text).replace(" ", "-")
        count = counts.get(anchor, 0)
        counts[anchor] = count + 1
        found.add(anchor if count == 0 else "%s-%d" % (anchor, count))
    return found


def main():
    root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    # Tracked files and new files that are not ignored.
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
        check=True, capture_output=True, text=True, cwd=root,
    ).stdout.split("\n")
    files = [os.path.join(root, name) for name in listed if name]
    files = [path for path in files if os.path.exists(path)]

    anchor_cache = {}
    broken = []
    checked = 0
    for path in files:
        for number, line in lines_outside_code(path):
            for target in LINK.findall(INLINE_CODE.sub("", line)):
                if EXTERNAL.match(target):
                    continue
                checked += 1
                file_part, _, anchor = target.partition("#")
                if file_part:
                    linked = os.path.normpath(os.path.join(os.path.dirname(path), file_part))
                else:
                    linked = path
                where = "%s:%d" % (os.path.relpath(path, root), number)
                if not os.path.exists(linked):
                    broken.append("%s: %s does not exist" % (where, target))
                elif anchor and linked.endswith(".md"):
                    if linked not in anchor_cache:
                        anchor_cache[linked] = anchors(linked)
                    if anchor.lower() not in anchor_cache[linked]:
                        broken.append("%s: %s has no heading for #%s" % (where, file_part or "this file", anchor))

    for line in broken:
        print(line)
    print("%d relative links checked in %d files, %d broken" % (checked, len(files), len(broken)))
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
