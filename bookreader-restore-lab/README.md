# bookreader-restore-lab

Experimental recovery helpers for old BookReader-style dictionary data.

This is a public-safe lab snapshot, not a polished product. It contains:

- `scripts/extract_bookreader_trial.py`
  - inspect original `START` files in block units
  - preserve `0x1Fxx` control markers
  - emit JSONL and HTML previews
- `scripts/merge_old_text_pronunciations.py`
  - merge an old text dump back into a draft JSONL
  - restore pronunciation/body for English-style entries
- `scripts/merge_kokugo_old_text.py`
  - merge an old text dump back into a draft JSONL
  - restore body text for a Kokugo-style dictionary
- `maps/`
  - solved token maps that were useful in one real restoration run
- `docs/`
  - reuse notes and a minimal workflow

What is intentionally not included:

- original dictionary binaries
- restored dictionary payloads
- full review outputs
- local absolute paths from the working machine

## Expected inputs

The scripts assume some combination of:

- original `START` files
- a token map JSON
- a draft `entries*.jsonl`
- an older text dump such as `omiyage_02.txt` or `test_dic.txt`

Those file names come from one restoration run. They are examples, not a standard.

## Quick start

Inspect original files:

```bash
python scripts/extract_bookreader_trial.py --source-root /path/to/bookreader --out-root ./out
```

Restore English pronunciation/body from an old text dump:

```bash
python scripts/merge_old_text_pronunciations.py \
  --source-root /path/to/bookreader \
  --out-root ./out
```

Restore Kokugo body text from an old text dump:

```bash
python scripts/merge_kokugo_old_text.py \
  --source-root /path/to/bookreader \
  --out-root ./out
```

## Notes

- The token maps are reusable hints, not universal truth.
- The Kokugo merge script still contains dictionary-specific heuristics.
- For a new dictionary, the realistic path is to copy one merge script and adjust header parsing and fallback rules.
