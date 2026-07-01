# Reuse Guide

## Conclusion

The recovery logic is reusable as a pattern, but not yet as a fully generic tool.

Use it like this:

1. inspect original `START` files
2. build or extend a token map
3. generate a draft JSONL
4. merge in an older text dump if one exists
5. emit review HTML or Markdown

## Reusable pieces

### `extract_bookreader_trial.py`

Best reuse value.

- samples block windows from original `START` files
- keeps control markers
- helps answer whether the original binary is better than the broken exported text

### Token maps under `maps/`

Useful as seed material.

- `symbol_map_common.json`
- `symbol_map_english_pron.json`
- `symbol_map_solved_initial.json`

They should be treated as candidate mappings. Another dictionary may reuse many tokens, but not all.

### Merge approach

Both merge scripts follow the same broad pattern:

1. read old text
2. normalize headers
3. apply token map
4. match draft rows
5. attach restored body or pronunciation
6. record match method for later audit

## Dictionary-specific parts

### English merge script

Good fit when entries look like:

```text
headword [pronunciation]
body...
```

Main specific assumptions:

- old text file name default is `omiyage_02.txt`
- pronunciation normalization rules are English-oriented

### Kokugo merge script

Still heavily specialized.

Main specific assumptions:

- old text file name default is `test_dic.txt`
- header parsing depends on `【...】` style lines
- some fallback rules are tailored to one dictionary layout
- a small set of manual tail fixes remains

## Best next refactor

If this lab is reused again, the next sensible step is:

1. move path and IO handling into a shared module
2. move token-map loading into a shared module
3. keep per-dictionary header rules in thin merge scripts
4. move manual fixes into external JSON or YAML
