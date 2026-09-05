#!/usr/bin/env bash
# Fetches and pins the two source corpora at the exact commits this project
# was built and verified against. Re-running this script always gives byte-
# identical source data, so extraction results stay reproducible even if
# upstream repos are later corrected or changed.
#
# Usage: ./fetch_corpus.sh [target_dir]

set -euo pipefail
TARGET_DIR="${1:-$(dirname "$0")/corpus}"

MORPHHB_COMMIT="3d15126fb1ef74867fc1434be1942e837932691f"
LEXICON_COMMIT="21c9add13bc727d3a951361778e97e3ff7afd1ce"

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

if [ ! -d morphhb ]; then
  git clone https://github.com/openscriptures/morphhb.git
fi
git -C morphhb fetch --depth 1 origin "$MORPHHB_COMMIT" || true
git -C morphhb checkout "$MORPHHB_COMMIT"

if [ ! -d HebrewLexicon ]; then
  git clone https://github.com/openscriptures/HebrewLexicon.git
fi
git -C HebrewLexicon fetch --depth 1 origin "$LEXICON_COMMIT" || true
git -C HebrewLexicon checkout "$LEXICON_COMMIT"

echo "Corpus ready at $TARGET_DIR, pinned to:"
echo "  morphhb:       $MORPHHB_COMMIT"
echo "  HebrewLexicon: $LEXICON_COMMIT"
