# -*- coding: utf-8 -*-
"""Batch-check DOI/PMID metadata.

Usage:
    python verify_refs.py refs.csv
    python verify_refs.py 10.1111/j.1365-2443.2005.00864.x 15966900

Input CSV: header with `doi` and/or `pmid` columns (extra columns ignored).
Output: <input>.verified.csv, plus a compact table on stdout.
"""
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "parameter-evidence-support/1.0 (mailto:research@example.org)"}


def get_json(url, tries=3):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:
            if attempt == tries - 1:
                return {"_error": str(exc)}
            time.sleep(1.5 * (attempt + 1))


def crossref(doi):
    if not doi:
        return {}
    data = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    if "_error" in data:
        return {"error": data["_error"]}
    m = data.get("message", {})
    authors = []
    for a in m.get("author", []) or []:
        name = " ".join(x for x in [a.get("given"), a.get("family")] if x)
        if name:
            authors.append(name)
    return {
        "title": (m.get("title") or [""])[0],
        "journal": (m.get("container-title") or [""])[0],
        "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0],
        "volume": m.get("volume", ""),
        "issue": m.get("issue", ""),
        "pages": m.get("page", ""),
        "authors": "; ".join(authors),
        "doi": m.get("DOI", doi),
    }


def pubmed(pmid):
    if not pmid:
        return {}
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
           f"?db=pubmed&retmode=json&id={urllib.parse.quote(str(pmid))}")
    data = get_json(url)
    if "_error" in data:
        return {"error": data["_error"]}
    result = data.get("result", {})
    if str(pmid) not in result:
        return {"error": "PMID not found"}
    m = result[str(pmid)]
    doi = ""
    for aid in m.get("articleids", []) or []:
        if aid.get("idtype") == "doi":
            doi = aid.get("value", "")
            break
    authors = [a.get("name", "") for a in m.get("authors", []) or []]
    return {
        "title": m.get("title", ""),
        "journal": m.get("source", ""),
        "year": (m.get("pubdate", "") or "").split(" ")[0],
        "volume": m.get("volume", ""),
        "issue": m.get("issue", ""),
        "pages": m.get("pages", ""),
        "authors": "; ".join(authors),
        "doi": doi,
        "pmid": str(pmid),
    }


def tokens(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower())) - {
        "a", "an", "the", "of", "and", "in", "on", "for", "to", "with", "by"
    }


def compare(cr, pm):
    if not cr or not pm or cr.get("error") or pm.get("error"):
        return "PARTIAL"
    a, b = tokens(cr.get("title")), tokens(pm.get("title"))
    if not a or not b:
        return "PARTIAL"
    overlap = len(a & b) / max(1, min(len(a), len(b)))
    return "OK" if overlap >= 0.55 else "MISMATCH"


def read_rows(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(2048)
        f.seek(0)
        if "," in sample.splitlines()[0]:
            reader = csv.DictReader(f)
            for r in reader:
                doi = (r.get("doi") or r.get("DOI") or "").strip()
                pmid = (r.get("pmid") or r.get("PMID") or "").strip()
                if doi or pmid:
                    rows.append((doi, pmid, r.get("label", "")))
        else:
            for line in f:
                line = line.strip()
                if line:
                    rows.append((line, "", ""))
    return rows


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    args = sys.argv[1:]
    out_rows = []
    if len(args) == 1 and Path(args[0]).exists():
        src = Path(args[0])
        rows = read_rows(src)
        out_path = src.with_suffix(src.suffix + ".verified.csv")
    else:
        rows = [(a, "", "") if not a.isdigit() else ("", a, "") for a in args]
        out_path = Path("verified_refs.csv")

    for doi, pmid, label in rows:
        cr = crossref(doi) if doi else {}
        pm = pubmed(pmid) if pmid else {}
        if not doi and pm.get("doi"):
            cr = crossref(pm["doi"])
        status = compare(cr, pm) if (cr and pm) else ("OK" if (cr or pm) else "NOT_FOUND")
        best = cr if cr and not cr.get("error") else pm
        out_rows.append({
            "label": label,
            "input_doi": doi,
            "input_pmid": pmid,
            "status": status,
            "title": best.get("title", ""),
            "journal": best.get("journal", ""),
            "year": best.get("year", ""),
            "volume": best.get("volume", ""),
            "issue": best.get("issue", ""),
            "pages": best.get("pages", ""),
            "authors": best.get("authors", ""),
            "doi": cr.get("doi", "") or pm.get("doi", ""),
            "pmid": pm.get("pmid", ""),
            "crossref_title": cr.get("title", ""),
            "pubmed_title": pm.get("title", ""),
            "error": cr.get("error", "") or pm.get("error", ""),
        })
        time.sleep(0.4)

    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        writer.writeheader()
        writer.writerows(out_rows)

    for r in out_rows:
        print(f"{r['status']:<10} | {r['doi']:<32} | {r['pmid']:<9} | {r['title'][:70]}")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
