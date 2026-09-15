#!/usr/bin/env python3
"""
Build script for the Hebrew Verb Map.

Reads every file in data/roots/*.json (one file per root, keyed by Strong's
number) and assembles the four runtime data structures the app needs:

  - VERB_DATA               keyed by Hebrew root spelling
  - VERB_INDEX              search aliases per root
  - ROOT_ORDER              display order (COMPUTED, not hand-maintained --
                             this is the fix for the bug where new roots
                             went missing from the UI because a second,
                             hand-maintained array silently fell out of sync)
  - ROOT_CITATION_TRANSLIT  transliteration shown under each chip

Outputs:
  dist/hebrew-verb-map.jsx   -- single-file React artifact (for Claude.ai)
  dist/hebrew-verb-map.html  -- single-file offline version (unchanged UI,
                                font, and behavior; only the data differs)
  dist/data.json             -- the four structures alone, for a
                                separate static-site frontend if wanted

Per-root JSON files are the single source of truth. Never hand-edit the
dist/ files -- they are regenerated from data/roots/ every time this runs.
"""
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOTS_DIR = ROOT / "data" / "roots"
DIST_DIR = ROOT / "dist"
TEMPLATE_JSX = ROOT / "src" / "template.jsx"
TEMPLATE_HTML = ROOT / "src" / "template.html"

sys.path.insert(0, str(ROOT / "pipeline"))
import pipeline as P

HEB_ALPHABET = "אבגדהוזחטיכלמנסעפצקרשת"
FINALS = {'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ'}
SUP_MAP = {'¹': 1, '²': 2, '³': 3, '⁴': 4, '⁵': 5}


def hebrew_sort_key(root):
    """Strict Hebrew-alphabet order, final letters normalized to their base
    form, with true homonyms (same consonants) ordered by the *numeric
    value* of their superscript -- not raw codepoint, since ² and ³ have
    lower codepoints than ¹ and a naive string sort gets this backwards."""
    base = ''.join(c for c in root if c not in SUP_MAP)
    sup = next((SUP_MAP[c] for c in root if c in SUP_MAP), 0)
    try:
        letters = [HEB_ALPHABET.index(FINALS.get(c, c)) for c in base]
    except ValueError as e:
        raise ValueError(f"root {root!r} contains a non-Hebrew-letter character") from e
    return (letters, sup)


def load_roots():
    entries = {}
    seen_strong = {}
    for path in sorted(ROOTS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        root = data.get("root")
        strong = data.get("strong")
        if not root:
            sys.exit(f"ERROR: {path.name} has no 'root' field")
        if not strong:
            sys.exit(f"ERROR: {path.name} has no 'strong' field")
        if path.stem != strong:
            sys.exit(f"ERROR: {path.name} filename doesn't match its own "
                      f"strong field ({strong}) -- did a Strong's number get "
                      f"edited without renaming the file?")
        if strong in seen_strong:
            sys.exit(f"ERROR: duplicate Strong's number {strong} in "
                      f"{path.name} and {seen_strong[strong]}")
        seen_strong[strong] = path.name
        if root in entries:
            sys.exit(f"ERROR: duplicate root key {root!r} "
                      f"({seen_strong[strong]} and an earlier file)")
        entries[root] = data
    return entries


def compute_occurrence_counts(entries):
    """Total attested-verb-occurrence count per root, summed across the
    root's own Strong's number plus any strong_alt numbers (a suppletive
    pair like הלך/ילך draws its paradigm from two numbers, so both count
    toward the one root's total). Computed fresh from the morphhb corpus
    each build, the same way ROOT_ORDER is computed rather than hand-
    maintained -- see pipeline.count_all_occurrences for exactly what
    counts as an occurrence.

    Returns {} if the corpus isn't present locally (it's gitignored and
    fetched on demand via pipeline/fetch_corpus.sh) -- the UI shows the
    occurrence count only when this data is available, same as any other
    corpus-derived figure here."""
    if not glob.glob(P.WLC_GLOB):
        return {}
    numbers_by_root = {}
    all_numbers = set()
    for root, data in entries.items():
        nums = [data["strong"][1:]] + [a[1:] for a in data.get("strong_alt", [])]
        numbers_by_root[root] = nums
        all_numbers.update(nums)
    counts_by_number = P.count_all_occurrences(all_numbers)
    return {
        root: sum(counts_by_number.get(n, 0) for n in nums)
        for root, nums in numbers_by_root.items()
    }


def build():
    entries = load_roots()
    print(f"loaded {len(entries)} roots from {ROOTS_DIR}")

    verb_data = {}
    verb_index = []
    root_citation_translit = {}

    for root, data in entries.items():
        clean = {k: v for k, v in data.items()
                 if k not in ("root", "search_match", "citation_translit")}
        # strong_alt and notes (used for suppletive roots) pass straight through
        verb_data[root] = clean
        verb_index.append({"root": root, "match": data.get("search_match", [])})
        if "citation_translit" in data:
            root_citation_translit[root] = data["citation_translit"]
        else:
            sys.exit(f"ERROR: {root} ({data['strong']}) has no citation_translit field")

    root_order = sorted(entries.keys(), key=hebrew_sort_key)

    # sanity: every structure must agree on the exact same root set
    assert set(verb_data) == set(root_order) == set(root_citation_translit)
    assert {e["root"] for e in verb_index} == set(verb_data)

    root_occurrences = compute_occurrence_counts(entries)
    if root_occurrences:
        print(f"computed occurrence counts for {len(root_occurrences)} roots from the corpus")
    else:
        print("corpus not present locally -- occurrence counts omitted (see pipeline/fetch_corpus.sh)")

    DIST_DIR.mkdir(exist_ok=True)

    bundle = {
        "VERB_DATA": verb_data,
        "VERB_INDEX": verb_index,
        "ROOT_ORDER": root_order,
        "ROOT_CITATION_TRANSLIT": root_citation_translit,
        "ROOT_OCCURRENCES": root_occurrences,
    }
    with open(DIST_DIR / "data.json", "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=1)
    print(f"wrote {DIST_DIR / 'data.json'}")

    for template_path, out_name, var_prefix in [
        (TEMPLATE_JSX, "hebrew-verb-map.jsx", "export const "),
        (TEMPLATE_HTML, "hebrew-verb-map.html", "const "),
    ]:
        if not template_path.exists():
            print(f"skipping {out_name}: template {template_path} not found yet")
            continue
        with open(template_path, encoding="utf-8") as f:
            template = f.read()
        data_block = (
            f'{var_prefix}VERB_DATA = ' + json.dumps(verb_data, ensure_ascii=False, indent=1) + ';\n\n\n'
            f'{var_prefix}VERB_INDEX = ' + json.dumps(verb_index, ensure_ascii=False, indent=1) + ';\n\n\n'
            f'{var_prefix}ROOT_ORDER = ' + json.dumps(root_order, ensure_ascii=False, indent=1) + ';\n\n\n'
            f'{var_prefix}ROOT_CITATION_TRANSLIT = ' + json.dumps(root_citation_translit, ensure_ascii=False, indent=1) + ';\n\n\n'
            f'{var_prefix}ROOT_OCCURRENCES = ' + json.dumps(root_occurrences, ensure_ascii=False, indent=1) + ';\n'
        )
        out = template.replace("/*__DATA_BLOCK__*/", data_block)
        with open(DIST_DIR / out_name, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"wrote {DIST_DIR / out_name}")


if __name__ == "__main__":
    build()
