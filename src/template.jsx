import React, { useMemo, useState } from "react";

/* ---------------------------------------------------------------
   DATA — auto-generated from the Open Scriptures Hebrew Bible
   (attested morphology) + Strong lexicon. Only forms that
   actually occur in the biblical text are included.
------------------------------------------------------------------ */

/*__DATA_BLOCK__*/

/* ---------------------------------------------------------------
   COMPONENT — dynamic version driven by VERB_DATA / VERB_INDEX
------------------------------------------------------------------ */

const STEM_COLOR = {
  qal: { color: "#8B3A2F", soft: "#F1DCD6", name: "Qal" },
  qal_passive: { color: "#707070", soft: "#E3E3E3", name: "Qal passive" },
  niphal: { color: "#3A5F6B", soft: "#D8E4E6", name: "Niphal" },
  piel: { color: "#8B6F1F", soft: "#EFE6C6", name: "Piel" },
  pilpel: { color: "#C77D2F", soft: "#F5E3D0", name: "Pilpel" },
  polel: { color: "#2F6B8B", soft: "#D6E6EE", name: "Polel" },
  poel: { color: "#5C8B2F", soft: "#E1EBD6", name: "Poel" },
  pealal: { color: "#4A6B2F", soft: "#DEE6D6", name: "Pealal" },
  pulal: { color: "#3E8B47", soft: "#D7EFDA", name: "Pulal" },
  pual: { color: "#5C4A8B", soft: "#E1DAEF", name: "Pual" },
  poal: { color: "#8B5C2F", soft: "#EFE0D0", name: "Poal" },
  polal: { color: "#6B8B2F", soft: "#E6EBD6", name: "Polal" },
  polpal: { color: "#2F8B5C", soft: "#D6EFE1", name: "Polpal" },
  hiphil: { color: "#2F6B3A", soft: "#D9E8DC", name: "Hiphil" },
  hophal: { color: "#6B4A2F", soft: "#E6DAD0", name: "Hophal" },
  hitpael: { color: "#8B2F5C", soft: "#EBD6E1", name: "Hitpael" },
  hithpolel: { color: "#2F8B8B", soft: "#D6EBEB", name: "Hithpolel" },
  hithpalpel: { color: "#4A2F8B", soft: "#DCD6EF", name: "Hithpalpel" },
  hothpaal: { color: "#8B4A2F", soft: "#EFDCD0", name: "Hothpaal" },
  nithpael: { color: "#8B2F8B", soft: "#EBD6EB", name: "Nithpael" },
  hishtaphel: { color: "#3A4A8B", soft: "#DADFF0", name: "Hishtaphel" },
};
const STEM_ORDER = ["qal", "qal_passive", "niphal", "piel", "pilpel", "polel", "poel", "pealal", "pulal", "pual", "poal", "polal", "polpal", "hiphil", "hophal", "hitpael", "hithpolel", "hithpalpel", "hothpaal", "nithpael", "hishtaphel"];

// a handful of roots default to a stem other than the first-available one in
// STEM_ORDER, because that stem is overwhelmingly the dominant/expected form
// for that specific verb (e.g. "bow down" is almost always Hishtaphel, a rare
// stem historically unique to this root, rather than its much sparser Qal).
const DEFAULT_STEM_OVERRIDE = {
  "אזן": "hiphil",
  "בדל": "hiphil",
  "בקש": "piel",
  "דכא": "piel",
  "זהר": "hiphil",
  "זמר": "piel",
  "חתן": "hitpael",
  "יאל¹": "niphal",
  "יאל²": "hiphil",
  "יחל": "piel",
  "יחש": "hitpael",
  "יכח": "hiphil",
  "ילל": "hiphil",
  "ינה": "hiphil",
  "יעל": "hiphil",
  "יצב": "hitpael",
  "ישע": "hiphil",
  "יתר": "niphal",
  "כהן": "piel",
  "כון": "hiphil",
  "כחד": "piel",
  "כנע": "hiphil",
  "מאן": "piel",
  "מור": "hiphil",
  "מטר": "hiphil",
  "מלט": "niphal",
  "נבא": "niphal",
  "נבט": "hiphil",
  "נגד": "hiphil",
  "נחם": "niphal",
  "נכה": "hiphil",
  "נכר": "hiphil",
  "נסה": "piel",
  "נצב": "niphal",
  "נצח": "piel",
  "נצל": "hiphil",
  "נשג": "hiphil",
  "סות": "hiphil",
  "סתר": "niphal",
  "עלם": "hiphil",
  "עלף": "hitpael",
  "ערה": "piel",
  "פלא": "niphal",
  "פלל": "hitpael",
  "צוה": "piel",
  "קוה": "piel",
  "קטר": "hiphil",
  "קשב": "hiphil",
  "רוע": "hiphil",
  "שבע¹": "niphal",
  "שחת": "hiphil",
  "שכם": "hiphil",
  "שלך": "hiphil",
  "שמד": "hiphil",
  "שען": "niphal",
  "שקה": "hiphil",
  "שרת": "piel",
  "שחה": "hishtaphel",
  "נשא²": "hiphil",
  "הום": "niphal",
  "כלם": "niphal",
  "שזר": "hophal",
  "תעב": "piel",
};

const CATEGORY_ORDER = {
  qatal: { singular: ["1cs", "2ms", "2fs", "3ms", "3fs"], plural: ["1cp", "2mp", "2fp", "3cp"] },
  yiqtol: { singular: ["1cs", "2ms", "2fs", "3ms", "3fs"], plural: ["1cp", "2mp", "2fp", "3mp", "3fp"] },
  participle: { singular: ["ms", "fs"], plural: ["mp", "fp"] },
  imperative: { singular: ["2ms", "2fs"], plural: ["2mp", "2fp"] },
};
const FORM_CATEGORY = {
  perfect: "qatal", veqatal: "qatal", wayyiqtol: "yiqtol", yiqtol: "yiqtol",
  participle_active: "participle", participle_passive: "participle", imperative: "imperative",
  cohortative: "yiqtol", jussive: "yiqtol",
  infinitive_construct: "infinitive", infinitive_absolute: "infinitive",
};
const BASE_FORM_META = [
  { key: "perfect", label: "Qatal", sub: "Perfect" },
  { key: "wayyiqtol", label: "Wayyiqtol", sub: "Vav-consec. (narrative)" },
  { key: "yiqtol", label: "Yiqtol", sub: "Imperfect" },
  { key: "veqatal", label: "Veqatal", sub: "Vav-consec. (sequential)" },
  { key: "imperative", label: "Tsivvui", sub: "Imperative" },
  { key: "infinitive_construct", label: "Makor Natuy", sub: "Infinitive Construct" },
  { key: "infinitive_absolute", label: "Makor Muchlat", sub: "Infinitive Absolute" },
  { key: "cohortative", label: "Cohortative", sub: "Volitive · 1st" },
  { key: "jussive", label: "Jussive", sub: "Volitive · 3rd" },
];

// the participle spoke(s) are built dynamically per stem: two separate spokes
// (Qotel/Qatul) only when THIS stem has both an active and a passive
// participle attested; otherwise a single spoke pointing at whichever one
// exists (or a placeholder if neither does, so wheel geometry stays sane
// while browsing between stems/roots).
function buildFormMeta(stemEntry) {
  const hasActive = !!stemEntry.forms.participle_active;
  const hasPassive = !!stemEntry.forms.participle_passive;
  let participleSpokes;
  if (hasActive && hasPassive) {
    participleSpokes = [
      { key: "participle_active", label: "Qotel", sub: "Active Participle" },
      { key: "participle_passive", label: "Qatul", sub: "Passive Participle" },
    ];
  } else if (hasActive) {
    participleSpokes = [{ key: "participle_active", label: "Beinoni", sub: "Participle" }];
  } else if (hasPassive) {
    participleSpokes = [{ key: "participle_passive", label: "Beinoni", sub: "Participle" }];
  } else {
    participleSpokes = [{ key: "participle_active", label: "Beinoni", sub: "Participle" }];
  }
  return [
    BASE_FORM_META[0], BASE_FORM_META[1],
    ...participleSpokes,
    ...BASE_FORM_META.slice(2),
  ];
}

function splitForm(formKey, entries) {
  const cat = FORM_CATEGORY[formKey];
  if (cat === "infinitive") {
    // invariant - one form only, no singular/plural distinction
    return { invariant: entries };
  }
  const order = CATEGORY_ORDER[cat];
  const byCode = Object.fromEntries(entries.map((e) => [e.code, e]));
  return {
    singular: order.singular.map((c) => byCode[c]).filter(Boolean),
    plural: order.plural.map((c) => byCode[c]).filter(Boolean),
  };
}

function firstAvailableStem(rootEntry, root) {
  const override = root && DEFAULT_STEM_OVERRIDE[root];
  if (override && rootEntry.stems[override]) return override;
  return STEM_ORDER.find((s) => rootEntry.stems[s]) || Object.keys(rootEntry.stems)[0];
}
function firstAvailableForm(stemEntry) {
  const formMeta = buildFormMeta(stemEntry);
  return formMeta.find((f) => stemEntry.forms[f.key])?.key || Object.keys(stemEntry.forms)[0];
}
function pickRepresentativeRow(rows) {
  // prefer the 3ms slot (or 'ms' for participle/invariant forms) as the citation
  // form shown at the center of the wheel; fall back to whatever's first only if
  // neither is attested for this stem/form.
  return rows.find((r) => r.code === "3ms") || rows.find((r) => r.code === "ms") || rows[0];
}
function stemGloss(rootEntry, stem, category) {
  // for roots with a different sense per stem (e.g. עלה: Qal 'go up' vs Hiphil
  // 'bring up'), show the sense that actually applies to the currently selected
  // stem, falling back to the root's primary (Qal-based) gloss for any stem
  // that doesn't have its own explicit override.
  // A stem can further vary by grammatical category (e.g. גרש Qal: 'drive out'
  // generally, but the passive participle is the fixed legal term 'divorced
  // (woman)') -- form_glosses[category] takes priority over stem_glosses when
  // the currently displayed form's category has its own override.
  const stemEntry = rootEntry.stems[stem];
  const formOverride = category && stemEntry && stemEntry.form_glosses && stemEntry.form_glosses[category];
  return formOverride || (rootEntry.stem_glosses && rootEntry.stem_glosses[stem]) || rootEntry.glosses[0];
}
function rootCitationTranslit(root) {
  const entry = VERB_DATA[root];
  const stem = firstAvailableStem(entry, root);
  const stemEntry = entry.stems[stem];
  const form = firstAvailableForm(stemEntry);
  return pickRepresentativeRow(stemEntry.forms[form]).translit;
}

export default function HebrewVerbMap() {
  const [query, setQuery] = useState("");
  const [notFound, setNotFound] = useState(false);
  const [activeRoot, setActiveRoot] = useState(null);
  const [activeStem, setActiveStem] = useState(null);
  const [activeForm, setActiveForm] = useState(null);

  function loadRoot(root) {
    const entry = VERB_DATA[root];
    const stem = firstAvailableStem(entry, root);
    setActiveRoot(root);
    setActiveStem(stem);
    setActiveForm(null);
    setNotFound(false);
  }

  function handleSearch() {
    const q = query.trim().toLowerCase();
    if (!q) return;
    // exact match first, so a short alias (e.g. "be") never wins over an exact
    // match elsewhere in the index just because it happens to be a substring
    // of the typed query (e.g. "bear" contains "be"). Only fall back to a
    // whole-word-boundary match if nothing matches exactly -- plain substring
    // containment would let "do" match inside "dover", or "make" match
    // inside a multi-word alias it isn't really part of.
    let hit = VERB_INDEX.find((entry) => entry.match.some((m) => m === q));
    if (!hit) {
      hit = VERB_INDEX.find((entry) =>
        entry.match.some((m) => new RegExp("\\b" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b").test(m))
      );
    }
    if (hit) {
      loadRoot(hit.root);
    } else {
      setNotFound(true);
    }
  }

  const angles = useMemo(() => {
    if (!activeRoot || !activeStem) return [];
    const stemEntry = VERB_DATA[activeRoot].stems[activeStem];
    const n = buildFormMeta(stemEntry).length;
    return Array.from({ length: n }, (_, i) => (360 / n) * i - 90);
  }, [activeRoot, activeStem]);

  // nothing picked yet -- show the header/search/root-picker but no wheel,
  // rather than auto-loading a default root
  if (!activeRoot) {
    return (
      <div style={styles.page}>
        <style>{fontFace}</style>
        <header style={styles.header}>
          <p style={styles.eyebrow}>מַפַּת הַפֹּעַל · Hebrew Verb Map</p>
          <h1 style={styles.title}>Paradigm explorer</h1>
          <p style={styles.subtitle}>
            {Object.keys(VERB_DATA).length} roots · attested Biblical Hebrew forms only (Open Scriptures Hebrew Bible)
          </p>
        </header>

        <div style={styles.searchRow}>
          <input
            value={query}
            onChange={(e) => { setQuery(e.target.value); setNotFound(false); }}
            onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
            placeholder="Try: go · give · shamar · קרא · reign · make king"
            style={styles.input}
            aria-label="Search for a verb in English, transliteration, or Hebrew"
          />
          <button type="button" onClick={handleSearch} style={styles.searchBtn}>Find</button>
        </div>
        {notFound && (
          <p style={styles.notFound}>Not in the database. Try an English gloss, a transliteration, or the Hebrew root.</p>
        )}

        <div style={styles.rootPickerBox}>
          <span style={styles.legendTitle}>Roots ({Object.keys(VERB_DATA).length})</span>
          <div style={styles.rootPickerRow}>
            {ROOT_ORDER.map((root) => (
              <button
                key={root}
                onClick={() => loadRoot(root)}
                style={{ ...styles.rootChip, background: "#FBF6EC", color: "#2B2018" }}
                title={VERB_DATA[root].glosses.join(", ")}
              >
                <span style={styles.rootChipHeb}>{root}</span>
                <span style={{ ...styles.rootChipGloss, color: "#8A7F6A" }}>
                  {ROOT_CITATION_TRANSLIT[root]}
                </span>
              </button>
            ))}
          </div>
        </div>

        <p style={styles.placeholderHint}>Pick a root above, or search, to open its paradigm wheel.</p>

        <footer style={styles.footer}>
          <p>
            {Object.keys(VERB_DATA).length} roots, every form pulled from actual attested occurrences in the Hebrew
            Bible (Open Scriptures Hebrew Bible morphology + Westminster Leningrad Codex text). Gaps are real gaps —
            if a form doesn't occur in Scripture, it isn't shown. Vowel points (niqqud) included; cantillation marks
            removed for readability.
          </p>
        </footer>
      </div>
    );
  }

  const rootEntry = VERB_DATA[activeRoot];
  const stemKeys = STEM_ORDER.filter((s) => rootEntry.stems[s]);
  const stemEntry = rootEntry.stems[activeStem];
  const stemColor = STEM_COLOR[activeStem];
  const formMeta = buildFormMeta(stemEntry);

  const split =
    activeForm && stemEntry.forms[activeForm]
      ? splitForm(activeForm, stemEntry.forms[activeForm])
      : null;

  // representative word for the center card: first available form's first row
  const repFormKey = firstAvailableForm(stemEntry);
  const repRow = pickRepresentativeRow(stemEntry.forms[repFormKey]);

  return (
    <div style={styles.page}>
      <style>{fontFace}</style>

      <header style={styles.header}>
        <p style={styles.eyebrow}>מַפַּת הַפֹּעַל · Hebrew Verb Map</p>
        <h1 style={styles.title}>Paradigm explorer</h1>
        <p style={styles.subtitle}>
          {Object.keys(VERB_DATA).length} roots · attested Biblical Hebrew forms only (Open Scriptures Hebrew Bible)
        </p>
      </header>

      <div style={styles.searchRow}>
        <input
          value={query}
          onChange={(e) => { setQuery(e.target.value); setNotFound(false); }}
          onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
          placeholder="Try: go · give · shamar · קרא · reign · make king"
          style={styles.input}
          aria-label="Search for a verb in English, transliteration, or Hebrew"
        />
        <button type="button" onClick={handleSearch} style={styles.searchBtn}>Find</button>
      </div>
      {notFound && (
        <p style={styles.notFound}>Not in the database. Try an English gloss, a transliteration, or the Hebrew root.</p>
      )}

      {/* root picker chips */}
      <div style={styles.rootPickerBox}>
        <span style={styles.legendTitle}>Roots ({Object.keys(VERB_DATA).length})</span>
        <div style={styles.rootPickerRow}>
          {ROOT_ORDER.map((root) => (
            <button
              key={root}
              onClick={() => loadRoot(root)}
              style={{
                ...styles.rootChip,
                background: root === activeRoot ? "#2B2018" : "#FBF6EC",
                color: root === activeRoot ? "#F4EEDF" : "#2B2018",
              }}
              title={VERB_DATA[root].glosses.join(", ")}
            >
              <span style={styles.rootChipHeb}>{root}</span>
              <span
                style={{
                  ...styles.rootChipGloss,
                  color: root === activeRoot ? "#D9CDB0" : "#8A7F6A",
                }}
              >
                {ROOT_CITATION_TRANSLIT[root]}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Legend — dynamic to current root */}
      <div style={styles.legendBox}>
        <span style={styles.legendTitle}>
          Binyan legend — {rootEntry.glosses[0]} ({activeRoot})
        </span>
        <div style={styles.legendRow}>
          {STEM_ORDER.map((key) => {
            const meta = STEM_COLOR[key];
            const available = !!rootEntry.stems[key];
            return (
              <button
                key={key}
                disabled={!available}
                onClick={() => { if (!available) return; setActiveStem(key); setActiveForm(null); }}
                style={{
                  ...styles.legendChip,
                  borderColor: meta.color,
                  color: available ? meta.color : "#9C9284",
                  background: activeStem === key ? meta.color : "transparent",
                  opacity: available ? 1 : 0.5,
                  cursor: available ? "pointer" : "not-allowed",
                }}
                title={available ? `View ${meta.name}` : `${meta.name} not attested for ${activeRoot}`}
              >
                <span style={{ ...styles.legendDot, background: activeStem === key ? "#FBF6EC" : meta.color }} />
                {meta.name}
                {!available && <span style={styles.legendAsterisk}>†</span>}
              </button>
            );
          })}
        </div>
        <span style={styles.legendFootnote}>† not attested for this root in the Hebrew Bible</span>
      </div>

      <section style={styles.wheelSection}>
        {!activeForm && (
          <div style={styles.wheelWrap}>
            <div style={styles.spokesLayer} aria-hidden="true">
              {angles.map((deg, i) => (
                <div key={i} style={{ ...styles.spoke, transform: `rotate(${deg + 90}deg)`, background: `linear-gradient(90deg, ${stemColor.color}55, transparent)` }} />
              ))}
            </div>

            <div style={{ ...styles.centerCard, borderColor: stemColor.color, boxShadow: `0 0 0 6px ${stemColor.soft}` }}>
              <span style={{ ...styles.centerStemLabel, color: stemColor.color }}>{stemColor.name}</span>
              <span style={styles.centerHeb}>{repRow.heb}</span>
              <span style={styles.centerTranslit}>{repRow.translit}</span>
              <span style={styles.centerEng}>{stemGloss(rootEntry, activeStem, repFormKey)}</span>
              <span style={styles.centerSense}>{stemEntry.sense_hint}</span>
            </div>

            {formMeta.map((f, i) => {
              const deg = angles[i];
              const rad = (deg * Math.PI) / 180;
              const radius = 190;
              const x = Math.cos(rad) * radius;
              const y = Math.sin(rad) * radius;
              const available = !!stemEntry.forms[f.key];
              return (
                <button
                  key={f.key}
                  disabled={!available}
                  onClick={() => available && setActiveForm(f.key)}
                  style={{
                    ...styles.formBtn,
                    left: `calc(50% + ${x}px)`,
                    top: `calc(50% + ${y}px)`,
                    borderColor: available ? stemColor.color : "#C9BB98",
                    background: "#FBF6EC",
                    color: available ? stemColor.color : "#B7AC94",
                    opacity: available ? 1 : 0.55,
                    cursor: available ? "pointer" : "not-allowed",
                  }}
                  title={available ? "" : "Not attested for this stem"}
                >
                  <span style={styles.formBtnLabel}>{f.label}</span>
                  <span style={styles.formBtnSub}>{f.sub}</span>
                </button>
              );
            })}
          </div>
        )}

        {activeForm && split && (
          <div style={styles.expandedWrap}>
            <button style={styles.backBtn} onClick={() => setActiveForm(null)}>← wheel</button>

            <div style={{ ...styles.centerCardFlat, borderColor: stemColor.color, boxShadow: `0 0 0 5px ${stemColor.soft}` }}>
              <span style={{ ...styles.centerStemLabel, color: stemColor.color }}>{stemColor.name}</span>
              <span style={styles.centerHebSmall}>{repRow.heb}</span>
              <span style={styles.centerTranslit}>{repRow.translit}</span>
            </div>

            <div style={styles.tabStrip}>
              {formMeta.map((f) => {
                const available = !!stemEntry.forms[f.key];
                const isActive = f.key === activeForm;
                return (
                  <button
                    key={f.key}
                    disabled={!available}
                    onClick={() => available && setActiveForm(f.key)}
                    style={{
                      ...styles.tabBtn,
                      borderColor: available ? stemColor.color : "#C9BB98",
                      background: isActive ? stemColor.color : "transparent",
                      color: isActive ? "#FBF6EC" : available ? stemColor.color : "#B7AC94",
                      opacity: available ? 1 : 0.5,
                      cursor: available ? "pointer" : "not-allowed",
                    }}
                  >
                    <span style={styles.tabBtnLabel}>{f.label}</span>
                    <span style={styles.tabBtnSub}>{f.sub}</span>
                  </button>
                );
              })}
            </div>

            <div style={styles.columnsWrap}>
              {split.invariant ? (
                <div style={styles.invariantWrap}>
                  {split.invariant.map((row) => (
                    <WordCard key={row.code + row.heb} row={row} color={stemColor.color} gloss={stemGloss(rootEntry, activeStem, activeForm)} />
                  ))}
                </div>
              ) : (
                <>
                  <div style={styles.column}>
                    <span style={{ ...styles.columnTitle, color: stemColor.color }}>Singular</span>
                    <div style={styles.columnCards}>
                      {split.singular.map((row) => <WordCard key={row.code + row.heb} row={row} color={stemColor.color} gloss={stemGloss(rootEntry, activeStem, activeForm)} />)}
                    </div>
                  </div>
                  <div style={styles.column}>
                    <span style={{ ...styles.columnTitle, color: stemColor.color }}>Plural</span>
                    <div style={styles.columnCards}>
                      {split.plural.map((row) => <WordCard key={row.code + row.heb} row={row} color={stemColor.color} gloss={stemGloss(rootEntry, activeStem, activeForm)} />)}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </section>

      <footer style={styles.footer}>
        <p>
          {Object.keys(VERB_DATA).length} roots, every form pulled from actual attested occurrences in the Hebrew
          Bible (Open Scriptures Hebrew Bible morphology + Westminster Leningrad Codex text). Gaps are real gaps —
          if a form doesn't occur in Scripture, it isn't shown. Vowel points (niqqud) included; cantillation marks
          removed for readability.
        </p>
      </footer>
    </div>
  );
}

function WordCard({ row, color, gloss }) {
  return (
    <div style={{ ...styles.wordCard, borderTopColor: color }}>
      <div style={styles.cardTopRow}>
        <span style={styles.cardSlot}>{row.label}</span>
        <span style={styles.badgeGroup}>
          {row.has_prefix && (
            <span style={styles.prefixBadge} title="No form of this exact slot without an attached conjunction/article/preposition occurs anywhere in the Bible.">
              + prefix
            </span>
          )}
          {row.has_suffix && (
            <span style={styles.suffixBadge} title="No bare (unsuffixed) form of this exact slot occurs anywhere in the Bible — this attested form carries an attached pronominal object suffix.">
              + suffix
            </span>
          )}
        </span>
      </div>
      <span style={styles.cardHeb}>{row.heb}</span>
      <span style={styles.cardTranslit}>{row.translit}</span>
      <span style={styles.cardEng}>{gloss} · {row.ref}</span>
    </div>
  );
}

/* ---------------------------------------------------------------
   STYLE — "scribe's wheel": parchment + iron-gall ink + pigment
   accents per binyan, evoking manuscript illumination
------------------------------------------------------------------ */

const fontFace = `
  :root { --heb: 'Taamey Frank CLM','Frank Ruhl Libre','David Libre','SBL Hebrew','Times New Roman',serif; }
`;

const styles = {
  page: {
    minHeight: "100vh",
    background: "#F4EEDF",
    backgroundImage: "radial-gradient(circle at 15% 10%, #EFE6CF 0%, transparent 45%), radial-gradient(circle at 85% 90%, #EFE6CF 0%, transparent 45%)",
    color: "#2B2018",
    fontFamily: "Georgia, 'Iowan Old Style', serif",
    padding: "28px 16px 60px",
    boxSizing: "border-box",
  },
  header: { textAlign: "center", marginBottom: 18 },
  eyebrow: { letterSpacing: "0.14em", textTransform: "uppercase", fontSize: 11, color: "#8B6F1F", margin: 0, fontFamily: "'Courier New', monospace" },
  title: { fontSize: "clamp(26px, 5vw, 38px)", margin: "6px 0 4px", fontWeight: 700, letterSpacing: "-0.01em" },
  subtitle: { margin: 0, color: "#5B5040", fontSize: 13 },

  searchRow: { display: "flex", gap: 8, maxWidth: 560, margin: "20px auto 6px" },
  input: { flex: 1, padding: "12px 14px", borderRadius: 10, border: "1.5px solid #C9BB98", background: "#FBF6EC", fontSize: 15, color: "#2B2018", fontFamily: "inherit", outline: "none" },
  searchBtn: { padding: "12px 20px", borderRadius: 10, border: "1.5px solid #2B2018", background: "#2B2018", color: "#F4EEDF", fontSize: 14, fontWeight: 600, cursor: "pointer", letterSpacing: "0.02em" },
  notFound: { maxWidth: 560, margin: "0 auto 10px", textAlign: "center", fontSize: 13, color: "#8B3A2F" },
  placeholderHint: { textAlign: "center", fontSize: 13, color: "#8A7F6A", marginTop: 28, fontStyle: "italic" },

  rootPickerBox: { maxWidth: 900, margin: "18px auto 0", textAlign: "center" },
  rootPickerRow: { display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 6, marginTop: 8, maxHeight: 220, overflowY: "auto", padding: 4, direction: "rtl" },
  rootChip: {
    fontFamily: "inherit",
    border: "1px solid #C9BB98",
    borderRadius: 8,
    padding: "5px 10px",
    cursor: "pointer",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 1,
    minWidth: 64,
  },
  rootChipHeb: { fontFamily: "var(--heb)", fontSize: 16, lineHeight: 1.1 },
  rootChipGloss: { fontSize: 9.5, lineHeight: 1.1, fontStyle: "italic", maxWidth: 96, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },

  legendBox: { maxWidth: 720, margin: "22px auto 0", textAlign: "center" },
  legendTitle: { fontSize: 11, letterSpacing: "0.08em", textTransform: "uppercase", color: "#8B6F1F", fontFamily: "'Courier New', monospace" },
  legendRow: { display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 8, marginTop: 10 },
  legendChip: { display: "inline-flex", alignItems: "center", gap: 6, padding: "6px 12px", borderRadius: 999, border: "1.5px solid", fontSize: 13, fontWeight: 600, background: "transparent", transition: "background 0.15s ease" },
  legendDot: { width: 8, height: 8, borderRadius: "50%", display: "inline-block" },
  legendAsterisk: { marginLeft: 2, fontSize: 11 },
  legendFootnote: { display: "block", marginTop: 8, fontSize: 11, color: "#8A7F6A" },

  wheelSection: { display: "flex", justifyContent: "center", marginTop: 36 },
  wheelWrap: { position: "relative", width: 460, height: 460, maxWidth: "92vw", maxHeight: "92vw" },
  spokesLayer: { position: "absolute", inset: 0 },
  spoke: { position: "absolute", left: "50%", top: "50%", width: 190, height: 2, transformOrigin: "0 0" },
  centerCard: {
    position: "absolute", left: "50%", top: "50%", transform: "translate(-50%,-50%)",
    width: 168, height: 168, borderRadius: "50%", background: "#FBF6EC", border: "3px solid",
    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
    textAlign: "center", padding: 10, boxSizing: "border-box", gap: 2,
  },
  centerStemLabel: { fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase" },
  centerHeb: { fontFamily: "var(--heb)", fontSize: 26, lineHeight: 1.1, direction: "rtl" },
  centerTranslit: { fontSize: 12, fontStyle: "italic", color: "#5B5040" },
  centerEng: { fontSize: 11, color: "#5B5040" },
  centerSense: { fontSize: 9.5, color: "#8A7F6A", marginTop: 2 },

  formBtn: {
    position: "absolute", transform: "translate(-50%,-50%)", width: 104, height: 68, borderRadius: 12,
    border: "2px solid", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
    boxShadow: "0 2px 6px rgba(43,32,24,0.12)", transition: "background 0.15s ease, color 0.15s ease",
  },
  formBtnLabel: { fontSize: 12.5, fontWeight: 700 },
  formBtnSub: { fontSize: 10, opacity: 0.85, fontStyle: "italic" },

  expandedWrap: { width: "100%", maxWidth: 640, display: "flex", flexDirection: "column", alignItems: "center", gap: 14 },
  backBtn: { alignSelf: "flex-start", border: "1px solid #C9BB98", background: "#FBF6EC", borderRadius: 8, padding: "6px 12px", fontSize: 12.5, color: "#5B5040", cursor: "pointer" },
  centerCardFlat: { borderRadius: 14, border: "2.5px solid", background: "#FBF6EC", padding: "10px 22px", display: "flex", flexDirection: "column", alignItems: "center", gap: 2 },
  centerHebSmall: { fontFamily: "var(--heb)", fontSize: 22, direction: "rtl" },

  tabStrip: { display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 6, width: "100%" },
  tabBtn: { borderRadius: 10, border: "2px solid", padding: "6px 10px", display: "flex", flexDirection: "column", alignItems: "center", minWidth: 82 },
  tabBtnLabel: { fontSize: 11.5, fontWeight: 700 },
  tabBtnSub: { fontSize: 9.5, fontStyle: "italic", opacity: 0.85 },

  columnsWrap: { width: "100%", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 6 },
  invariantWrap: { gridColumn: "1 / -1", display: "flex", justifyContent: "center", padding: "4px 0" },
  column: { display: "flex", flexDirection: "column", gap: 8 },
  columnTitle: { fontSize: 12, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", textAlign: "center" },
  columnCards: { display: "flex", flexDirection: "column", gap: 8 },

  wordCard: { background: "#FFFDF7", border: "1px solid #E4D9BC", borderTop: "4px solid", borderRadius: 10, padding: "8px 12px", display: "flex", flexDirection: "column", gap: 2 },
  cardTopRow: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: 6 },
  badgeGroup: { display: "flex", gap: 4 },
  suffixBadge: { fontSize: 9, fontWeight: 700, letterSpacing: "0.03em", color: "#8B6F1F", background: "#F1E9CE", border: "1px solid #D8C98E", borderRadius: 5, padding: "1px 5px", whiteSpace: "nowrap" },
  prefixBadge: { fontSize: 9, fontWeight: 700, letterSpacing: "0.03em", color: "#3A5F6B", background: "#DCE7E9", border: "1px solid #B9CDD1", borderRadius: 5, padding: "1px 5px", whiteSpace: "nowrap" },
  cardSlot: { fontSize: 10, letterSpacing: "0.06em", textTransform: "uppercase", color: "#8A7F6A" },
  cardHeb: { fontFamily: "var(--heb)", fontSize: 19, direction: "rtl" },
  cardTranslit: { fontSize: 12, fontStyle: "italic", color: "#5B5040" },
  cardEng: { fontSize: 11, color: "#2B2018" },

  footer: { maxWidth: 700, margin: "40px auto 0", textAlign: "center", fontSize: 11.5, color: "#8A7F6A", lineHeight: 1.5 },
};
