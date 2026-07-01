from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ENTRY_RE = re.compile(
    r"^\s*(?P<headword>[^\n\[]+?)［(?P<pron>[^\n］]+)］\r?\n(?P<body>.*?)(?=^\s*[^\n\[]+?［[^\n］]+］\r?$|\Z)",
    re.MULTILINE | re.DOTALL,
)
TOKEN_RE = re.compile(r"\[([zh]A[0-9A-Fa-f]{3})\]")
HYPHEN_RE = re.compile(r"[‐‑‒–—―−]+")
SPACE_RE = re.compile(r"\s+")
INLINE_SPACE_RE = re.compile(r"[ \t]+")
LABEL_RE = re.compile(r"<label>(.*?)</label>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore pronunciation/body from an old text dump.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--raw-path", type=Path, help="Draft/raw entries JSONL. Defaults to <out-root>/entries_raw.jsonl.")
    parser.add_argument("--map-path", type=Path, help="Token map JSON. Defaults to <out-root>/symbol_map_solved_initial.json.")
    parser.add_argument("--old-text-path", type=Path, help="Old text dump. Defaults to <source-root>/omiyage_02.txt.")
    parser.add_argument("--source-id", default="crcen_START_2048", help="Only enrich rows that match this source_id.")
    return parser.parse_args()


def load_token_map(map_path: Path) -> dict[str, str]:
    payload = json.loads(map_path.read_text(encoding="utf-8"))
    return {token: str(info["value"]) for token, info in payload["tokens"].items()}


def apply_map(text: str, token_map: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        return token_map.get(match.group(1), match.group(0))

    return TOKEN_RE.sub(repl, text)


def cleanup_pron(text: str) -> str:
    rules = [
        (r"ei", "eɪ"),
        (r"ai", "aɪ"),
        (r"au", "aʊ"),
        (r"oi", "ɔɪ"),
        (r"ou", "oʊ"),
        (r"juː", "ju:"),
        (r"ɪː", "i:"),
        (r"ɜː", "ɜ:"),
        (r"ɔː", "ɔ:"),
        (r"uː", "u:"),
        (r"ʃn\b", "ʃən"),
        (r"ʒn\b", "ʒən"),
        (r"əbei", "əbeɪ"),
        (r"əbeit", "əbeɪt"),
        (r"əbeis", "əbeɪs"),
        (r"eibi", "eɪbi"),
        (r"baud", "baʊd"),
        (r"dau", "daʊ"),
        (r"juə", "ju"),
    ]
    for pattern, replacement in rules:
        text = re.sub(pattern, replacement, text)
    return SPACE_RE.sub(" ", text).strip()


def cleanup_body(text: str) -> str:
    text = text.replace("<subentry>", "\n\n")
    text = text.replace("<derived>", "\n〔派生〕")
    text = text.replace("<usage>", "〔語法〕")
    text = text.replace("<sense-group>", "\n\n")
    text = LABEL_RE.sub(lambda m: f"〔{m.group(1)}〕", text)
    text = unicodedata.normalize("NFKC", text)
    lines = [INLINE_SPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_headword(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.strip().lower()
    text = text.replace("�]", "-").replace("�[", "-").replace("�^", "-")
    text = text.replace("･", " ")
    text = HYPHEN_RE.sub("-", text)
    text = SPACE_RE.sub(" ", text)
    return text.strip(" -")


def parse_old_text_rows(old_text_path: Path, token_map: dict[str, str]) -> list[dict[str, str]]:
    text = old_text_path.read_text(encoding="cp932", errors="replace")
    rows: list[dict[str, str]] = []
    for match in ENTRY_RE.finditer(text):
        headword = match.group("headword").strip()
        pron_raw = match.group("pron").strip()
        body = match.group("body").strip()
        if not TOKEN_RE.search(pron_raw):
            continue
        pron_mapped = apply_map(pron_raw, token_map)
        pron_normalized = cleanup_pron(pron_mapped)
        body_mapped = apply_map(body, token_map)
        body_readable = cleanup_body(body_mapped)
        body_unresolved_tokens = sorted(set(TOKEN_RE.findall(body_mapped)))
        rows.append(
            {
                "headword": headword,
                "headword_normalized": normalize_headword(headword),
                "pronunciation_raw": pron_raw,
                "pronunciation_mapped": pron_mapped,
                "pronunciation_normalized": pron_normalized,
                "body_raw": body,
                "body_mapped": body_mapped,
                "body_readable": body_readable,
                "body_snippet": body_readable[:220],
                "body_unresolved_count": str(len(TOKEN_RE.findall(body_mapped))),
                "body_unresolved_tokens": ",".join(body_unresolved_tokens),
            }
        )
    return rows


def choose_unique(rows: list[dict[str, str]]) -> dict[str, str] | None:
    normalized_values = {row["pronunciation_normalized"] for row in rows}
    if len(normalized_values) != 1:
        return None
    raw_values = {row["pronunciation_raw"] for row in rows}
    candidate = dict(rows[0])
    candidate["variant_count"] = str(len(rows))
    candidate["raw_variant_count"] = str(len(raw_values))
    return candidate


def build_lookup(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, int]]:
    exact_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    normalized_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        exact_groups[row["headword"]].append(row)
        normalized_groups[row["headword_normalized"]].append(row)

    exact_lookup: dict[str, dict[str, str]] = {}
    normalized_lookup: dict[str, dict[str, str]] = {}
    ambiguous_exact = 0
    ambiguous_normalized = 0

    for key, group in exact_groups.items():
        candidate = choose_unique(group)
        if candidate is None:
            ambiguous_exact += 1
            continue
        exact_lookup[key] = candidate

    for key, group in normalized_groups.items():
        candidate = choose_unique(group)
        if candidate is None:
            ambiguous_normalized += 1
            continue
        normalized_lookup[key] = candidate

    stats = {
        "old_rows": len(rows),
        "exact_keys": len(exact_groups),
        "normalized_keys": len(normalized_groups),
        "exact_lookup_keys": len(exact_lookup),
        "normalized_lookup_keys": len(normalized_lookup),
        "ambiguous_exact_keys": ambiguous_exact,
        "ambiguous_normalized_keys": ambiguous_normalized,
    }
    return exact_lookup, normalized_lookup, stats


def attach_pronunciation(row: dict[str, object], candidate: dict[str, str], match_method: str, old_text_name: str) -> dict[str, object]:
    pronunciation = dict(row.get("pronunciation", {}))
    pronunciation.update(
        {
            "raw": candidate["pronunciation_raw"],
            "normalized": candidate["pronunciation_normalized"],
            "confidence": "verified",
            "source": old_text_name,
            "match_method": match_method,
        }
    )
    row["pronunciation"] = pronunciation
    status = dict(row.get("status", {}))
    status["pronunciation"] = "verified"
    row["status"] = status
    notes = list(row.get("notes", []))
    notes.append(f"pronunciation_restored_from_old_text:{match_method}")
    row["notes"] = notes
    return row


def attach_restored_body(row: dict[str, object], candidate: dict[str, str], match_method: str, old_text_name: str) -> dict[str, object]:
    body = dict(row.get("body", {}))
    body["restored_old_text_raw"] = candidate["body_raw"]
    body["restored_old_text_mapped"] = candidate["body_mapped"]
    body["restored_old_text_readable"] = candidate["body_readable"]
    body["restored_old_text_source"] = old_text_name
    body["restored_old_text_match_method"] = match_method
    row["body"] = body
    notes = list(row.get("notes", []))
    notes.append(f"body_restored_from_old_text:{match_method}")
    row["notes"] = notes
    return row


def main() -> None:
    args = parse_args()
    out_root = args.out_root
    raw_path = args.raw_path or (out_root / "entries_raw.jsonl")
    map_path = args.map_path or (out_root / "symbol_map_solved_initial.json")
    old_text_path = args.old_text_path or (args.source_root / "omiyage_02.txt")
    old_text_name = old_text_path.name

    token_map = load_token_map(map_path)
    old_rows = parse_old_text_rows(old_text_path, token_map)
    exact_lookup, normalized_lookup, lookup_stats = build_lookup(old_rows)

    index_path = out_root / "old_text_pron_index.jsonl"
    with index_path.open("w", encoding="utf-8", newline="\n") as f:
        for row in old_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    out_path = out_root / "entries_pron_enriched.jsonl"
    sample_path = out_root / "entries_pron_enriched_sample.jsonl"
    verified_index_path = out_root / "entries_pron_verified_index.jsonl"
    counts: Counter[str] = Counter()
    unresolved_body_tokens: Counter[str] = Counter()
    verified_samples: list[dict[str, object]] = []

    with raw_path.open(encoding="utf-8") as src, out_path.open("w", encoding="utf-8", newline="\n") as out, verified_index_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as verified_out:
        for line in src:
            row = json.loads(line)
            counts["total_entries"] += 1
            source_id = row["source"]["source_id"]
            if source_id != args.source_id:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                continue

            counts["filtered_entries"] += 1
            match_method = None
            candidate = exact_lookup.get(row["headword"])
            if candidate is not None:
                match_method = "headword_exact"
            else:
                normalized_key = normalize_headword(row["headword"])
                candidate = normalized_lookup.get(normalized_key)
                if candidate is not None:
                    match_method = "headword_normalized"
                elif row.get("orthography"):
                    orth_key = normalize_headword(str(row["orthography"]))
                    candidate = normalized_lookup.get(orth_key)
                    if candidate is not None:
                        match_method = "orthography_normalized"

            if candidate is not None and match_method is not None:
                row = attach_pronunciation(row, candidate, match_method, old_text_name)
                row = attach_restored_body(row, candidate, match_method, old_text_name)
                counts["verified_matches"] += 1
                counts[match_method] += 1
                counts["restored_body_total"] += 1
                unresolved_count = int(candidate.get("body_unresolved_count", "0"))
                counts["restored_body_unresolved_tokens"] += unresolved_count
                if candidate.get("body_unresolved_tokens"):
                    for token in str(candidate["body_unresolved_tokens"]).split(","):
                        if token:
                            unresolved_body_tokens[token] += 1
                verified_out.write(
                    json.dumps(
                        {
                            "id": row["id"],
                            "source_id": row["source"]["source_id"],
                            "headword": row["headword"],
                            "orthography": row.get("orthography"),
                            "pronunciation_raw": row["pronunciation"]["raw"],
                            "pronunciation_normalized": row["pronunciation"]["normalized"],
                            "match_method": match_method,
                            "block_guess": row["location"]["block_guess"],
                            "byte_offset_guess": row["location"]["byte_offset_guess"],
                            "body_snippet": row["body"]["normalized"][:220],
                            "body_restored_snippet": row["body"]["restored_old_text_readable"][:220],
                            "body_unresolved_count": unresolved_count,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                if len(verified_samples) < 240:
                    verified_samples.append(
                        {
                            "id": row["id"],
                            "headword": row["headword"],
                            "orthography": row.get("orthography"),
                            "pronunciation": row["pronunciation"]["normalized"],
                            "match_method": match_method,
                            "body_restored_snippet": row["body"]["restored_old_text_readable"][:220],
                        }
                    )
            else:
                counts["unmatched_filtered"] += 1

            out.write(json.dumps(row, ensure_ascii=False) + "\n")

    with sample_path.open("w", encoding="utf-8", newline="\n") as f:
        for row in verified_samples:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = {
        "lookup": lookup_stats,
        "merge_counts": dict(counts),
        "coverage": {
            "verified_ratio": round(counts["verified_matches"] / counts["filtered_entries"], 6)
            if counts["filtered_entries"]
            else 0.0
        },
        "restored_body": {
            "total_rows": counts["restored_body_total"],
            "total_unresolved_tokens": counts["restored_body_unresolved_tokens"],
            "top_unresolved_tokens": dict(unresolved_body_tokens.most_common(20)),
        },
        "outputs": {
            "old_text_pron_index": str(index_path),
            "entries_pron_enriched": str(out_path),
            "entries_pron_enriched_sample": str(sample_path),
            "entries_pron_verified_index": str(verified_index_path),
        },
    }
    (out_root / "entries_pron_enriched_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )

    print(
        "wrote pronunciation index and enriched entries: "
        f"verified={counts['verified_matches']} coverage={report['coverage']['verified_ratio']:.2%}"
    )


if __name__ == "__main__":
    main()
