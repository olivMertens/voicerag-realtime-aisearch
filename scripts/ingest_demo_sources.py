import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fingerprint_item(category: str, title: str, chunk: str) -> str:
    base = "|".join(
        [
            _normalize_text(category).lower(),
            _normalize_text(title).lower(),
            _normalize_text(chunk).lower(),
        ]
    )
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def _flatten_section(section: Dict[str, Any], parent_title: Optional[str] = None) -> List[Tuple[str, str]]:
    """Return list of (title, chunk) pairs for a website section/subsection."""
    pairs: List[Tuple[str, str]] = []

    title = section.get("title") or ""
    full_title = f"{parent_title} – {title}" if parent_title and title else (title or parent_title or "")

    parts: List[str] = []
    content = section.get("content")
    if isinstance(content, str) and content.strip():
        parts.append(content.strip())

    # Common list fields
    for key in ("bullets", "items", "examples", "recommendations", "topics", "scope"):
        val = section.get(key)
        if isinstance(val, list) and val:
            cleaned = [str(x).strip() for x in val if str(x).strip()]
            if cleaned:
                parts.append("\n".join(f"- {x}" for x in cleaned))

    # Deadlines: list of dicts
    deadlines = section.get("deadlines")
    if isinstance(deadlines, list) and deadlines:
        lines = []
        for d in deadlines:
            if not isinstance(d, dict):
                continue
            t = str(d.get("type", "")).strip()
            days = d.get("deadline_days")
            note = str(d.get("note", "")).strip()
            if t and days is not None:
                line = f"{t}: {days} jours"
                if note:
                    line += f" ({note})"
                lines.append(line)
        if lines:
            parts.append("Délais de déclaration:\n" + "\n".join(f"- {x}" for x in lines))

    # Terms: list of dicts
    terms = section.get("terms")
    if isinstance(terms, list) and terms:
        lines = []
        for term in terms:
            if not isinstance(term, dict):
                continue
            k = str(term.get("term", "")).strip()
            v = str(term.get("definition", "")).strip()
            if k and v:
                lines.append(f"{k}: {v}")
        if lines:
            parts.append("Glossaire:\n" + "\n".join(f"- {x}" for x in lines))

    # Groups: list of {name, items}
    groups = section.get("groups")
    if isinstance(groups, list) and groups:
        lines = []
        for g in groups:
            if not isinstance(g, dict):
                continue
            name = str(g.get("name", "")).strip()
            items = g.get("items")
            if name and isinstance(items, list) and items:
                cleaned = [str(x).strip() for x in items if str(x).strip()]
                if cleaned:
                    lines.append(name + ": " + ", ".join(cleaned))
        if lines:
            parts.append("Garanties (exemples):\n" + "\n".join(f"- {x}" for x in lines))

    # Channels: list
    channels = section.get("channels")
    if isinstance(channels, list) and channels:
        cleaned = [str(x).strip() for x in channels if str(x).strip()]
        if cleaned:
            parts.append("Canaux:\n" + "\n".join(f"- {x}" for x in cleaned))

    # Subsections: recurse
    subsections = section.get("subsections")
    if isinstance(subsections, list) and subsections:
        for sub in subsections:
            if isinstance(sub, dict):
                pairs.extend(_flatten_section(sub, parent_title=full_title))

    chunk = _normalize_text("\n\n".join(parts))
    if full_title and chunk:
        pairs.insert(0, (full_title, chunk))

    return pairs


def _chunk_text(text: str, *, target_chars: int = 1100, overlap: int = 200, max_chunks: int = 80) -> List[str]:
    text = _normalize_text(text)
    if not text:
        return []

    # Split into sentence-ish segments first
    segments = re.split(r"(?<=[\.\!\?])\s+", text)
    segments = [s.strip() for s in segments if s.strip()]

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    def flush():
        nonlocal current, current_len
        if not current:
            return
        chunk = _normalize_text(" ".join(current))
        if chunk:
            chunks.append(chunk)
        current = []
        current_len = 0

    for seg in segments:
        if current_len + len(seg) + 1 <= target_chars:
            current.append(seg)
            current_len += len(seg) + 1
        else:
            flush()
            current.append(seg)
            current_len = len(seg) + 1
        if len(chunks) >= max_chunks:
            break

    flush()

    # Add overlap by repeating tail of previous chunk into next (simple approach)
    if overlap > 0 and len(chunks) > 1:
        overlapped: List[str] = []
        prev_tail = ""
        for i, ch in enumerate(chunks):
            if i == 0:
                overlapped.append(ch)
            else:
                tail = prev_tail[-overlap:]
                combined = _normalize_text(tail + " " + ch) if tail else ch
                overlapped.append(combined)
            prev_tail = ch
        chunks = overlapped

    return chunks


def _extract_pdf_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "pypdf is required to extract PDF text. Install it with: ./.venv/Scripts/python -m pip install pypdf"
        ) from e

    reader = PdfReader(str(pdf_path))
    pages_text: List[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        t = _normalize_text(t)
        if t:
            pages_text.append(t)
    return "\n\n".join(pages_text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge demo sources (PDF + website JSON) into data/faq.json")
    parser.add_argument("--faq", default="data/faq.json", help="Path to faq.json")
    parser.add_argument("--website", required=True, help="Path to website embedding JSON")
    parser.add_argument("--pdf", required=True, help="Path to insurance policy PDF")
    parser.add_argument("--dry-run", action="store_true", help="Do not write, only report")
    args = parser.parse_args()

    faq_path = Path(args.faq)
    website_path = Path(args.website)
    pdf_path = Path(args.pdf)

    faq: List[Dict[str, str]] = json.loads(faq_path.read_text(encoding="utf-8"))

    existing = set(
        _fingerprint_item(it.get("category", ""), it.get("title", ""), it.get("chunk", ""))
        for it in faq
        if isinstance(it, dict)
    )

    added: List[Dict[str, str]] = []

    # Website JSON -> FAQ entries
    website_obj = json.loads(website_path.read_text(encoding="utf-8"))
    source_url = str(website_obj.get("source_url", "")).strip()
    base_categories = website_obj.get("category")
    category = "Habitation"
    if isinstance(base_categories, list):
        if any(str(x).lower() == "habitation" for x in base_categories):
            category = "Habitation"
        elif base_categories:
            category = str(base_categories[0])

    website_title = str(website_obj.get("title", "")).strip()
    website_summary = str(website_obj.get("summary", "")).strip()
    if website_title and website_summary:
        chunk = _normalize_text(website_summary + (f"\n\nSource: {source_url}" if source_url else ""))
        fp = _fingerprint_item(category, f"Site Contoso – {website_title} (résumé)", chunk)
        if fp not in existing:
            item = {"category": category, "title": f"Site Contoso – {website_title} (résumé)", "chunk": chunk}
            added.append(item)
            existing.add(fp)

    sections = website_obj.get("sections")
    if isinstance(sections, list):
        for sec in sections:
            if not isinstance(sec, dict):
                continue
            for t, ch in _flatten_section(sec):
                title = _normalize_text(f"Site Contoso – {t}")
                chunk = _normalize_text(ch + (f"\n\nSource: {source_url}" if source_url else ""))
                fp = _fingerprint_item(category, title, chunk)
                if fp in existing:
                    continue
                added.append({"category": category, "title": title, "chunk": chunk})
                existing.add(fp)

    # PDF -> FAQ entries
    pdf_text = _extract_pdf_text(pdf_path)
    pdf_chunks = _chunk_text(pdf_text, target_chars=1200, overlap=200, max_chunks=60)
    for i, ch in enumerate(pdf_chunks, start=1):
        title = f"Home policy terms – Excerpt {i}"
        chunk = _normalize_text(ch)
        fp = _fingerprint_item("Habitation", title, chunk)
        if fp in existing:
            continue
        added.append({"category": "Habitation", "title": title, "chunk": chunk})
        existing.add(fp)

    if args.dry_run:
        print(f"Existing FAQ items: {len(faq)}")
        print(f"New items to add: {len(added)}")
        return 0

    faq.extend(added)
    faq_path.write_text(json.dumps(faq, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✅ Updated {faq_path} (+{len(added)} items, total {len(faq)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
