# -*- coding: utf-8 -*-
"""Find candidate papers for a parameter, without MCP.

Queries Europe PMC (biomedical) and OpenAlex (broad), deduplicates by DOI or
normalized title, and writes a CSV ordered by citation count.

Usage:
    python find_papers.py "GATA2 half-life P815" --limit 15 --year-from 1990 --out candidates.csv
"""
import argparse
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
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:
            if attempt == tries - 1:
                print(f"[warn] {url[:90]} -> {exc}", file=sys.stderr)
                return {}
            time.sleep(1.5 * (attempt + 1))


def europepmc(query, limit, year_from):
    q = query
    if year_from:
        q += f" AND (FIRST_PDATE:[{year_from}-01-01 TO 3000-12-31])"
    params = {
        "query": q,
        "format": "json",
        "pageSize": str(limit),
        "resultType": "core",
        "sort": "CITED desc",
    }
    data = get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(params))
    out = []
    for r in data.get("resultList", {}).get("result", []) or []:
        out.append({
            "source": "EuropePMC",
            "title": r.get("title", ""),
            "authors": r.get("authorString", ""),
            "journal": ((r.get("journalInfo") or {}).get("journal", {}) or {}).get("title", "") or r.get("journalTitle", ""),
            "year": r.get("pubYear", ""),
            "doi": (r.get("doi", "") or "").lower(),
            "pmid": r.get("pmid", ""),
            "cited_by": r.get("citedByCount", 0) or 0,
            "url": f"https://europepmc.org/article/{r.get('source', 'MED')}/{r.get('id', '')}",
        })
    return out


def openalex(query, limit, year_from, mailto):
    params = {"search": query, "per-page": str(limit)}
    if year_from:
        params["filter"] = f"from_publication_date:{year_from}-01-01"
    if mailto:
        params["mailto"] = mailto
    data = get_json("https://api.openalex.org/works?" + urllib.parse.urlencode(params))
    out = []
    for r in data.get("results", []) or []:
        names = []
        for a in (r.get("authorships") or [])[:6]:
            n = (a.get("author") or {}).get("display_name")
            if n:
                names.append(n)
        if len(r.get("authorships") or []) > 6:
            names.append("et al.")
        doi = (r.get("doi") or "").replace("https://doi.org/", "").lower()
        src = ((r.get("primary_location") or {}).get("source") or {}).get("display_name", "")
        out.append({
            "source": "OpenAlex",
            "title": r.get("title", "") or "",
            "authors": "; ".join(names),
            "journal": src,
            "year": r.get("publication_year", ""),
            "doi": doi,
            "pmid": "",
            "cited_by": r.get("cited_by_count", 0) or 0,
            "url": r.get("id", ""),
        })
    return out


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def dedupe(rows):
    seen = {}
    order = []
    for r in rows:
        key = r["doi"] or norm_title(r["title"])
        if not key:
            continue
        if key in seen:
            old = seen[key]
            old["cited_by"] = max(old.get("cited_by", 0), r.get("cited_by", 0))
            old["pmid"] = old.get("pmid") or r.get("pmid", "")
            old["doi"] = old.get("doi") or r.get("doi", "")
            if r["source"] not in old["source"]:
                old["source"] += "+" + r["source"]
        else:
            seen[key] = r
            order.append(key)
    return [seen[k] for k in order]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--year-from", type=int, default=None)
    ap.add_argument("--mailto", default="")
    ap.add_argument("--out", default="candidates.csv")
    ap.add_argument("--no-epmc", action="store_true")
    ap.add_argument("--no-openalex", action="store_true")
    args = ap.parse_args()

    rows = []
    if not args.no_epmc:
        rows += europepmc(args.query, args.limit, args.year_from)
        time.sleep(0.4)
    if not args.no_openalex:
        rows += openalex(args.query, args.limit, args.year_from, args.mailto)

    rows = dedupe(rows)
    rows.sort(key=lambda r: (r.get("cited_by", 0), str(r.get("year", ""))), reverse=True)
    rows = rows[: args.limit * 2]

    out = Path(args.out)
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["source", "title", "authors", "journal", "year", "doi", "pmid", "cited_by", "url"])
        w.writeheader()
        w.writerows(rows)

    for r in rows:
        print(f"{r['cited_by']:>5} | {r['year']} | {r['journal'][:32]:<32} | {r['title'][:78]}")
        print(f"      DOI {r['doi'] or '-'} | PMID {r['pmid'] or '-'} | {r['source']}")
    print(f"\n{len(rows)} candidates -> {out}")
    print("Next: verify metadata with verify_refs.py, then acquire the PDF, then quote page + sentence.")


if __name__ == "__main__":
    main()

