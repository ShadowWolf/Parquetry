#!/usr/bin/env python3
"""Checks the relative links in the repository's Markdown files.

A link fails the check if the file it points to does not exist, or if it
names a heading that the file does not have. Run it from anywhere inside the
repository:

    python3 .github/scripts/check_links.py

It prints each broken link and exits with status 1 if there are any.

What it checks:

- Inline links, [text](target), including text that wraps onto the next
  line, a target in angle brackets, and a target followed by a title.
- Reference definitions, [label]: target.
- href attributes in HTML.
- A target that starts with / is taken from the root of the repository.

What it does not check:

- Web addresses, so a run does not fail because another site is down.
- Text inside code blocks, code spans, and HTML comments.

Known limits. None of these forms is used in the repository, and the check
would need more work before one is:

- A file name that contains a parenthesis, and link text that contains a
  square bracket.
- A heading written with a line of = or - under it. Only headings that start
  with # are known, so a link to the other kind is reported as broken.
- A heading whose text has underscores for emphasis, and an anchor made with
  an HTML <a> tag. A link to either is reported as broken.
"""
import os
import re
import subprocess
import sys
from urllib.parse import unquote

INLINE_LINK = re.compile(r"\[[^\[\]]*\]\(\s*<?([^()<>\s]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REFERENCE_DEFINITION = re.compile(r"^ {0,3}\[[^\]]+\]:\s*<?([^<>\s]+)>?", re.MULTILINE)
HREF = re.compile(r"href=\"([^\"]+)\"")
FENCED_BLOCK = re.compile(r"^[ \t]*(```|~~~).*?^[ \t]*\1[ \t]*$", re.MULTILINE | re.DOTALL)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
CODE_SPAN = re.compile(r"(`+)(?!`).*?(?<!`)\1(?!`)", re.DOTALL)
HEADING = re.compile(r"^#{1,6}[ \t]+(.*?)[ \t]*#*[ \t]*$", re.MULTILINE)
EXTERNAL = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def blank(match):
    """Replaces a match with spaces, keeping line breaks, so that the line
    numbers of the text after it do not change."""
    return re.sub(r"[^\n]", " ", match.group(0))


def prose(path, keep_code_spans=False):
    """Returns a file's text with code blocks and HTML comments blanked out,
    and code spans too unless keep_code_spans is set."""
    with open(path, encoding="utf-8") as file:
        text = file.read()
    text = FENCED_BLOCK.sub(blank, text)
    text = HTML_COMMENT.sub(blank, text)
    if not keep_code_spans:
        text = CODE_SPAN.sub(blank, text)
    return text


def anchors(path):
    """Returns the heading anchors GitHub generates for a Markdown file."""
    found = set()
    counts = {}
    for match in HEADING.finditer(prose(path, keep_code_spans=True)):
        # GitHub builds the anchor from the heading as displayed: a link
        # shows only its text, and backticks and asterisks are not shown.
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", match.group(1))
        text = text.replace("`", "").replace("*", "").lower()
        # It then drops everything except letters, digits, spaces, hyphens,
        # and underscores, and turns each space into a hyphen. A repeated
        # heading gets -1, -2, and so on.
        anchor = re.sub(r"[^\w\- ]", "", text).replace(" ", "-")
        count = counts.get(anchor, 0)
        counts[anchor] = count + 1
        found.add(anchor if count == 0 else "%s-%d" % (anchor, count))
    return found


def targets(text):
    """Yields (line number, target) for every link in a file's text."""
    for pattern in (INLINE_LINK, REFERENCE_DEFINITION, HREF):
        for match in pattern.finditer(text):
            yield text.count("\n", 0, match.start(1)) + 1, match.group(1)


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
        for number, target in sorted(targets(prose(path))):
            if EXTERNAL.match(target):
                continue
            checked += 1
            file_part, _, anchor = target.partition("#")
            file_part = unquote(file_part)
            if file_part.startswith("/"):
                linked = os.path.normpath(os.path.join(root, file_part.lstrip("/")))
            elif file_part:
                linked = os.path.normpath(os.path.join(os.path.dirname(path), file_part))
            else:
                linked = path
            where = "%s:%d" % (os.path.relpath(path, root), number)
            if not os.path.exists(linked):
                broken.append("%s: %s does not exist" % (where, target))
            elif anchor and linked.endswith(".md"):
                if linked not in anchor_cache:
                    anchor_cache[linked] = anchors(linked)
                if unquote(anchor).lower() not in anchor_cache[linked]:
                    broken.append("%s: %s has no heading for #%s" % (where, file_part or "this file", anchor))

    for line in broken:
        print(line)
    print("%d relative links checked in %d files, %d broken" % (checked, len(files), len(broken)))
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
