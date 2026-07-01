from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


BLOCK_SIZES = (512, 1024, 2048)
KNOWN_BLOCKS = {
    "root_START": [0x000F, 0x3134],
    "kokugo_START": [0x000F, 0x3134],
    "crcen_START": [0x000F, 0x3134],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect BookReader-style START files.")
    parser.add_argument("--source-root", type=Path, required=True, help="Directory that contains START/KOKUGO/CRCEN.")
    parser.add_argument("--out-root", type=Path, required=True, help="Output directory.")
    return parser.parse_args()


def build_sources(source_root: Path) -> list[tuple[str, Path]]:
    return [
        ("root_START", source_root / "START"),
        ("kokugo_START", source_root / "KOKUGO" / "START"),
        ("crcen_START", source_root / "CRCEN" / "START"),
    ]


def jis_pair_to_text(hi: int, lo: int) -> str:
    try:
        return bytes((hi + 0x80, lo + 0x80)).decode("euc_jp")
    except UnicodeDecodeError:
        return "\uFFFD"


def decode_chunk(data: bytes) -> tuple[str, list[dict[str, str | int]]]:
    tokens: list[dict[str, str | int]] = []
    parts: list[str] = []
    i = 0
    while i < len(data):
        c = data[i]
        if c == 0x1F and i + 1 < len(data):
            code = f"1F{data[i + 1]:02X}"
            tokens.append({"type": "control", "offset": i, "code": code})
            parts.append("\n" if data[i + 1] in (0x0A, 0x0D) else f"⟦{code}⟧")
            i += 2
            continue
        if c == 0x00:
            i += 1
            continue
        if c in (0x0A, 0x0D):
            parts.append("\n")
            i += 1
            continue
        if 0x21 <= c <= 0x7E and i + 1 < len(data) and 0x21 <= data[i + 1] <= 0x7E:
            ch = jis_pair_to_text(c, data[i + 1])
            tokens.append({"type": "jis0208", "offset": i, "hex": f"{c:02X}{data[i + 1]:02X}", "text": ch})
            parts.append(ch)
            i += 2
            continue
        if 0x20 <= c <= 0x7E:
            ch = chr(c)
            tokens.append({"type": "ascii", "offset": i, "hex": f"{c:02X}", "text": ch})
            parts.append(ch)
        else:
            tokens.append({"type": "byte", "offset": i, "hex": f"{c:02X}"})
            parts.append(" ")
        i += 1
    text = "".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(), tokens


def score_text(text: str) -> int:
    if not text:
        return 0
    score = 0
    for ch in text:
        if "\u3040" <= ch <= "\u30FF" or "\u4E00" <= ch <= "\u9FFF":
            score += 3
        elif ("\uFF01" <= ch <= "\uFF5E") or (ch.isascii() and ch.isalpha()):
            score += 1
        elif ch in "〈〉【】（）[]・ー。、．，":
            score += 2
    score -= text.count("\uFFFD") * 10
    return score


def normalized_preview(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("⟦1F0A⟧", "\n")
    text = re.sub(r"⟦1F[0-9A-F]{2}⟧", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def make_samples(sources: list[tuple[str, Path]]) -> list[dict[str, object]]:
    samples: list[dict[str, object]] = []
    for source_id, path in sources:
        raw = path.read_bytes()
        for block_size in BLOCK_SIZES:
            max_block = len(raw) // block_size
            candidate_blocks = set(KNOWN_BLOCKS.get(source_id, []))
            step = max(1, max_block // 400)
            candidate_blocks.update(range(0, max_block, step))
            scored = []
            for block in sorted(b for b in candidate_blocks if 0 <= b < max_block):
                start = block * block_size
                chunk = raw[start : start + block_size]
                decoded, tokens = decode_chunk(chunk)
                normalized = normalized_preview(decoded)
                score = score_text(normalized)
                if score > 80 or block in KNOWN_BLOCKS.get(source_id, []):
                    scored.append((score, block, start, decoded, normalized, tokens, chunk[:128].hex(" ")))
            scored.sort(reverse=True, key=lambda row: row[0])
            selected = scored[:40]
            selected_blocks = {row[1] for row in selected}
            for row in scored:
                if row[1] in KNOWN_BLOCKS.get(source_id, []) and row[1] not in selected_blocks:
                    selected.append(row)
                    selected_blocks.add(row[1])
            for rank, (score, block, start, decoded, normalized, tokens, raw_hex) in enumerate(selected, 1):
                samples.append(
                    {
                        "id": f"{source_id}:{block_size}:{block}",
                        "source": str(path),
                        "source_id": source_id,
                        "block_size": block_size,
                        "block": block,
                        "block_hex": f"{block:04X}",
                        "offset": start,
                        "score": score,
                        "rank": rank,
                        "decoded_with_controls": decoded[:3000],
                        "normalized_preview": normalized[:3000],
                        "control_codes": Counter(str(t["code"]) for t in tokens if t.get("type") == "control"),
                        "raw_hex_first_128": raw_hex,
                    }
                )
    return samples


def make_focused_windows(sources: list[tuple[str, Path]]) -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    for source_id, path in sources:
        raw = path.read_bytes()
        for block_size in BLOCK_SIZES:
            max_block = len(raw) // block_size
            for known in KNOWN_BLOCKS.get(source_id, []):
                if not (0 <= known < max_block):
                    continue
                start_block = max(0, known - 2)
                end_block = min(max_block, known + 6)
                start = start_block * block_size
                end = end_block * block_size
                decoded, tokens = decode_chunk(raw[start:end])
                windows.append(
                    {
                        "id": f"{source_id}:{block_size}:{known}:window",
                        "source": str(path),
                        "source_id": source_id,
                        "block_size": block_size,
                        "known_block": known,
                        "known_block_hex": f"{known:04X}",
                        "window_start_block": start_block,
                        "window_end_block": end_block - 1,
                        "offset": start,
                        "decoded_with_controls": decoded[:12000],
                        "normalized_preview": normalized_preview(decoded)[:12000],
                        "control_codes": Counter(str(t["code"]) for t in tokens if t.get("type") == "control"),
                    }
                )
    return windows


def write_outputs(out_root: Path, samples: list[dict[str, object]], focused_windows: list[dict[str, object]]) -> None:
    out_root.mkdir(parents=True, exist_ok=True)
    with (out_root / "raw_block_samples.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for row in samples:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with (out_root / "focused_known_windows.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for row in focused_windows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    control_totals: Counter[str] = Counter()
    for row in samples:
        control_totals.update(row["control_codes"])

    (out_root / "control_codes.tsv").write_text(
        "code\tcount\n" + "".join(f"{code}\t{count}\n" for code, count in control_totals.most_common()),
        encoding="utf-8",
        newline="\n",
    )

    html_parts = [
        "<!doctype html><meta charset='utf-8'>",
        "<title>BookReader Trial Decode</title>",
        "<style>body{font-family:system-ui,sans-serif;line-height:1.6;margin:24px;max-width:1100px}"
        "article{border-top:1px solid #bbb;padding:16px 0}pre{white-space:pre-wrap;background:#f6f6f6;padding:12px}"
        "code{background:#eee;padding:1px 4px}.meta{color:#555}</style>",
        "<h1>BookReader Trial Decode</h1>",
        "<p>Read-only trial extraction from original START files.</p>",
    ]
    for row in sorted(samples, key=lambda r: (str(r["source_id"]), int(r["block_size"]), int(r["rank"])))[:80]:
        html_parts.append("<article>")
        html_parts.append(
            f"<h2>{html.escape(str(row['id']))}</h2>"
            f"<p class='meta'>score={row['score']} offset={row['offset']} block_hex={row['block_hex']}</p>"
        )
        html_parts.append("<h3>Normalized preview</h3>")
        html_parts.append(f"<pre>{html.escape(str(row['normalized_preview']))}</pre>")
        html_parts.append("<h3>With control markers</h3>")
        html_parts.append(f"<pre>{html.escape(str(row['decoded_with_controls']))}</pre>")
        html_parts.append("</article>")
    (out_root / "preview.html").write_text("\n".join(html_parts), encoding="utf-8", newline="\n")

    focused_html = [
        "<!doctype html><meta charset='utf-8'>",
        "<title>Focused Known Windows</title>",
        "<style>body{font-family:system-ui,sans-serif;line-height:1.6;margin:24px;max-width:1100px}"
        "article{border-top:1px solid #bbb;padding:16px 0}pre{white-space:pre-wrap;background:#f6f6f6;padding:12px}"
        ".meta{color:#555}</style>",
        "<h1>Focused Known Windows</h1>",
        "<p>Continuous windows around selected known blocks.</p>",
    ]
    for row in focused_windows:
        focused_html.append("<article>")
        focused_html.append(
            f"<h2>{html.escape(str(row['id']))}</h2>"
            f"<p class='meta'>offset={row['offset']} blocks={row['window_start_block']}..{row['window_end_block']}</p>"
        )
        focused_html.append("<h3>Normalized preview</h3>")
        focused_html.append(f"<pre>{html.escape(str(row['normalized_preview']))}</pre>")
        focused_html.append("<h3>With control markers</h3>")
        focused_html.append(f"<pre>{html.escape(str(row['decoded_with_controls']))}</pre>")
        focused_html.append("</article>")
    (out_root / "focused_known_windows.html").write_text("\n".join(focused_html), encoding="utf-8", newline="\n")


def main() -> None:
    args = parse_args()
    sources = build_sources(args.source_root)
    samples = make_samples(sources)
    focused_windows = make_focused_windows(sources)
    write_outputs(args.out_root, samples, focused_windows)
    print(f"wrote {len(samples)} samples and {len(focused_windows)} focused windows to {args.out_root}")


if __name__ == "__main__":
    main()
