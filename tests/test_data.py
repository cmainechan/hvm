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
OPTIONAL_ROOT_FIELDS = {"stem_glosses", "strong_alt", "notes", "stem_coverage_checked"}
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
def test_no_unknown_fields(strong, data):
    unknown = set(data.keys()) - REQUIRED_ROOT_FIELDS - OPTIONAL_ROOT_FIELDS
    assert not unknown, f"{strong} has unrecognized top-level fields: {unknown}"


@pytest.mark.parametrize("strong,data", ALL_ROOTS.items())
def test_strong_alt_is_well_formed(strong, data):
    if "strong_alt" not in data:
        return
    alts = data["strong_alt"]
    assert isinstance(alts, list) and alts, f"{strong} strong_alt must be a non-empty list"
    for a in alts:
        assert re.match(r"^H\d+$", a), f"{strong} strong_alt entry {a!r} isn't a valid Strong's number"


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
def test_form_glosses_reference_known_categories(strong, data):
    """form_glosses is an optional per-stem override keyed by grammatical
    category (e.g. גרש Qal's participle_passive being the fixed legal term
    "divorced (woman)" rather than the stem's general "drive out"). Every
    key must be a real category, and must actually have forms in that stem
    -- an override for a category with nothing to show is dead data."""
    for stem, stem_obj in data["stems"].items():
        form_glosses = stem_obj.get("form_glosses")
        if not form_glosses:
            continue
        for category in form_glosses:
            assert category in VALID_CATEGORIES, (
                f"{strong} stem {stem!r} form_glosses references unknown category {category!r}"
            )
            assert category in stem_obj["forms"], (
                f"{strong} stem {stem!r} form_glosses has an override for "
                f"{category!r} but that category has no forms in this stem"
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


def _stem_order_from(src_path):
    text = (ROOT / src_path).read_text(encoding="utf-8")
    m = re.search(r"const STEM_ORDER = \[(.*?)\];", text, re.S)
    assert m, f"couldn't find STEM_ORDER in {src_path}"
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def test_every_stem_is_known_to_the_ui():
    """STEM_ORDER/STEM_COLOR in the two UI templates are a fixed, hand-
    maintained list of the stems the wheel and legend know how to render.
    A stem that shows up in data/roots/ but isn't in that list gets stored
    correctly and then silently never appears as a wheel wedge -- a real
    bug caught in review (polal/hithpolel/nithpael/pilpel all slipped
    through this way at once). This test closes the loop: it fails loudly
    at data-add time instead of requiring a manual side-by-side audit."""
    used_stems = {stem for data in ALL_ROOTS.values() for stem in data["stems"]}
    for src_path in ("src/template.jsx", "src/template.html"):
        known = _stem_order_from(src_path)
        missing = used_stems - known
        assert not missing, (
            f"{src_path}'s STEM_ORDER doesn't include: {missing} -- "
            "add each to both STEM_ORDER and STEM_COLOR in template.jsx "
            "AND template.html, or the wheel will silently hide that stem"
        )


def test_translit_engine_matches_its_regression_fixture():
    """pipeline/translit.py is the tool used to generate every `translit`
    and `citation_translit` value when adding new roots. It previously
    lived only as a session scratchpad file and was lost once when that
    directory got reset; it now lives here specifically so that can't
    happen again. This test is the other half of that safety net -- it
    fails loudly in CI (not just when someone remembers to run the file
    by hand) if an edit ever changes its behavior against the known-good
    pairs embedded in its own regression fixture."""
    import translit
    fails = [
        (heb, expected, got)
        for heb, expected in translit._REGRESSION_PAIRS
        if (got := translit.transliterate(heb)) != expected
    ]
    assert not fails, f"translit.py regression mismatches: {fails}"


def _corpus_available():
    return (ROOT / "pipeline" / "corpus" / "morphhb" / "wlc").exists()


@pytest.mark.skipif(not _corpus_available(), reason="corpus not fetched -- run pipeline/fetch_corpus.sh")
class TestAgainstCorpus:
    """Cross-verify every stored form, in every root, against a fresh
    extraction from the pinned source texts. This is the expensive tier --
    it re-parses the whole WLC once (not once per root, via scan_all) --
    but it's what actually keeps the dataset honest, and it's how the
    dataset-wide cleanup was found and verified in the first place."""

    @classmethod
    def setup_class(cls):
        sys.path.insert(0, str(ROOT / "pipeline"))
        import pipeline
        cls.pipeline = pipeline
        target_numbers = set()
        for strong, data in ALL_ROOTS.items():
            target_numbers.add(strong[1:])
            for alt in data.get("strong_alt", []):
                target_numbers.add(alt[1:])
        cls.records_by_number, cls.unmapped = pipeline.scan_all(target_numbers, verbose=False)

    def test_no_unmapped_stem_letters(self):
        assert not self.unmapped, f"unmapped stem letters found: {self.unmapped}"

    @pytest.mark.parametrize("strong,data", ALL_ROOTS.items())
    def test_root_matches_fresh_extraction(self, strong, data):
        discs = self.pipeline.verify_root(strong, data, self.records_by_number)
        assert not discs, (
            f"{strong} ({data.get('root')}) has {len(discs)} discrepancies "
            f"vs a fresh corpus extraction: {discs[:3]}"
            + (" ..." if len(discs) > 3 else "")
        )

    def test_sanity_roots_match_pipeline(self):
        """Kept as an explicit, named regression check on the two original
        hand-verification anchors, on top of the full sweep above."""
        for strong, expect_root in [("H935", "בוא"), ("H8104", "שמר")]:
            data = ALL_ROOTS.get(strong)
            if data is None:
                pytest.skip(f"{strong} not in dataset")
            assert data["root"] == expect_root
            discs = self.pipeline.verify_root(strong, data, self.records_by_number)
            assert not discs, f"{strong} sanity check failed: {discs}"
