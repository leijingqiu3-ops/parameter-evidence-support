# -*- coding: utf-8 -*-
"""Locate a verbatim passage in a PDF and render page/crop screenshots.

The search is punctuation- and whitespace-tolerant: it compares an
alphanumeric-only stream while mapping every character back to its PDF word
box. A successful match therefore survives line breaks, PDF hyphenation, and
different spacing. The output is a JSON record plus a full-page PNG and a
cropped PNG with the matched lines highlighted.

Usage:
    python locate_passage.py paper.pdf "verbatim sentence" --out-dir shots
    python locate_passage.py paper.pdf "verbatim sentence" --page 3 --occurrence 0
    python locate_passage.py paper.pdf "verbatim sentence" --dpi 220 --padding 48

Exit codes:
    0  passage found and images written
    2  passage not found
    3  PDF cannot be opened or has no text layer
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Missing dependency: pip install PyMuPDF", file=sys.stderr)
    raise SystemExit(3)

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Missing dependency: pip install Pillow", file=sys.stderr)
    raise SystemExit(3)


def alnum_key(value):
    value = unicodedata.normalize("NFKC", str(value))
    return "".join(char.lower() for char in value if char.isalnum())


def find_occurrences(page, quote_key, limit=50):
    words = page.get_text("words")
    if not words:
        return []

    stream_parts = []
    char_word = []
    for word_index, word in enumerate(words):
        token = alnum_key(word[4])
        for char in token:
            stream_parts.append(char)
            char_word.append(word_index)
    stream = "".join(stream_parts)
    if not stream or not quote_key:
        return []

    occurrences = []
    start = 0
    while len(occurrences) < limit:
        position = stream.find(quote_key, start)
        if position < 0:
            break
        word_indices = sorted(set(char_word[position:position + len(quote_key)]))
        groups = {}
        for word_index in word_indices:
            word = words[word_index]
            rect = fitz.Rect(word[0], word[1], word[2], word[3])
            key = (word[5], word[6])
            if key in groups:
                groups[key].include_rect(rect)
            else:
                groups[key] = fitz.Rect(rect)
        occurrences.append({
            "char_position": position,
            "word_indices": word_indices,
            "rects": [groups[key] for key in sorted(groups)],
            "matched_words": " ".join(words[i][4] for i in word_indices),
        })
        start = position + max(1, len(quote_key))
    return occurrences


def context_for(words, word_indices, radius=18):
    if not word_indices:
        return ""
    first = max(0, min(word_indices) - radius)
    last = min(len(words), max(word_indices) + radius + 1)
    return " ".join(words[i][4] for i in range(first, last))


def union_rect(rects):
    result = fitz.Rect(rects[0])
    for rect in rects[1:]:
        result.include_rect(rect)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", help="path to the source PDF")
    parser.add_argument("quote", help="verbatim passage to locate")
    parser.add_argument("--out-dir", default="screenshots", help="directory for PNG and JSON output")
    parser.add_argument("--page", type=int, default=0, help="search only this 1-based page")
    parser.add_argument("--occurrence", type=int, default=0, help="which occurrence to use (0-based)")
    parser.add_argument("--dpi", type=int, default=180, help="render resolution (default: 180)")
    parser.add_argument("--padding", type=float, default=36.0, help="crop padding in PDF points")
    parser.add_argument("--name", default="", help="output filename stem")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 3

    quote_key = alnum_key(args.quote)
    if len(quote_key) < 4:
        print("Quote is too short after normalization; use at least four letters or digits.", file=sys.stderr)
        return 3

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        print(f"Cannot open PDF: {exc}", file=sys.stderr)
        return 3

    if args.page:
        if args.page < 1 or args.page > doc.page_count:
            print(f"Page {args.page} is outside 1..{doc.page_count}", file=sys.stderr)
            return 3
        page_numbers = [args.page]
    else:
        page_numbers = list(range(1, doc.page_count + 1))

    found = []
    text_pages = 0
    for page_number in page_numbers:
        page = doc[page_number - 1]
        words = page.get_text("words")
        if words:
            text_pages += 1
        for occurrence in find_occurrences(page, quote_key):
            occurrence.update({
                "page_number": page_number,
                "page_index": page_number - 1,
                "context": context_for(words, occurrence["word_indices"]),
            })
            found.append(occurrence)

    if not found:
        if text_pages == 0:
            print("【找不到文本层】The selected pages contain no extractable text; OCR is required.", file=sys.stderr)
            return 3
        print("【找不到原文】The passage was not found. Try a shorter, contiguous sentence from the PDF.", file=sys.stderr)
        return 2
    if args.occurrence >= len(found):
        print(f"Found {len(found)} occurrence(s), but --occurrence={args.occurrence} was requested.", file=sys.stderr)
        return 2

    hit = found[args.occurrence]
    page = doc[hit["page_index"]]
    page_number = hit["page_number"]
    rects = hit["rects"]
    union = union_rect(rects)

    zoom = args.dpi / 72.0
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for rect in rects:
        x0 = int(round(rect.x0 * zoom)) - 2
        y0 = int(round(rect.y0 * zoom)) - 2
        x1 = int(round(rect.x1 * zoom)) + 2
        y1 = int(round(rect.y1 * zoom)) + 2
        draw.rectangle([x0, y0, x1, y1], fill=(255, 221, 51, 75), outline=(190, 120, 0, 220), width=3)
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.name or pdf_path.stem
    page_image = out_dir / f"{stem}_p{page_number}_page.png"
    crop_image = out_dir / f"{stem}_p{page_number}_crop.png"
    json_path = out_dir / f"{stem}_p{page_number}_passage.json"

    image.save(page_image)

    pad = args.padding * zoom
    x0 = max(0, int(round(union.x0 * zoom - pad)))
    y0 = max(0, int(round(union.y0 * zoom - pad)))
    x1 = min(image.width, int(round(union.x1 * zoom + pad)))
    y1 = min(image.height, int(round(union.y1 * zoom + pad)))
    image.crop((x0, y0, x1, y1)).save(crop_image)

    record = {
        "found": True,
        "pdf": str(pdf_path),
        "page_number": page_number,
        "page_index": hit["page_index"],
        "quote": args.quote,
        "matched_words": hit["matched_words"],
        "context": hit["context"],
        "bbox_pdf_points": [round(union.x0, 2), round(union.y0, 2), round(union.x1, 2), round(union.y1, 2)],
        "page_size_points": [round(page.rect.width, 2), round(page.rect.height, 2)],
        "page_image": str(page_image),
        "crop_image": str(crop_image),
        "dpi": args.dpi,
        "occurrences_found": len(found),
        "occurrence_used": args.occurrence,
    }
    json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())