# Hebrew Verb Map — Project Maintenance Guide

---

## 1. What this project is

A "Paradigm Explorer" — a radial-wheel UI for exploring Biblical Hebrew verb
paradigms. Every single form shown is pulled from **actual attested
occurrences** in the Hebrew Bible (Open Scriptures Hebrew Bible morphology +
Westminster Leningrad Codex text) — nothing is generated from memory or
theoretical rules. Gaps are real gaps: if a form doesn't occur in Scripture,
it isn't shown, and this is treated as a feature, not a bug to "fix" by
inventing a form.

Two deliverables are kept in sync at all times:
- `hebrew-verb-map.jsx` — a React artifact (Claude.ai-native)
- `hebrew-verb-map.html` — a single self-contained offline file, zero
  external dependencies, vanilla JS (no React/CDN at runtime), Hebrew font
  bundled as base64

Both embed the same four data blocks and must always be regenerated together
from one source of truth.

---

## 2. Data model

Four JS data structures, all embedded in both output files:

- **`VERB_DATA`** — object keyed by root spelling. Each entry:
  ```
  {
    glosses: ["primary english gloss"],       // shown on chip/legend/wheel by default
    stem_glosses: { "hiphil": "cause X" },    // optional, stem-specific override
    stems: {
      "qal": {
        sense_hint: "simple",
        form_glosses: { "participle_passive": "divorced (woman)" }, // optional, category-specific override
        forms: {
          "perfect": [ { code, label, heb, translit, ref, has_suffix, has_prefix }, ... ]
        }
      }
    }
  }
  ```
- **`VERB_INDEX`** — array of `{ root, match: [aliases...] }` for search. Kept
  **separate** from display glosses on purpose (see §4).
- **`ROOT_ORDER`** — array controlling chip display order (currently
  alphabetical, Hebrew-alphabet order, RTL flow — see the superscript
  sorting note in §4).
- **`ROOT_CITATION_TRANSLIT`** — one transliteration per root, shown under
  the Hebrew on each chip (lexicon citation form, not necessarily an
  attested inflected form).

### Root key conventions
- Bare root spelling is the normal key (e.g. `שמר`).
- **True homographs** (different Strong's numbers, same consonants, genuinely
  unrelated meanings) get superscript-numbered keys: `שבר¹` (break), `שבר²`
  (buy grain), `שבר³` (wait for). Sort using *numeric value* of the
  superscript, not raw Unicode codepoint — `²`/`³` have lower codepoints
  than `¹`, so a naive string sort puts them in the wrong order.
- **Synonym pairs with distinct spellings** (e.g. two different words both
  meaning "flee": ברח and נוס) do NOT need superscripts — just add a
  parenthetical to the *gloss key* during resolution if needed to avoid a
  dictionary collision (e.g. "flee (nas)"), but see §4 re: keeping this out
  of the display.

### Per-stem gloss precision (`stem_glosses`)
Many roots mean something different in different binyanim — sometimes
subtly (go up → bring up), sometimes very differently (die → kill, know →
make known). Default behavior without an override: every stem shows the
root's primary (Qal-based) gloss, which is often wrong for Hiphil/Niphal/etc.
**Never assume a single gloss is stem-agnostic — always sanity-check the
attested form against the gloss before shipping.**

For roots with **no Qal stem at all** (e.g. כון, ישע, שקה, נגד — surprisingly
common), a `DEFAULT_STEM_OVERRIDE` map in the component code controls which
stem the wheel opens to by default, since the ordinary priority order would
otherwise land on a passive stem (Niphal/Hophal) when the label implies an
active sense. Any new no-Qal root needs an entry here.

### No gloss without an attested citation
A sense only belongs in `glosses`, `stem_glosses`, or `form_glosses` if an
actual attested form in the corpus supports it — never because a lexicon
(Strong's or BDB) lists it as the word's primary or historical meaning.
This holds even when the lexicon's listed sense is the headline definition:
if nothing citable in this dataset exemplifies it, it's excluded and the
exclusion is recorded in the root's `notes` field with the reason (e.g.
"BDB's own primary sense, but no citable verse in this dataset"). This is
a stricter check than "does the citation match the gloss" (§4 below and
CLAUDE.md step 10) — a sense can have a perfectly matched citation and
still fail this check if no citation exists for it at all.

This check runs per clause of a compound gloss, not just per stem or per
sense as a whole — a gloss like "spice; ripen; embalm" is three separate
claims, and each one needs its own citation, not just the gloss in
aggregate. A clause survives only when some citation's actual content
demonstrates it, not merely when it's a plausible inference from a
citation that demonstrates a different clause. See CLAUDE.md's "No uncited
glosses" section and its "Compound-gloss trim audit" for the worked
example (H2590 חנט), the two-flag tracking (`gloss_verified` vs.
`gloss_trim_checked`), and the retroactive backlog this created.

### Per-category gloss precision (`form_glosses`)
Occasionally a single stem itself spans more than one sense depending on
which grammatical category is attested — not different enough to warrant
a whole extra stem entry, but different enough that showing one blended
gloss for every form is actively misleading. The clearest case so far:
גרש (H1644) Qal covers "drive out" generally (participle_active,
wayyiqtol) but its participle_passive is `גְּרוּשָׁה`, a fixed legal term
meaning "divorced (woman)" (Lev.21.7, 21.14, 22.13, Num.30.10) — not "a
woman who has been driven out" read literally.

`form_glosses` is an optional object on a stem entry, keyed by grammatical
**category** (`perfect`, `participle_passive`, etc., same keys as `forms`),
each value an override gloss string. `stemGloss()` in both `template.jsx`
and `template.html` checks the currently-displayed form's category against
`form_glosses` first, then falls back to `stem_glosses[stem]`, then
`glosses[0]` — same override-chain pattern as `stem_glosses`, just one
level more specific. Only add an entry for the category(ies) that actually
need a different gloss; every other category in that stem keeps using the
stem-level (or root-level) gloss as before.

---

## 3. Extraction pipeline requirements

If the pipeline needs to be rebuilt (source: re-clone
`openscriptures/morphhb` and `openscriptures/HebrewLexicon` from GitHub),
it must correctly implement all of the following — each was a real,
previously-shipped bug:

1. **Morph codes are often compound.** `HC/Vqp3ms` (conjunction prefix),
   `HR/Vqrmsa` (preposition), `HTd/Vhp3ms` (article), `HVqp3ms/Sp1cs`
   (pronominal suffix). Strip leading `H`, split on `/`, find the segment
   starting with `V` — don't assume it's first. A segment *after* the verb
   segment starting with `S` = suffix. Verb segment not being first =
   prefix.
2. **Lemma field can also be compound** (`c/935`, `l/7125`) — split and
   check each part against target Strong's numbers, stripping trailing
   homonym letters (`1254 a` → `1254`).
3. **Exclude Aramaic** — only process morph codes starting with `H`, not `A`.
4. **Capture rare stems**, not just the standard 7. Confirmed real: `v`
   (Hishtaphel, e.g. שחה "bow down/worship" — 93 occurrences were silently
   dropped before this was caught). Also watch for: Polel, Polal, Hithpolel,
   Poel, Poal, Palel, Pulal, Qal-passive, Pilpel, Polpal, Hithpalpel,
   Nithpael and others. **Scan for unmapped stem letters across every target
   root whenever adding new ones** — don't assume 7-8 known stems is
   exhaustive.
5. **Keep active/passive participles separate** (`r`=active, `s`=passive) —
   they are different words with different meanings, not variants of the
   same form. Merging them silently drops the rarer one whenever the common
   one outnumbers it in raw frequency.
6. **Participles: absolute state only** (state code `a`, not `c`/construct).
   Construct-state participles are grammatically bound to what follows and
   usually carry suffixes, which pollutes the basic paradigm.
7. **Representative-form selection priority** when multiple surface forms
   compete for one slot: prefer none-of-prefix/suffix > has-one >
   has-both. **Exception:** wayyiqtol/veqatal's vav is integral to the form,
   not an optional attachment — don't penalize it there.
8. **Strip cantillation (U+0591–U+05AF), keep niqqud (vowel points).**
9. **Watch for homonym contamination** when resolving a root to a Strong's
   number — always read the actual meaning text of every lexicon candidate
   sharing those consonants before picking one. Confirmed real conflations
   caught previously: שבע (swear vs. be satisfied), עמד (stand vs. shake),
   קרא (call vs. encounter), נשא (lift vs. delude vs. lend), and others.
10. **Sanity-check any rebuilt pipeline** against a root already in the
    dataset (e.g. שמר, בוא) before trusting it on new data — confirm
    identical output.

---

## 4. Workflow for processing a new verb list

Given a list of (root, binyan(s), gloss(es)):

1. **Resolve each root to a Strong's number** via the lexicon, checking
   every candidate sharing the same bare consonants for meaning conflicts
   (see §3.9). Flag anything ambiguous before proceeding rather than
   guessing.
2. **Check for collisions against the existing dataset:**
   - Root spelling already present? → Skip (or confirm intent to replace).
   - Proposed English gloss already used by a *different* existing root? →
     Not a blocker, but flag it. If proceeding, apply a disambiguating
     transliteration suffix (e.g. "gather (laqat)") **only in the search
     index (`VERB_INDEX`)** — never in `VERB_DATA.glosses` or
     `stem_glosses`, since those are what actually renders on the wheel and
     legend. The wheel should only ever show the plain English word.
3. **Extract full paradigm data** via the pipeline (§3) for every attested
   stem — not just the stem(s)/slot the user happened to mention.
4. **Apply the user's confirmed glosses:**
   - A change to the **Qal row** updates the root-level `glosses[0]`
     (primary label), not a `stem_glosses` entry.
   - A change to any other stem becomes a `stem_glosses[stem]` entry.
   - If a root has no Qal stem, add it to `DEFAULT_STEM_OVERRIDE` pointing
     at whichever stem matches the intended primary sense (usually the most
     active/basic one — Hiphil or Piel over their passive counterparts).
5. **Rebuild all four data structures + both output files** from the
   updated source of truth. Regenerate, don't hand-patch.
6. **Test before delivering, every time:**
   - Syntax-check both files.
   - Run the paradigm logic (stem/form building, gloss lookup) across
     *every* root in the dataset, not just the new ones — a bad edit can
     silently break unrelated roots.
   - Actually render a sample in a real or headless browser and confirm
     no blank-page/runtime errors, especially after any structural change.
   - Confirm `VERB_DATA`, `ROOT_ORDER`, `ROOT_CITATION_TRANSLIT`, and
     `VERB_INDEX` are in sync (same root set, no orphaned references) —
     this exact mismatch caused a real "blank page" bug previously.

## 5. What to flag back to the user after each update

- Any homonym risk found and how it was resolved (which Strong's number
  chosen, which excluded, and why).
- Any gloss collision with an existing root, and what disambiguating search
  alias was used.
- Any root with no Qal stem, and what default stem was chosen.
- Any single-attestation or philologically contested form encountered
  (e.g. a form whose only biblical occurrence is entangled in a wordplay
  with a different root, or rests on a debatable lemma assignment) —
  recommend exclusion rather than silently keeping contested data.
- Any rare/unusual stem discovered that isn't among the standard 7.
- Any lexicon-listed sense excluded for lack of an attested citation (see
  §2 "No gloss without an attested citation"), and which root/stem it
  would otherwise have been attached to. Same for any individual clause of
  a compound gloss trimmed for lack of its own citation, even when a
  neighboring clause in the same gloss is well attested.
- Total root count and form count before/after, so drift is visible.
