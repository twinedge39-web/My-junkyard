from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


TOKEN_RE = re.compile(r"\[([zh]A[0-9A-Fa-f]{3})\]")
SPACE_RE = re.compile(r"\s+")
INLINE_SPACE_RE = re.compile(r"[ \t]+")
LABEL_RE = re.compile(r"<label>(.*?)</label>")
STRIP_SIG_RE = re.compile(r"[�\[\]<>〈〉()（）・:：;；,，.．\-―—\s]+")
HEAD_PREFIX_RE = re.compile(r"^\[zA423\]")
ORTH_ONLY_RE = re.compile(r"^【([^】]+)】(.*)$")

BODY_STARTS = ("〈", "（", "[", "［", "(", "〔", "《", "―", "—", "¶", "◆", "「")
HEADER_LITERAL_REPLACEMENTS = {
    "おうおうと【〈[zA43B][zA43B]〉と】": "おうおうと【〈怏怏〉と】",
    "はん【[zA42E]】": "はん【頒】",
    "はんぷ【[zA42E]布】": "はんぷ【頒布】",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore Kokugo-style entries from an old text dump.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--draft-path", type=Path, help="Draft JSONL. Defaults to <out-root>/entries_master_kokugo_draft.jsonl.")
    parser.add_argument("--map-path", type=Path, help="Token map JSON. Defaults to <out-root>/symbol_map_solved_initial.json.")
    parser.add_argument("--old-text-path", type=Path, help="Old text dump. Defaults to <source-root>/test_dic.txt.")
    return parser.parse_args()


def load_token_map(map_path: Path) -> dict[str, str]:
    payload = json.loads(map_path.read_text(encoding="utf-8"))
    return {token: str(info["value"]) for token, info in payload["tokens"].items()}


def apply_map(text: str, token_map: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        return token_map.get(match.group(1), match.group(0))

    return TOKEN_RE.sub(repl, text)


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


def normalize_key(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u3000", " ").strip()
    text = SPACE_RE.sub(" ", text)
    return text


def strip_head_prefix(text: str) -> str:
    return HEAD_PREFIX_RE.sub("", text, count=1).strip()


def apply_header_fixes(text: str) -> str:
    text = strip_head_prefix(text)
    for src, dst in HEADER_LITERAL_REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text


def head_part(text: str) -> str:
    return normalize_key(text.split("【", 1)[0])


def body_signature(text: str) -> str:
    return STRIP_SIG_RE.sub("", normalize_key(text))[:80]


def body_prefix_signature(text: str) -> str:
    first_line = normalize_key(text).splitlines()[0] if text else ""
    return STRIP_SIG_RE.sub("", first_line)[:40]


def split_orth_line(text: str) -> tuple[str | None, str]:
    match = ORTH_ONLY_RE.match(text)
    if match is None:
        return None, text
    orth = f"【{match.group(1)}】"
    rest = match.group(2).strip()
    return orth, rest


def looks_like_reading_marker(text: str) -> bool:
    return text.startswith("↓") or text.startswith("↑")


def parse_restored_header(text: str) -> tuple[str, str | None]:
    text = normalize_key(text)
    orth, _ = split_orth_line(text)
    if orth is not None and text == orth:
        return orth[1:-1], None
    if "【" in text and "】" in text:
        left, right = text.split("【", 1)
        orthography = right.split("】", 1)[0]
        return left, orthography
    return text, None


def is_head_line(line: str, next_line: str) -> bool:
    if not line or line.startswith("[ID="):
        return False
    stripped = apply_header_fixes(line)
    next_fixed = apply_header_fixes(next_line)
    if looks_like_reading_marker(stripped) and next_fixed.startswith("【"):
        return True
    if stripped.startswith("【"):
        return True
    if stripped.startswith(BODY_STARTS):
        return False
    if re.match(r"^[0-9０-９]+", stripped):
        return False
    if "【" in stripped and not stripped.startswith("【"):
        return True
    return next_line.startswith(BODY_STARTS) or bool(re.match(r"^[0-9０-９]+", next_line))


def parse_test_dic_rows(old_text_path: Path, token_map: dict[str, str]) -> list[dict[str, str]]:
    text = old_text_path.read_text(encoding="cp932", errors="replace")
    lines = text.splitlines()
    rows: list[dict[str, str]] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("[ID="):
            i += 1
            continue

        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines):
            break

        next_line = lines[j].strip()
        if not is_head_line(line, next_line):
            i += 1
            continue

        stripped_line = apply_header_fixes(line)
        headword_line = stripped_line
        inline_body_lines: list[str] = []
        k = j

        next_line_fixed = apply_header_fixes(next_line)
        if looks_like_reading_marker(stripped_line) and next_line_fixed.startswith("【"):
            orth_part, inline_rest = split_orth_line(next_line_fixed)
            if orth_part is not None:
                headword_line = f"{stripped_line}{orth_part}"
                if inline_rest:
                    inline_body_lines.append(inline_rest)
                k = j + 1
        elif stripped_line.startswith("【"):
            orth_part, inline_rest = split_orth_line(stripped_line)
            if orth_part is not None:
                headword_line = orth_part
                if inline_rest:
                    inline_body_lines.append(inline_rest)

        body_lines: list[str] = []
        body_lines.extend(inline_body_lines)
        while k < len(lines):
            current = lines[k].rstrip()
            if current.strip():
                jj = k + 1
                while jj < len(lines) and not lines[jj].strip():
                    jj += 1
                if jj < len(lines):
                    next_candidate = lines[jj].strip()
                    if is_head_line(current.strip(), next_candidate):
                        break
            body_lines.append(current)
            k += 1

        headword_line_mapped = apply_header_fixes(apply_map(headword_line, token_map))
        body_raw = "\n".join(x.strip() for x in body_lines if x.strip())
        body_mapped = apply_map(body_raw, token_map)
        body_readable = cleanup_body(body_mapped)
        unresolved_tokens = sorted(set(TOKEN_RE.findall(body_mapped)))
        rows.append(
            {
                "headword_line": headword_line,
                "headword_line_normalized": normalize_key(headword_line),
                "headword_line_mapped": headword_line_mapped,
                "headword_line_mapped_normalized": normalize_key(headword_line_mapped),
                "headword_line_head_part": head_part(headword_line_mapped),
                "body_raw": body_raw,
                "body_mapped": body_mapped,
                "body_readable": body_readable,
                "body_signature": body_signature(body_readable),
                "body_prefix_signature": body_prefix_signature(body_readable),
                "body_unresolved_count": str(len(TOKEN_RE.findall(body_mapped))),
                "body_unresolved_tokens": ",".join(unresolved_tokens),
            }
        )
        i = k
    return rows


def attach_restored_body(row: dict[str, object], candidate: dict[str, str], match_method: str, old_text_name: str) -> dict[str, object]:
    restored_headword, restored_orthography = parse_restored_header(candidate["headword_line_mapped"])
    row["headword"] = restored_headword
    row["orthography"] = restored_orthography

    header = dict(row.get("header", {}))
    header.setdefault("extracted_normalized", header.get("normalized"))
    header["normalized"] = candidate["headword_line_mapped_normalized"]
    header["restored_test_dic_mapped"] = candidate["headword_line_mapped"]
    header["restored_test_dic_normalized"] = candidate["headword_line_mapped_normalized"]
    row["header"] = header

    body = dict(row.get("body", {}))
    body["restored_test_dic_raw"] = candidate["body_raw"]
    body["restored_test_dic_mapped"] = candidate["body_mapped"]
    body["restored_test_dic_readable"] = candidate["body_readable"]
    body["restored_test_dic_source"] = old_text_name
    body["restored_test_dic_match_method"] = match_method
    row["body"] = body

    canonical = dict(row.get("canonical", {}))
    canonical["headword_display"] = restored_headword
    canonical["headword_normalized"] = candidate["headword_line_mapped_normalized"]
    canonical["orthography"] = restored_orthography
    canonical["body"] = candidate["body_readable"]
    canonical["body_source"] = old_text_name
    canonical["body_quality"] = "restored_old_text"
    canonical["body_match_method"] = match_method
    canonical["body_unresolved_tokens"] = [t for t in candidate["body_unresolved_tokens"].split(",") if t]
    canonical["review_ready"] = not canonical["body_unresolved_tokens"] and bool(canonical["body"])
    row["canonical"] = canonical

    status = dict(row.get("master_status", {}))
    status["body_restored_from_old_text"] = True
    status["ready_for_review"] = bool(canonical["review_ready"])
    row["master_status"] = status

    notes = list(row.get("notes", []))
    notes.append(f"body_restored_from_old_text:{match_method}")
    row["notes"] = notes
    return row


def make_synthetic_candidate(headword_line_mapped: str, body_readable: str) -> dict[str, str]:
    return {
        "headword_line": headword_line_mapped,
        "headword_line_normalized": normalize_key(headword_line_mapped),
        "headword_line_mapped": headword_line_mapped,
        "headword_line_mapped_normalized": normalize_key(headword_line_mapped),
        "headword_line_head_part": head_part(headword_line_mapped),
        "body_raw": body_readable,
        "body_mapped": body_readable,
        "body_readable": body_readable,
        "body_signature": body_signature(body_readable),
        "body_prefix_signature": body_prefix_signature(body_readable),
        "body_unresolved_count": "0",
        "body_unresolved_tokens": "",
    }


def find_candidate(
    row: dict[str, object],
    lookup_exact: dict[str, dict[str, str]],
    lookup_head_part: dict[str, list[dict[str, str]]],
    lookup_body_signature: dict[str, list[dict[str, str]]],
    lookup_body_prefix_signature: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, str] | None, str | None]:
    header_norm = normalize_key(str(row.get("header", {}).get("normalized") or ""))
    candidate = lookup_exact.get(header_norm)
    if candidate is not None:
        return candidate, "header_normalized_exact"

    header_head_part = head_part(header_norm)
    head_candidates = [c for c in lookup_head_part.get(header_head_part, []) if not c["headword_line_mapped"].startswith("【")]
    if header_head_part and len(head_candidates) == 1:
        return head_candidates[0], "head_part_unique"

    body_norm = str(row.get("canonical", {}).get("body") or "")
    signature = body_signature(body_norm)
    body_candidates = lookup_body_signature.get(signature, [])
    if len(body_candidates) == 1 and not body_candidates[0]["headword_line_mapped"].startswith("【"):
        return body_candidates[0], "body_signature_unique"

    prefix_signature = body_prefix_signature(body_norm)
    prefix_candidates = lookup_body_prefix_signature.get(prefix_signature, [])
    if len(prefix_candidates) == 1 and not prefix_candidates[0]["headword_line_mapped"].startswith("【"):
        return prefix_candidates[0], "body_prefix_signature_unique"

    return None, None


def apply_positional_fallback(rows: list[dict[str, object]], old_rows: list[dict[str, str]]) -> None:
    old_headers = [row["headword_line_mapped_normalized"] for row in old_rows]
    positions: dict[str, list[int]] = {}
    for idx, header in enumerate(old_headers):
        positions.setdefault(header, []).append(idx)

    i = 0
    while i < len(rows):
        if rows[i].get("master_status", {}).get("body_restored_from_old_text"):
            i += 1
            continue
        start = i
        while i < len(rows) and not rows[i].get("master_status", {}).get("body_restored_from_old_text"):
            i += 1
        end = i
        length = end - start
        if start == 0 or end >= len(rows):
            continue

        prev_key = normalize_key(str(rows[start - 1].get("header", {}).get("normalized") or ""))
        next_key = normalize_key(str(rows[end].get("header", {}).get("normalized") or ""))
        candidates: list[tuple[int, int]] = []
        for prev_pos in positions.get(prev_key, []):
            next_pos = prev_pos + length + 1
            if next_pos < len(old_headers) and old_headers[next_pos] == next_key:
                candidates.append((prev_pos, next_pos))
        if len(candidates) != 1:
            continue

        prev_pos, _ = candidates[0]
        for offset in range(length):
            row_index = start + offset
            old_index = prev_pos + 1 + offset
            rows[row_index] = attach_restored_body(rows[row_index], old_rows[old_index], "positional_window_unique", "old-text")


def apply_manual_tail_fixes(rows: list[dict[str, object]], old_rows: list[dict[str, str]], old_text_name: str) -> None:
    old_by_header = {row["headword_line_mapped_normalized"]: row for row in old_rows}
    for idx, row in enumerate(rows):
        if row.get("master_status", {}).get("body_restored_from_old_text"):
            continue
        header_norm = normalize_key(str(row.get("header", {}).get("normalized") or ""))
        body_norm = normalize_key(str(row.get("canonical", {}).get("body") or ""))

        if "つかまえる。「とんぼを―」" in body_norm and "皮算用" in body_norm:
            candidate = old_by_header.get(normalize_key("と・る【捕る】"))
            if candidate is not None:
                rows[idx] = attach_restored_body(row, candidate, "body_clue_known", old_text_name)
                continue

        if header_norm == "ひとたまりも―ない わずかの間も、もちこたえられない。":
            candidate = make_synthetic_candidate("ひとたまりも―ない", "わずかの間も、もちこたえられない。")
            rows[idx] = attach_restored_body(row, candidate, "inline_source_line_split", old_text_name)
            continue

        if header_norm == "ひらべった・い":
            candidate = make_synthetic_candidate("ひらべった・い", "")
            rows[idx] = attach_restored_body(row, candidate, "head_only_source_line", old_text_name)
            continue


def main() -> None:
    args = parse_args()
    out_root = args.out_root
    draft_path = args.draft_path or (out_root / "entries_master_kokugo_draft.jsonl")
    map_path = args.map_path or (out_root / "symbol_map_solved_initial.json")
    old_text_path = args.old_text_path or (args.source_root / "test_dic.txt")
    old_text_name = old_text_path.name

    token_map = load_token_map(map_path)
    old_rows = parse_test_dic_rows(old_text_path, token_map)
    lookup_exact = {row["headword_line_mapped_normalized"]: row for row in old_rows}
    lookup_head_part: dict[str, list[dict[str, str]]] = {}
    lookup_body_signature: dict[str, list[dict[str, str]]] = {}
    lookup_body_prefix_signature: dict[str, list[dict[str, str]]] = {}
    for row in old_rows:
        lookup_head_part.setdefault(row["headword_line_head_part"], []).append(row)
        lookup_body_signature.setdefault(row["body_signature"], []).append(row)
        lookup_body_prefix_signature.setdefault(row["body_prefix_signature"], []).append(row)

    (out_root / "kokugo_old_text_index.jsonl").write_text("", encoding="utf-8", newline="\n")
    with (out_root / "kokugo_old_text_index.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for row in old_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    rows: list[dict[str, object]] = []
    with draft_path.open(encoding="utf-8") as src:
        for line in src:
            row = json.loads(line)
            candidate, match_method = find_candidate(
                row,
                lookup_exact,
                lookup_head_part,
                lookup_body_signature,
                lookup_body_prefix_signature,
            )
            if candidate is not None:
                row = attach_restored_body(row, candidate, str(match_method), old_text_name)
            rows.append(row)

    apply_positional_fallback(rows, old_rows)
    apply_manual_tail_fixes(rows, old_rows, old_text_name)

    restored_path = out_root / "entries_master_kokugo_restored.jsonl"
    restored_index_path = out_root / "entries_master_kokugo_restored_index.jsonl"
    report_path = out_root / "entries_master_kokugo_restored_report.json"

    counts: Counter[str] = Counter()
    unresolved_tokens: Counter[str] = Counter()

    with restored_path.open("w", encoding="utf-8", newline="\n") as restored_out, restored_index_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as index_out:
        for row in rows:
            counts["total_entries"] += 1
            if row.get("master_status", {}).get("body_restored_from_old_text"):
                counts["restored_matches"] += 1
                match_method = str(row.get("canonical", {}).get("body_match_method") or "unknown")
                counts[f"match_method:{match_method}"] += 1
                unresolved = list(row.get("canonical", {}).get("body_unresolved_tokens") or [])
                counts["restored_unresolved_tokens"] += len(unresolved)
                for token in unresolved:
                    unresolved_tokens[str(token)] += 1
            else:
                counts["unmatched_entries"] += 1

            restored_out.write(json.dumps(row, ensure_ascii=False) + "\n")
            index_out.write(
                json.dumps(
                    {
                        "id": row["id"],
                        "headword": row.get("headword"),
                        "orthography": row.get("orthography"),
                        "body_quality": row.get("canonical", {}).get("body_quality"),
                        "review_ready": row.get("canonical", {}).get("review_ready"),
                        "body_unresolved_tokens": row.get("canonical", {}).get("body_unresolved_tokens"),
                        "body_snippet": str(row.get("canonical", {}).get("body") or "")[:220],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    report = {
        "old_rows": len(old_rows),
        "merge_counts": dict(counts),
        "coverage": {
            "restored_ratio": round(counts["restored_matches"] / counts["total_entries"], 6)
            if counts["total_entries"]
            else 0.0
        },
        "restored_body": {
            "total_rows": counts["restored_matches"],
            "total_unresolved_tokens": counts["restored_unresolved_tokens"],
            "top_unresolved_tokens": dict(unresolved_tokens.most_common(30)),
        },
        "outputs": {
            "kokugo_old_text_index": str(out_root / "kokugo_old_text_index.jsonl"),
            "entries_master_kokugo_restored": str(restored_path),
            "entries_master_kokugo_restored_index": str(restored_index_path),
        },
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    print(
        "wrote kokugo restored entries: "
        f"restored={counts['restored_matches']} unmatched={counts['unmatched_entries']} "
        f"coverage={report['coverage']['restored_ratio']:.2%}"
    )


if __name__ == "__main__":
    main()
