#!/usr/bin/env python3
"""Verify an implementation against its build card (the implementer-side half
of the work-item-architecture QM contract).

Static conformance checks:
  1. Every changed file in the repo is listed in the card's Files table
  2. Must-not scans on changed files: SeeAllData=true, `without sharing`
     (unless the card itself specifies it), TODO/FIXME markers; warns on
     quoted 15/18-char Id-like literals and System.debug
  3. Every test method named in the card's Test spec exists in the code

This is the static half only. Deploying to the target sandbox, running the
tests and PMD are the implementer's deploy step; this gate runs before it.

Usage:  python3 verify_implementation.py <build-card.md> <repo-root>
                [--diff-base <git-ref>] [--baseline <pre-build-copy-dir>]
        Git repo: --diff-base compares the working tree to a ref; without it,
        uncommitted changes (git status) are checked.
        Non-git tree: pass --baseline, a copy of the repo taken before the
        build; changed files are computed against it. NEVER run `git init`
        to satisfy this verifier.
        Cards whose Test spec opens with 'Manual verification:' (browser
        scripts, data steps) skip the test-method-existence check.
Exit:   0 = pass (warnings allowed), 1 = one or more failures
Stdlib only. Python 3.8+.
"""

import re
import subprocess
import sys
from pathlib import Path

IGNORED_PREFIXES = ("work-items/", ".sfdx/", ".sf/", "node_modules/", ".git/")

failures = []
warnings = []


def fail(msg):
    failures.append(msg)


def warn(msg):
    warnings.append(msg)


def git(repo, *args):
    out = subprocess.run(["git", "-C", str(repo)] + list(args),
                         capture_output=True, text=True)
    if out.returncode != 0:
        fail(f"git {' '.join(args)}: {out.stderr.strip()}")
        return ""
    return out.stdout


def changed_files(repo, diff_base, baseline):
    files = set()
    if (repo / ".git").is_dir():
        if diff_base:
            for line in git(repo, "diff", "--name-only", diff_base).splitlines():
                if line.strip():
                    files.add(line.strip())
        for line in git(repo, "status", "--porcelain", "-uall").splitlines():
            if not line.strip():
                continue
            path = line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            files.add(path.strip('"'))
    elif baseline:
        base = Path(baseline)
        if not base.is_dir():
            fail(f"--baseline '{baseline}' is not a directory")
            return set()
        for f in repo.rglob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(repo).as_posix()
            if rel.startswith(IGNORED_PREFIXES):
                continue
            twin = base / rel
            if not twin.is_file() or twin.read_bytes() != f.read_bytes():
                files.add(rel)
    else:
        fail("not a git repo: pass --baseline <pre-build copy of the repo>. "
             "Never run 'git init' to satisfy this verifier.")
    return {f for f in files if not f.startswith(IGNORED_PREFIXES)}


def card_paths(text):
    """Paths from the '## Files' table: the last pipe cell containing '/'."""
    paths = set()
    section = section_body(text, "Files")
    for line in section.splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        candidates = [c.split(" (")[0].strip() for c in cells if "/" in c]
        if candidates:
            paths.add(candidates[-1])
    return paths


def section_body(text, name):
    parts = re.split(r"(?m)^##\s+", text)
    for part in parts[1:]:
        lines = part.splitlines()
        if lines and lines[0].strip().lower().startswith(name.lower()):
            return "\n".join(lines[1:])
    return ""


def test_methods(text):
    spec = section_body(text, "Test spec")
    if "manual verification" in spec.lower():
        return []
    return sorted(set(re.findall(r"\btest[A-Za-z0-9_]{2,}", spec)))


def main():
    args = sys.argv[1:]
    diff_base = None
    baseline = None
    if "--diff-base" in args:
        i = args.index("--diff-base")
        diff_base = args[i + 1]
        del args[i:i + 2]
    if "--baseline" in args:
        i = args.index("--baseline")
        baseline = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    card_path, repo = Path(args[0]), Path(args[1])
    if not card_path.is_file() or not repo.is_dir():
        print("FAIL  card file or repo root not found")
        sys.exit(1)
    card = card_path.read_text(encoding="utf-8")

    allowed = card_paths(card)
    if not allowed:
        fail(f"{card_path.name}: no paths found in the '## Files' table")

    changed = changed_files(repo, diff_base, baseline)
    if not changed:
        warn("no changed files detected; nothing to verify against the card")

    # 1. subset check
    for f in sorted(changed - allowed):
        fail(f"changed file not listed in the card: {f}")

    # 2. must-not scans on changed files that exist
    card_allows_without_sharing = "without sharing" in card
    for f in sorted(changed):
        p = repo / f
        if not p.is_file():
            continue
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            warn(f"{f}: unreadable ({exc})")
            continue
        for i, line in enumerate(body.splitlines(), 1):
            if re.search(r"SeeAllData\s*=\s*true", line, re.IGNORECASE):
                fail(f"{f}:{i}: SeeAllData=true")
            if re.search(r"\bwithout sharing\b", line) and not card_allows_without_sharing:
                fail(f"{f}:{i}: 'without sharing' not specified by the card")
            if re.search(r"\b(TODO|FIXME)\b", line):
                fail(f"{f}:{i}: TODO/FIXME marker left in code")
            if re.search(r"'[a-zA-Z0-9]{15}'|'[a-zA-Z0-9]{18}'", line):
                warn(f"{f}:{i}: quoted 15/18-char literal; hardcoded Id?")
            if re.search(r"\bSystem\.debug\b", line):
                warn(f"{f}:{i}: System.debug left in code")

    # 3. test methods from the card exist somewhere in the listed files
    haystack = ""
    for f in sorted(allowed):
        p = repo / f
        if p.is_file():
            haystack += p.read_text(encoding="utf-8", errors="replace")
    for m in test_methods(card):
        if m not in haystack:
            fail(f"test method '{m}' from the card's Test spec not found in the listed files")

    for w in warnings:
        print(f"WARN  {w}")
    for f in failures:
        print(f"FAIL  {f}")
    print(f"\n{len(failures)} failure(s), {len(warnings)} warning(s) "
          f"verifying {card_path.name}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
