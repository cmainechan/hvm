#!/usr/bin/env python3
"""
Verify only the root files that actually changed, instead of re-checking
the entire dataset on every commit.

Rationale: the full pytest suite's corpus-verification tier is parametrized
over every root in data/roots/ (660+ and growing). At that scale, running
it locally on every commit means re-verifying hundreds of roots that didn't
change, for every batch of 15-40 new ones -- almost all of that output is
pure overhead. CI (.github/workflows/validate.yml) already re-runs the full
sweep on every push, so nothing ever goes unverified before landing on
main; this script just moves the *redundant* local re-checking out of the
hot path.

Usage:
    python3 scripts/verify_changed.py
        Verifies every root file that differs from the last commit (staged,
        unstaged, or untracked) -- i.e. exactly what you're about to commit.

    python3 scripts/verify_changed.py H1980 H3557 ...
        Verifies specific roots by Strong's number, regardless of git state.

Always also run the fast schema/duplicate/homonym tests in full -- they're
cheap regardless of dataset size:
    pytest tests/test_data.py -q -k "not TestAgainstCorpus"
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOTS_DIR = ROOT / "data" / "roots"
sys.path.insert(0, str(ROOT / "pipeline"))
import pipeline as P


def changed_root_files():
    """Every data/roots/*.json that's new, modified, or staged relative to
    the last commit -- i.e. exactly what `git commit` would pick up."""
    out = subprocess.run(
        ["git", "status", "--porcelain", "--", "data/roots"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    files = []
    for line in out.splitlines():
        path = line[3:].strip()
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        if path.endswith(".json"):
            files.append(ROOT / path)
    return files


def main():
    if len(sys.argv) > 1:
        strongs = [s if s.startswith("H") else f"H{s}" for s in sys.argv[1:]]
        paths = [ROOTS_DIR / f"{s}.json" for s in strongs]
        missing = [p for p in paths if not p.exists()]
        if missing:
            sys.exit(f"ERROR: not found: {[p.name for p in missing]}")
    else:
        paths = changed_root_files()
        if not paths:
            print("No changed files under data/roots/ -- nothing to verify.")
            print("(Pass Strong's numbers explicitly to check specific roots anyway.)")
            return

    roots = {}
    for p in paths:
        with open(p, encoding="utf-8") as f:
            roots[p.stem] = json.load(f)

    print(f"Verifying {len(roots)} root(s): {', '.join(sorted(roots))}")

    target_numbers = set()
    for strong, data in roots.items():
        target_numbers.add(strong[1:])
        for alt in data.get("strong_alt", []):
            target_numbers.add(alt[1:])

    records_by_number, unmapped = P.scan_all(target_numbers, verbose=False)
    if unmapped:
        print("WARNING -- unmapped stem letters found:", unmapped)

    any_failed = False
    for strong, data in sorted(roots.items()):
        discs = P.verify_root(strong, data, records_by_number)
        if discs:
            any_failed = True
            print(f"\nFAIL {strong} ({data.get('root')}): {len(discs)} discrepancies")
            for d in discs[:5]:
                print(f"   {d['stem']}/{d['cat']}/{d['code']}: "
                      f"stored {d['stored_heb']!r}@{d['stored_ref']} "
                      f"vs best {d['best']}")
            if len(discs) > 5:
                print(f"   ... and {len(discs) - 5} more")
        else:
            print(f"OK   {strong} ({data.get('root')})")

    if any_failed:
        sys.exit(1)
    print(f"\nAll {len(roots)} root(s) verified clean against a fresh corpus extraction.")


if __name__ == "__main__":
    main()
