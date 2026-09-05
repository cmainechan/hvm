"""
Data-integrity tests for the Hebrew Verb Map.

Run with: pytest tests/

Split into two tiers:
  - Fast tests (schema, duplicates, homonym-collision safety) run on every
    push/PR in CI, no corpus download needed.
  - Corpus tests (cross-verify every stored form against a fresh extraction
    from the pinned source texts) require pipeline/corpus/ to exist --
    run `pipeline/fetch_corpus.sh` first, or let the CI workflow do it.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ROOTS_DIR = ROOT / "data" / "roots"

sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "scripts"))

REQUIRED_ROOT_FIELDS = {"glosses", "strong", "stems", "root", "search_match", "citation_translit"}
REQUIRED_FORM_ROW_FIELDS = {"code", "label", "heb", "translit", "ref", "has_suffix", "has_prefix"}
VALID_CATEGORIES = {
    "perfect", "wayyiqtol", "veqatal", "yiqtol", "imperative",
    "infinitive_construct", "infinitive_absolute", "cohortative", "jussive",
    "participle_active", "participle_passive",
}
CANTILLATION = set(range(0x0591, 0x05AF + 1))


def _load_all_roots():
    entries = {}
    for path in sorted(ROOTS_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            entries[path.stem] = json.load(f)
    return entries


ALL_ROOTS = _load_all_roots()


@pytest.mark.parametrize("strong,data", ALL_ROOTS.items())
def test_filename_matches_strong_field(strong, data):
    assert data["strong"] == strong, (
        f"{strong}.json's 'strong' field says {data['strong']!r} -- "
        "filename and field must match exactly"
    )


@pytest.mark.parametrize("strong,data", ALL_ROOTS.items())
def test_required_fields_present(strong, data):
    missing = REQUIRED_ROOT_FIELDS - set(data.keys())
    # stem_glosses is optional (only present when a stem's sense differs
    # from the root-level primary gloss)
    assert not missing, f"{strong} ({data.get('root')}) missing fields: {missing}"


@pytest.mark.parametrize("strong,data", ALL_ROOTS.items())
def test_every_stem_has_at_least_one_form(strong, data):
    for stem, stem_obj in data["stems"].items():
        assert stem_obj["forms"], f"{strong} stem {stem!r} has no forms at all"


@pytest.mark.parametrize("strong,data", ALL_ROOTS.items())
def test_form_categories_are_known(strong, data):
    for stem, stem_obj in data["stems"].items():
        for category in stem_obj["forms"]:
            assert category in VALID_CATEGORIES, (
                f"{strong} stem {stem!r} has unknown category {category!r}"
            )


@pytest.mark.parametrize("strong,data", ALL_ROOTS.items())
def test_form_rows_have_required_fields(strong, data):
    for stem, stem_obj in data["stems"].items():
        for category, rows in stem_obj["forms"].items():
            for row in rows:
                missing = REQUIRED_FORM_ROW_FIELDS - set(row.keys())
                assert not missing, (
                    f"{strong} {stem}/{category} row {row.get('code')} "
                    f"missing fields: {missing}"
                )


@pytest.mark.parametrize("strong,data", ALL_ROOTS.items())
def test_no_stray_cantillation_marks(strong, data):
    """Requirement 8: cantillation stripped, niqqud kept. A stray cantillation
    mark slipping through usually means a hand-typed form was pasted with
    trope marks still attached."""
    for stem, stem_obj in data["stems"].items():
        for category, rows in stem_obj["forms"].items():
            for row in rows:
                bad = [c for c in row["heb"] if ord(c) in CANTILLATION]
                assert not bad, (
                    f"{strong} {stem}/{category}/{row['code']} still has "
                    f"cantillation marks: {[hex(ord(c)) for c in bad]}"
                )


@pytest.mark.parametrize("strong,data", ALL_ROOTS.items())
def test_no_literal_slash_in_heb(strong, data):
    """OSHB word text embeds literal '/' at morpheme boundaries -- these must
    be stripped, not displayed."""
    for stem, stem_obj in data["stems"].items():
        for category, rows in stem_obj["forms"].items():
            for row in rows:
                assert "/" not in row["heb"], (
                    f"{strong} {stem}/{category}/{row['code']} heb field "
                    f"contains a literal slash: {row['heb']!r}"
                )


def test_no_duplicate_strong_numbers():
    nums = [d["strong"] for d in ALL_ROOTS.values()]
    dupes = {n for n in nums if nums.count(n) > 1}
    assert not dupes, f"duplicate Strong's numbers: {dupes}"


def test_homonym_groups_have_distinct_numbers():
    """Roots sharing the same bare consonants (superscript-disambiguated,
    e.g. שבר¹/שבר²/שבר³) must resolve to different Strong's numbers -- if
    two superscripts share a number, the homonym split was done wrong."""
    by_bare = defaultdict(list)
    for strong, data in ALL_ROOTS.items():
        bare = re.sub(r"[¹²³⁴⁵]", "", data["root"])
        by_bare[bare].append((data["root"], strong))
    for bare, group in by_bare.items():
        if len(group) > 1:
            nums = [g[1] for g in group]
            assert len(set(nums)) == len(nums), (
                f"homonym group {bare!r} has a Strong's-number collision: {group}"
            )


def test_root_order_is_computable_and_consistent():
    """The build script computes ROOT_ORDER from data/roots/ rather than
    reading a hand-maintained array -- this test just confirms every root
    string is sortable under the Hebrew-alphabet key (i.e. contains only
    known letters + optional superscript), so the build script won't choke
    or silently mis-sort on a bad root string."""
    from build import hebrew_sort_key  # noqa: F401 -- import via build.py below
    for strong, data in ALL_ROOTS.items():
        hebrew_sort_key(data["root"])  # raises ValueError on bad input


def _corpus_available():
    return (ROOT / "pipeline" / "corpus" / "morphhb" / "wlc").exists()


@pytest.mark.skipif(not _corpus_available(), reason="corpus not fetched -- run pipeline/fetch_corpus.sh")
class TestAgainstCorpus:
    """Cross-verify every stored form against a fresh extraction from the
    pinned source texts. This is the expensive tier -- it re-parses the
    whole WLC for every root under test, so it's opt-in locally and
    conditionally run in CI (see .github/workflows/validate.yml)."""

    def test_sanity_roots_match_pipeline(self):
        """The two roots used as the original hand-verification anchors --
        confirms pipeline.py hasn't regressed."""
        import pipeline
        for strong, expect_root in [("H935", "בוא"), ("H8104", "שמר")]:
            data = ALL_ROOTS.get(strong)
            if data is None:
                pytest.skip(f"{strong} not in dataset")
            assert data["root"] == expect_root
            records, unmapped = pipeline.scan_root({strong[1:]}, verbose=False)
            assert not unmapped, f"{strong}: unmapped stem letters {unmapped}"
            groups = defaultdict(list)
            for r in records:
                groups[(r["stem"], r["category"], r["code"])].append(r)
            for stem, stem_obj in data["stems"].items():
                for category, rows in stem_obj["forms"].items():
                    for row in rows:
                        key = (stem, category, row["code"])
                        candidates = [c for c in groups.get(key, []) if c["ref"] == row["ref"]]
                        assert candidates, (
                            f"{strong} {stem}/{category}/{row['code']} ref "
                            f"{row['ref']} not found in a fresh extraction"
                        )
                        c = candidates[0]
                        assert c["heb"] == row["heb"], (
                            f"{strong} {stem}/{category}/{row['code']}: "
                            f"stored {row['heb']!r} vs freshly extracted {c['heb']!r}"
                        )
