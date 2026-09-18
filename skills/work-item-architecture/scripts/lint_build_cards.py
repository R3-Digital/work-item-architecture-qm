#!/usr/bin/env python3
"""Lint build cards produced by the work-item-architecture QM skill.

Scope: format-checks build cards, 01-requirements.json and
02-components.json ONLY. It does not read the architecture document or the
ADRs; a green exit is not whole-package validation (SA-AUDIT covers card
correctness; the human gate covers the design).

Enforces the zero-open-decisions bar mechanically:
  1. Banned vague phrases in any build card
  2. Required sections present per component type
  3. Every FR in 01-requirements.json satisfied by at least one card
  4. Every card's Test spec names at least one test
  5. 02-components.json and the cards cross-reference cleanly

Usage:  python3 lint_build_cards.py <workspace-dir>
Exit:   0 = pass (warnings allowed), 1 = one or more failures
Stdlib only. Python 3.8+.
"""

import json
import re
import sys
from pathlib import Path

# Single source of truth: references/card-sections.json (shared with the
# build card template). Edit the manifest, not these fallbacks.
_MANIFEST = Path(__file__).resolve().parent.parent / "references" / "card-sections.json"
try:
    _m = json.loads(_MANIFEST.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"FAIL  cannot load {_MANIFEST}: {exc}")
    sys.exit(1)

BANNED = [(p, label) for p, label in _m["banned"]]
UNIVERSAL_SECTIONS = _m["universalSections"]
_by_type = _m["sectionsByType"]
BEHAVIOUR_TYPES = set(_by_type.get("Behaviour", []))
METADATA_TYPES = set(_by_type.get("Metadata spec", []))
GOVERNOR_TYPES = set(_by_type.get("Governor budget", []))
DATA_STEP_TYPES = set(_by_type.get("Data steps", []))
INTERFACE_TYPES = set(_m["warnSections"].get("Interface", []))

failures = []
warnings = []


def fail(msg):
    failures.append(msg)


def warn(msg):
    warnings.append(msg)


def read(path):
    return path.read_text(encoding="utf-8")


def sections_of(text):
    """Return {section_title_lower: body} for '## ' headings."""
    out = {}
    parts = re.split(r"(?m)^##\s+", text)
    for part in parts[1:]:
        lines = part.splitlines()
        title = lines[0].strip().lower()
        out[title] = "\n".join(lines[1:])
    return out


def has_section(secs, name):
    key = name.lower()
    return any(t == key or t.startswith(key) for t in secs)


def section_body(secs, name):
    key = name.lower()
    for t, body in secs.items():
        if t == key or t.startswith(key):
            return body
    return ""


def card_type(text, card):
    m = re.search(r"\*\*Type\*\*\s*:\s*([A-Za-z]+)", text)
    if not m:
        fail(f"{card}: missing '**Type**:' in the metadata block")
        return None
    return m.group(1)


def card_satisfies(text):
    m = re.search(r"\*\*Satisfies\*\*\s*:\s*(.+)", text)
    if not m:
        return []
    return re.findall(r"(?:\d+-)?FR-\d+", m.group(1))


def main(ws):
    cards_dir = ws / "02-build-cards"
    if not cards_dir.is_dir():
        fail(f"no build cards directory at {cards_dir}")
        return

    cards = sorted(cards_dir.glob("*.md"))
    if not cards:
        fail(f"no .md build cards found in {cards_dir}")
        return

    # --- load requirements (check 3) ---
    # DEFERRED / RESOLVED-NOT-IMPLEMENTED FRs are exempt from card coverage
    # but still valid to reference. IDs may be namespaced (604-FR-01) in
    # coordinated sets: see templates.md section 1.
    fr_ids = []
    fr_required = []
    skip_status = {"DEFERRED", "RESOLVED-NOT-IMPLEMENTED", "SATISFIED-EXISTING"}
    req_path = ws / "01-requirements.json"
    if req_path.is_file():
        try:
            req = json.loads(read(req_path))
            for f in req.get("functionalRequirements", []):
                fr_ids.append(f["id"])
                if str(f.get("status", "ACTIVE")).upper() not in skip_status:
                    fr_required.append(f["id"])
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            fail(f"01-requirements.json unreadable: {exc}")
    else:
        warn("01-requirements.json not found: skipping FR traceability check")

    satisfied = set()

    for card in cards:
        name = card.name
        text = read(card)
        secs = sections_of(text)

        # 1. banned phrases
        for pattern, label in BANNED:
            for i, line in enumerate(text.splitlines(), 1):
                if re.search(pattern, line, re.IGNORECASE):
                    fail(f"{name}:{i}: banned phrase '{label}': {line.strip()[:90]}")

        # 2. required sections by type
        ctype = card_type(text, name)
        required = list(UNIVERSAL_SECTIONS)
        if ctype in BEHAVIOUR_TYPES:
            required.append("Behaviour")
        if ctype in METADATA_TYPES:
            required.append("Metadata spec")
        if ctype in GOVERNOR_TYPES:
            required.append("Governor budget")
        if ctype in DATA_STEP_TYPES:
            required.append("Data steps")
        for sec in required:
            if not has_section(secs, sec):
                fail(f"{name}: missing required section '## {sec}' for type {ctype}")
        if ctype in INTERFACE_TYPES and not has_section(secs, "Interface"):
            warn(f"{name}: type {ctype} usually needs an '## Interface' section")

        # 4. test spec names at least one test (cards opening the section
        # with 'Manual verification:' are exempt: browser scripts, data steps)
        tests = section_body(secs, "Test spec")
        if tests and "manual verification" not in tests.lower() \
                and not re.search(r"\btest[A-Za-z0-9_]{2,}", tests):
            fail(f"{name}: Test spec names no test methods")
        if has_section(secs, "Done when") and "- [" not in section_body(secs, "Done when"):
            warn(f"{name}: 'Done when' has no checklist items")

        # gather FRs
        frs = card_satisfies(text)
        if not frs:
            warn(f"{name}: no 'Satisfies: FR-NN' entries in the metadata block")
        for fr in frs:
            satisfied.add(fr)
            if fr_ids and fr not in fr_ids:
                fail(f"{name}: satisfies unknown requirement {fr}")

    # 3. every active FR satisfied
    for fr in fr_required:
        if fr not in satisfied:
            fail(f"traceability: {fr} is satisfied by no build card")

    # 5. components.json cross-check
    comp_path = ws / "02-components.json"
    if comp_path.is_file():
        try:
            comp = json.loads(read(comp_path))
            referenced = set()
            for c in comp.get("components", []):
                bc = c.get("buildCard", "")
                if not bc:
                    fail(f"components.json: '{c.get('name')}' has no buildCard path")
                    continue
                referenced.add(Path(bc).name)
                if not (ws / bc).is_file():
                    fail(f"components.json: buildCard '{bc}' does not exist")
            for card in cards:
                if card.name not in referenced:
                    warn(f"{card.name}: not referenced by any component in components.json")
        except (json.JSONDecodeError, TypeError) as exc:
            fail(f"02-components.json unreadable: {exc}")
    else:
        warn("02-components.json not found: skipping cross-reference check")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    workspace = Path(sys.argv[1])
    if not workspace.is_dir():
        print(f"FAIL: workspace '{workspace}' is not a directory")
        sys.exit(1)

    main(workspace)

    for w in warnings:
        print(f"WARN  {w}")
    for f in failures:
        print(f"FAIL  {f}")
    print(f"\n{len(failures)} failure(s), {len(warnings)} warning(s) "
          f"across workspace {workspace}")
    sys.exit(1 if failures else 0)
