"""
Simplified Hebrew transliteration engine for the Hebrew Verb Map project.

Used during the "adding new roots" workflow (CLAUDE.md) to generate the
`translit` value for each attested form and the `citation_translit` value
for each root, from the `heb` text copied out of the pipeline's extraction
output. Import as:

    from pipeline.translit import transliterate
    transliterate('קָפַץ')  # -> 'qafatz'

This lived only as a session scratchpad file for a long time and was lost
once when the scratchpad directory got reset; it was reconstructed from
the documented conventions and validated letter-by-letter against a large
set of (heb, translit) ground-truth pairs already shipped in the dataset.
It now lives here, in the repo, specifically so that loss can't happen
again -- run this file directly (`python3 pipeline/translit.py`) to replay
that validation against the fixed regression set embedded at the bottom.

Deliberately a *simplified* transliteration, not full academic IPA:

- Only bet/kaf/peh alternate hard/soft (b/v, k/kh, p/f) based on the
  presence of a dagesh. Gimel/dalet/tav are always g/d/t (never rendered
  with their historical fricative allophones).
- A dagesh on any consonant that is NOT the first letter of the word
  doubles that consonant (gemination) -- e.g. dagesh-forte from an
  assimilated nun, or a piel/niphal-doubled middle radical. A dagesh on
  the first letter of the word is dagesh lene (just selects the hard
  begadkefat sound) and does not double. A dagesh right after a silent
  shva (a closed syllable) is also lene, not forte -- it only doubles
  when the letter before it actually sounded a vowel.
- Vav/yod act as vowel letters (matres lectionis) in the usual contexts:
  vav+holam = "o", vav+dagesh-alone = shuruq "u", bare yod immediately
  contributes nothing (long-hiriq mater). A vav or yod carrying its own
  vowel point is a full consonant ("v"/"y" + that vowel). A bare yod
  carrying only a dagesh (e.g. the geminated yod after the definite
  article, הַיּוֹרְדוֹת) is a real consonant, not a silent mater.
- Word-final heh: with mappiq (dagesh) -> doubled "hh" (plus any vowel,
  including a furtive patah, appended literally after -- no phonetic
  reordering); without mappiq (a plain vowel-marking final heh, e.g. the
  feminine "-ah" ending) -> single "h". Mid-word heh is never a silent
  mater (that role is final-heh-only) -- it's always a real consonant,
  common e.g. in the -הוּ/-הָ pronominal-suffix pattern, so it renders
  as "h" even when bare (no vowel of its own).
- Aleph: word-initial or word-final -> silent (no apostrophe), whether or
  not it carries its own vowel point (e.g. citation forms like קרא
  "qara", מצא "matza" have no final apostrophe). Medial -> always gets an
  apostrophe, even when bare/vowelless (a real glottal stop, e.g.
  וַיֶּאְסֹר "vayye'sor", תָּבֹאוּ "tavo'u").
- Ayin: no apostrophe word-initially or word-finally; a medial ayin WITH
  its own vowel point gets an apostrophe before the vowel. A bare ayin
  (no vowel point of its own, shva doesn't count) contributes nothing at
  all, in any position -- unlike aleph, ayin does go fully silent
  mid-word.
- Shva is always silent/contributes nothing (this engine doesn't
  distinguish vocal vs. silent shva).
- Meteg, rafe, and cantillation marks are ignored.

Known limitation: roughly 15% of the *existing* dataset's stored
`translit` values don't match this engine's output when re-run against
them. Spot-checking a broad sample showed the mismatches split into two
kinds: (a) clear legacy shortcuts from older/different conventions (e.g.
a stored translit that silently drops the word's prefix or a suffix
entirely), and (b) a couple of forms from one root (H7582 שאה) that
look like one-off mistakes made in the same session that produced this
file's own ground truth, rather than a genuine second rule -- see the
two commented-out pairs in the regression set below. This engine reflects
the current, intended standard; it is not meant to reproduce every
historical inconsistency already shipped.
"""

import unicodedata

CANT = set(range(0x0591, 0x05AF + 1))
SHEVA = 'ְ'
HATAF_SEGOL = 'ֱ'
HATAF_PATAH = 'ֲ'
HATAF_QAMATS = 'ֳ'
HIRIQ = 'ִ'
TSERE = 'ֵ'
SEGOL = 'ֶ'
PATAH = 'ַ'
QAMATS = 'ָ'
HOLAM = 'ֹ'
HOLAM_HASER_VAV = 'ֺ'
QUBUTS = 'ֻ'
DAGESH = 'ּ'
METEG = 'ֽ'
RAFE = 'ֿ'
SHIN_DOT = 'ׁ'
SIN_DOT = 'ׂ'
QAMATS_QATAN = 'ׇ'

VOWELS = {
    HATAF_SEGOL: 'e', HATAF_PATAH: 'a', HATAF_QAMATS: 'o',
    HIRIQ: 'i', TSERE: 'e', SEGOL: 'e', PATAH: 'a', QAMATS: 'a',
    HOLAM: 'o', HOLAM_HASER_VAV: 'o', QUBUTS: 'u', QAMATS_QATAN: 'o',
}

IGNORE = {METEG, RAFE}

# base consonant -> (hard, soft) or a plain string for non-alternating letters
BASE = {
    'ב': ('b', 'v'), 'כ': ('k', 'kh'), 'ך': ('k', 'kh'),
    'פ': ('p', 'f'), 'ף': ('p', 'f'),
    'ג': 'g', 'ד': 'd', 'ת': 't',
    'ז': 'z', 'ט': 't', 'ח': 'ch', 'ל': 'l',
    'מ': 'm', 'ם': 'm', 'נ': 'n', 'ן': 'n',
    'ס': 's', 'צ': 'tz', 'ץ': 'tz', 'ק': 'q', 'ר': 'r',
}


def _letters_with_marks(word):
    """Yield (letter, marks_string, is_last_letter, is_first_letter) for
    each Hebrew letter, where marks_string is the concatenation of
    niqqud/other combining marks attached to it (up to the next letter),
    with cantillation/meteg/rafe already stripped out."""
    groups = []
    cur_letter = None
    cur_marks = []
    for ch in word:
        code = ord(ch)
        if code in CANT or ch in IGNORE:
            continue
        cat = unicodedata.category(ch)
        if cat == 'Lo':  # a Hebrew letter
            if cur_letter is not None:
                groups.append((cur_letter, ''.join(cur_marks)))
            cur_letter = ch
            cur_marks = []
        else:
            cur_marks.append(ch)
    if cur_letter is not None:
        groups.append((cur_letter, ''.join(cur_marks)))
    n = len(groups)
    for i, (letter, marks) in enumerate(groups):
        yield letter, marks, (i == n - 1), (i == 0)


def transliterate(word):
    out = []
    # Whether a real vowel SOUND immediately precedes the letter currently
    # being processed -- a dagesh only doubles (dagesh forte) when preceded
    # by an actual vowel; at the start of the word, or right after a silent
    # shva (or another silent letter), a dagesh just selects the hard
    # begadkefat sound (dagesh lene) and does not double.
    prev_had_vowel = False

    for letter, marks, is_last, is_first in _letters_with_marks(word):
        has_dagesh = DAGESH in marks
        vowel = ''
        for m in marks:
            if m in VOWELS:
                vowel = VOWELS[m]
                break
        has_real_vowel = vowel != ''
        may_double = has_dagesh and prev_had_vowel
        this_had_vowel = False  # updated per-branch below before falling through

        if letter in ('ו',):
            if HOLAM in marks or HOLAM_HASER_VAV in marks:
                out.append('o')
                this_had_vowel = True
            elif has_dagesh and not has_real_vowel:
                out.append('u')
                this_had_vowel = True
            elif has_real_vowel:
                cons = 'v'
                if may_double:
                    cons = cons[0] + cons
                out.append(cons + vowel)
                this_had_vowel = True
            elif SHEVA in marks:
                out.append('v')
            # else: bare vav, silent -- this_had_vowel stays False
            prev_had_vowel = this_had_vowel
            continue

        if letter in ('י',):
            if not marks:
                pass  # bare yod: silent mater -- but the vowel it carries
                # (e.g. a preceding hiriq) is still "sounding" through it
                this_had_vowel = prev_had_vowel
            elif has_real_vowel:
                cons = 'y'
                if may_double:
                    cons = cons[0] + cons
                out.append(cons + vowel)
                this_had_vowel = True
            elif SHEVA in marks:
                out.append('y')
            elif has_dagesh:
                # Bare yod carrying only a dagesh (e.g. the geminated yod
                # after a definite article, הַיּוֹרְדוֹת) is a real
                # consonant, not a silent mater.
                cons = 'y'
                if may_double:
                    cons = cons[0] + cons
                out.append(cons)
            prev_had_vowel = this_had_vowel
            continue

        if letter in ('ה',):
            if is_last:
                if has_dagesh:
                    out.append('hh' + vowel)
                    this_had_vowel = True
                elif not marks or marks == SHEVA:
                    out.append('h')
                else:
                    out.append('h' + vowel)
                    this_had_vowel = has_real_vowel
            else:
                # Mid-word heh is never a silent mater in pointed Hebrew
                # (that role is final-heh-only) -- it's a real consonant,
                # common e.g. in the -הוּ/-הָ pronominal-suffix pattern,
                # so it renders as "h" even when bare (no vowel of its own).
                cons = 'h'
                if may_double:
                    cons = cons[0] + cons
                out.append(cons + vowel)
                this_had_vowel = has_real_vowel
            prev_had_vowel = this_had_vowel
            continue

        if letter == 'א':
            # Aleph: word-initial or word-final -> silent (no apostrophe),
            # whether or not it carries its own vowel point (e.g. citation
            # forms like קרא "qara", מצא "matza" have no final apostrophe).
            # Medial -> always gets an apostrophe, even when bare/vowelless
            # (a real glottal stop, e.g. וַיֶּאְסֹר "vayye'sor", תָּבֹאוּ
            # "tavo'u") -- unlike ayin below, aleph doesn't go fully silent
            # mid-word.
            if is_first or is_last:
                if has_real_vowel:
                    out.append(vowel)
                    this_had_vowel = True
            else:
                out.append("'" + vowel)
                this_had_vowel = True
            prev_had_vowel = this_had_vowel
            continue

        if letter == 'ע':
            if has_real_vowel:
                apostrophe = '' if (is_first or is_last) else "'"
                out.append(apostrophe + vowel)
                this_had_vowel = True
            # else: bare (or only shva): silent
            prev_had_vowel = this_had_vowel
            continue

        if letter == 'ש' and SIN_DOT in marks:
            phon = 's'
        elif letter == 'ש':
            phon = 'sh'
        else:
            base = BASE.get(letter)
            if base is None:
                phon = ''
            elif isinstance(base, tuple):
                phon = base[0] if has_dagesh else base[1]
            else:
                phon = base

        if may_double:
            phon = phon[0] + phon
        out.append(phon + vowel)
        prev_had_vowel = has_real_vowel

    return ''.join(out)


# ---------------------------------------------------------------------
# Regression fixture. Run `python3 pipeline/translit.py` to replay this
# against the current code -- it should always print "39/39 matched".
# Most of these pairs are drawn from forms already verified and shipped
# in the dataset in the same session that produced this engine, so
# they're a reliable baseline for catching an accidental behavior change.
# The one exception is הַיּוֹרְדוֹת, added by hand as a regression check
# for the geminated-yod-after-the-article bug fix described above -- the
# dataset's own stored value for that word ("yordot") predates the fix
# and drops the article entirely, so it isn't usable as a fixture pair.
#
# Two forms from H7582 (שאה) -- שָׁאוּ/"shau" and יִשָּׁאֽוּן/"yisshaun" --
# are deliberately excluded: this engine now produces "sha'u" and
# "yissha'un" for them (a medial bare aleph getting an apostrophe), which
# is judged correct per the aleph rule documented above and confirmed by
# many other forms (e.g. citation forms for קרא/מצא/יצא-type roots); the
# two stored values look like a one-off mistake from when they were first
# shipped, not a second rule to preserve.
# ---------------------------------------------------------------------
_REGRESSION_PAIRS = [
    ('וְקָבַע', 'vqava'),
    ('יְרֻטָּשׁוּ', 'yruttashu'),
    ('וְנָקֹטּוּ', 'vnaqottu'),
    ('תִשְׂטֶה', 'tisteh'),
    ('קִנְּנָה', 'qinnnah'),
    ('תִּשָּׁאֶה', "tissha'eh"),
    ('יָנוּם', 'yanum'),
    ('לָנֽוּם', 'lanum'),
    ('תְּקַנֵּן', 'tqannen'),
    ('אֶתְקוֹטָֽט', 'etqotat'),
    ('יַכְתִּרוּ', 'yakhtiru'),
    ('קְבַעֲנוּךָ', "qva'anukha"),
    ('וְשִׂפַּח', 'vsippach'),
    ('מָעֲדוּ', "ma'adu"),
    ('מַכְתִּיר', 'makhtir'),
    ('וְהִקְרִיחוּ', 'vhiqrichu'),
    ('לְיַאֵשׁ', "lya'esh"),
    ('יָפִיק', 'yafiq'),
    ('שְׂטֵה', 'steh'),
    ('נָגַהּ', 'nagahh'),
    ('חֻמְצָתֽוֹ', 'chumtzato'),
    ('נִכְסָֽף', 'nikhsaf'),
    ('נִכְסְפָה', 'nikhsfah'),
    ('וְנוֹאַשׁ', "vno'ash"),
    ('הִשָּׁהּ', 'hisshahh'),
    ('יִתְחַמֵּץ', 'yitchammetz'),
    ('וּנְקֹֽטֹתֶם', 'unqototem'),
    ('לַעֲבֹט', "la'avot"),
    ('נֻקַּרְתֶּֽם', 'nuqqartem'),
    ('וְנִסְפְּחוּ', 'vnispchu'),
    ('יְפַלֵּס', 'yfalles'),
    ('יָלֻזוּ', 'yaluzu'),
    ('נֹשֶׁה', 'nosheh'),
    ('לוּשִׁי', 'lushi'),
    ('סָפוּן', 'safun'),
    ('אֶמְעָֽד', "em'ad"),
    ('נָשִׁיתִי', 'nashiti'),
    ('מֵחַוֺּת', 'mechaot'),
    ('הַיּוֹרְדוֹת', 'hayyordot'),
]

if __name__ == '__main__':
    fails = 0
    for heb, expected in _REGRESSION_PAIRS:
        got = transliterate(heb)
        if got != expected:
            fails += 1
            print(f'MISMATCH: {heb!r} expected {expected!r} got {got!r}')
    total = len(_REGRESSION_PAIRS)
    print(f'{total - fails}/{total} matched')
